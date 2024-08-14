from flask import Flask, request, jsonify
from flask_cors import CORS
from azure.cosmos import CosmosClient, exceptions, PartitionKey
from upload import start_upload_process
from global_vars import get_all_rfps, clear_completed_uploads
import os
from dotenv import load_dotenv
from flask import Flask, Response, request, render_template
import json
import os
from langchain_openai import AzureChatOpenAI
from langchain_core.tools import tool

import azure.cosmos.documents as documents
import azure.cosmos.cosmos_client as cosmos_client
import azure.cosmos.exceptions as exceptions
from azure.cosmos.partition_key import PartitionKey


load_dotenv()

app = Flask(__name__)
CORS(app)

COSMOS_HOST = os.getenv('COSMOS_HOST')
COSMOS_MASTER_KEY = os.getenv('COSMOS_MASTER_KEY')
COSMOS_DATABASE_ID = os.getenv('COSMOS_DATABASE_ID')
COSMOS_CONTAINER_ID = os.getenv('COSMOS_CONTAINER_ID')







aoai_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
aoai_key = os.getenv("AZURE_OPENAI_API_KEY")
aoai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")



primary_llm = AzureChatOpenAI(
            azure_deployment=aoai_deployment,
            api_version="2024-05-01-preview",
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2,
            api_key=aoai_key,
            azure_endpoint=aoai_endpoint
    )


selected_rfp = None

@app.route('/select-rfp', methods=['POST'])
def select_rfp():
    global selected_rfp
    data = request.json
    selected_rfp = data.get('rfp_name')
    if selected_rfp:
        return jsonify({"message": f"Selected RFP: {selected_rfp}"}), 200
    else:
        return jsonify({"error": "No RFP name provided"}), 400

def get_rfps_from_cosmos():
    client = CosmosClient(COSMOS_HOST, {'masterKey': COSMOS_MASTER_KEY}, user_agent="CosmosDBPythonQuickstart", user_agent_overwrite=True)
    try:
        db = client.get_database_client(COSMOS_DATABASE_ID)
        container = db.get_container_client(COSMOS_CONTAINER_ID)
        
        query = "SELECT DISTINCT c.partitionKey FROM c"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        
        return [{"name": docs['partitionKey'], "status": 'Complete'} for docs in items]
    except Exception as e:
        print(f"Error reading from CosmosDB: {str(e)}")
        return []

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    start_upload_process(file)
    
    return jsonify({"message": "RFP Ingestion process started. This can take anywhere from 2 to 15 minutes."}), 202

@app.route('/available-rfps', methods=['GET'])
def get_rfps():
    cosmos_rfps = get_rfps_from_cosmos()
    in_memory_rfps = get_all_rfps()
    
    # Combine and deduplicate RFPs
    all_rfps = {rfp['name']: rfp for rfp in cosmos_rfps + in_memory_rfps}
    
    return jsonify(list(all_rfps.values()))

@app.route('/in-progress-rfps', methods=['GET'])
def get_in_progress_rfps():
    return jsonify(get_all_rfps())









client = cosmos_client.CosmosClient(COSMOS_HOST, {'masterKey': COSMOS_MASTER_KEY}, user_agent="CosmosDBUser", user_agent_overwrite=True)
try:
        # setup database for this sample
        try:
            db = client.create_database(id=COSMOS_DATABASE_ID)
            print('Database with id \'{0}\' created'.format(COSMOS_DATABASE_ID))

        except exceptions.CosmosResourceExistsError:
            db = client.get_database_client(COSMOS_DATABASE_ID)
            print('Database with id \'{0}\' was found'.format(COSMOS_DATABASE_ID))

        try:
                container = db.create_container(id=COSMOS_CONTAINER_ID, partition_key=PartitionKey(path='/partitionKey'))
                print('Container with id \'{0}\' created'.format(COSMOS_CONTAINER_ID))

        except exceptions.CosmosResourceExistsError:
                container = db.get_container_client(COSMOS_CONTAINER_ID)
                print('Container with id \'{0}\' was found'.format(COSMOS_CONTAINER_ID))
except exceptions.CosmosHttpResponseError as e:
        print('\nrun_sample has caught an error. {0}'.format(e.message))






if __name__ == '__main__':
    app.run(debug=True, threaded=True)