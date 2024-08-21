from flask import Flask, request, jsonify
from flask_cors import CORS
from azure.cosmos import CosmosClient
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
import os
from langchain_openai import AzureChatOpenAI
from helper_functions import get_rfp_analysis_from_db

from upload import process_rfp
from search import search

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
    result = get_rfp_analysis_from_db(rfp_name)
    
    if result == "RFP name is required":
        return jsonify({"error": result}), 400
    elif result == "RFP analysis not found":
        return jsonify({"error": result}), 404
    elif result.startswith("An error occurred"):
        return jsonify({"error": result}), 500
    else:
        return jsonify({"skills_and_experience": result}), 200

@app.route('/search', methods=['POST'])
def search_employees():
    data = request.json
    rfp_name = data.get('rfpName')
    feedback = data.get('feedback')

    if not rfp_name:
        return jsonify({"error": "RFP name is required"}), 400

    try:

        results = search(rfp_name, feedback)
        return jsonify({"results": results}), 200
    
    except Exception as e:
        print(f"Error during search: {str(e)}")
        return jsonify({"error": "An error occurred during the search"}), 500

def generate_mock_enhanced_resume_link(resume_id, rfp_name):
    # This is a mock function to generate a fake enhanced resume link
    return f"http://example.com/enhanced-resumes/{resume_id}.pdf"

@app.route('/enhance', methods=['POST'])
def enhance_resume():
    data = request.json
    resume_name = data.get('resumeName')
    rfp_name = data.get('rfpName')
    print(f"Enhancing resume {resume_name} for RFP {rfp_name}")

    if not resume_name or not rfp_name:
        return jsonify({"error": "Missing resumeId or rfpName"}), 400

    # In a real implementation, you would process the resume here
    # For this mock-up, we'll just generate a fake enhanced resume link
    enhanced_resume_link = generate_mock_enhanced_resume_link(resume_name, rfp_name)

    return jsonify({
        "enhancedResumeLink": enhanced_resume_link
    }), 200

if __name__ == '__main__':
    app.run(debug=True, threaded=True)