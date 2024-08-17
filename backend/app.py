from flask import Flask, request, jsonify
from flask_cors import CORS
from azure.cosmos import CosmosClient
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
import os
from langchain_openai import AzureChatOpenAI

from upload import process_rfp

load_dotenv()

app = Flask(__name__)
CORS(app)

# Environment variables
COSMOS_HOST = os.getenv('COSMOS_HOST')
COSMOS_MASTER_KEY = os.getenv('COSMOS_MASTER_KEY')
COSMOS_DATABASE_ID = os.getenv('COSMOS_DATABASE_ID')
COSMOS_CONTAINER_ID = os.getenv('COSMOS_CONTAINER_ID')

AOAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
AOAI_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AOAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")

STORAGE_ACCOUNT_CONNECTION_STRING = os.getenv("STORAGE_ACCOUNT_CONNECTION_STRING")
STORAGE_ACCOUNT_CONTAINER = os.getenv("STORAGE_ACCOUNT_CONTAINER")

# Initialize Azure services
primary_llm = AzureChatOpenAI(
    azure_deployment=AOAI_DEPLOYMENT,
    api_version="2024-05-01-preview",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    api_key=AOAI_KEY,
    azure_endpoint=AOAI_ENDPOINT
)

cosmos_client = CosmosClient(COSMOS_HOST, {'masterKey': COSMOS_MASTER_KEY})
database = cosmos_client.get_database_client(COSMOS_DATABASE_ID)
container = database.get_container_client(COSMOS_CONTAINER_ID)

blob_service_client = BlobServiceClient.from_connection_string(STORAGE_ACCOUNT_CONNECTION_STRING)
blob_container_client = blob_service_client.get_container_client(STORAGE_ACCOUNT_CONTAINER)

def get_rfps_from_blob_storage():
    rfps = []
    blobs = blob_container_client.list_blobs()
    for blob in blobs:
        rfps.append({"name": blob.name, "status": "Complete"})
    return rfps

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    try:
        file_content = file.read()
        return process_rfp(file_content, file.filename)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/available-rfps', methods=['GET'])
def get_rfps():
    blob_rfps = get_rfps_from_blob_storage()
    return jsonify(blob_rfps)

@app.route('/get-rfp-analysis', methods=['GET'])
def get_rfp_analysis():
    rfp_name = request.args.get('rfp_name')
    if not rfp_name:
        return jsonify({"error": "RFP name is required"}), 400

    try:
        query = f"SELECT c.skills_and_experience FROM c WHERE c.partitionKey = '{rfp_name}'"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        
        if items:
            return jsonify({"skills_and_experience": items[0]['skills_and_experience']}), 200
        else:
            return jsonify({"error": "RFP analysis not found"}), 404
    except Exception as e:
        print(f"Error querying CosmosDB: {str(e)}")
        return jsonify({"error": "An error occurred while fetching RFP analysis"}), 500


@app.route('/search', methods=['POST'])
def search_employees():
    data = request.json
    rfp_name = data.get('rfpName')
    feedback = data.get('feedback')

    if not rfp_name:
        return jsonify({"error": "RFP name is required"}), 400

    try:
        # TODO: Implement actual search logic here
        # For now, we'll return dummy results
        dummy_results = [
            {"name": "JohnDoeResume.pdf", "url": "#"},
            {"name": "JaneDoeResume.pdf", "url": "#"},
            {"name": "BobSmithResume.pdf", "url": "#"}
        ]
        return jsonify({"results": dummy_results}), 200
    except Exception as e:
        print(f"Error during search: {str(e)}")
        return jsonify({"error": "An error occurred during the search"}), 500

if __name__ == '__main__':
    app.run(debug=True, threaded=True)