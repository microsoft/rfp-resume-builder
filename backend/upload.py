import os
from dotenv import load_dotenv
import time
from io import BytesIO
import json
import concurrent.futures
from global_vars import add_in_progress_upload, remove_in_progress_upload, set_upload_error

from langchain_openai import AzureChatOpenAI

from prompts import skills_and_experience_prompt

from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.storage.blob import BlobServiceClient
import azure.cosmos.cosmos_client as cosmos_client
import azure.cosmos.exceptions as exceptions
from azure.cosmos.partition_key import PartitionKey

from flask import jsonify
from werkzeug.utils import secure_filename

# Create a ThreadPoolExecutor
executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)

load_dotenv()

# Azure Form Recognizer
form_recognizer_endpoint = os.getenv("FORM_RECOGNIZER_ENDPOINT")
form_recognizer_key = os.getenv("FORM_RECOGNIZER_KEY")

# Azure Blob Storage
connect_str = os.getenv("STORAGE_ACCOUNT_CONNECTION_STRING")
container_name = os.getenv("STORAGE_ACCOUNT_CONTAINER")
storage_account_name = os.getenv("STORAGE_ACCOUNT_NAME")

# Azure Cosmos DB
COSMOS_HOST = os.getenv("COSMOS_HOST")
COSMOS_MASTER_KEY = os.getenv("COSMOS_MASTER_KEY")
COSMOS_DATABASE_ID = os.getenv("COSMOS_DATABASE_ID")
COSMOS_CONTAINER_ID = os.getenv("COSMOS_CONTAINER_ID")

# Azure OpenAI
aoai_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
aoai_key = os.getenv("AZURE_OPENAI_API_KEY")
aoai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")

# Initialize clients
document_analysis_client = DocumentAnalysisClient(
    endpoint=form_recognizer_endpoint, credential=AzureKeyCredential(form_recognizer_key)
)

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

primary_llm_json = AzureChatOpenAI(
    azure_deployment=aoai_deployment,
    api_version="2024-05-01-preview",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    api_key=aoai_key,
    azure_endpoint=aoai_endpoint,
    model_kwargs={"response_format": {"type": "json_object"}}
)

def inference(llm, messages, step, json_mode=False):
    start_time = time.time()
    raw_response = llm.invoke(messages)
    end_time = time.time()
    latency = end_time - start_time
    
    response = raw_response.content

    if json_mode:
        response = json.loads(raw_response.content)
        
    messages.append({"role": "assistant", "content": response})

    telemetry = {
        "step_name": step, 
        "step_type": "llm",
        "endpoint": llm.azure_endpoint,
        "deployment": llm.deployment_name,
        "version": llm.openai_api_version, 
        "messages": messages,
        "tokens": raw_response.usage_metadata,
        "latency": latency
    }
    return response

def write_to_cosmos(container, json):
    client = cosmos_client.CosmosClient(COSMOS_HOST, {'masterKey': COSMOS_MASTER_KEY}, user_agent="CosmosDBAgent", user_agent_overwrite=True)
    try:
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
    
    try:
        container.create_item(body=json)
        print('\nSuccess writing to cosmos...\n')
    except exceptions.CosmosHttpResponseError as e:
        print("Error writing to cosmos")
        print(f"Status code: {e.status_code}, Error message: {e.message}")
    except Exception as e:
        print("An unexpected error occurred")
        print(str(e))

def read_pdf(input_file):
    blob_url = f"https://{storage_account_name}.blob.core.windows.net/{container_name}/{input_file}"
    poller = document_analysis_client.begin_analyze_document_from_url("prebuilt-layout", blob_url)
    result = poller.result()
    print("Successfully read the PDF from blob storage and analyzed.")
    return result

def extract_skills_and_experience(result):
    text = ""
    for page in result.pages:
        for line in page.lines:
            text += line.content
    
    messages = [{"role": "system", "content": skills_and_experience_prompt}]
    messages.append({"role": "user", "content": text})
    
    skills_and_experience = inference(primary_llm, messages, "Extract Skills and Experience")
    
    return skills_and_experience

def process_rfp(file_content, original_filename):
    try:
        blob_file = BytesIO(file_content)
        upload_file_to_blob(blob_file, original_filename)

        adi_result_object = read_pdf(original_filename)
        skills_and_experience = extract_skills_and_experience(adi_result_object)

        skills_and_experience_json = {
            "id": original_filename + "_analysis",
            "partitionKey": original_filename,
            "skills_and_experience": skills_and_experience
        }

        write_to_cosmos(COSMOS_CONTAINER_ID, skills_and_experience_json)

        for chunk in primary_llm.stream([{"role": "user", "content": f"Format the following skills and experience as markdown:\n\n{skills_and_experience}"}]):
            yield chunk.content

    except Exception as e:
        yield f"Error processing RFP {original_filename}: {str(e)}\n"

def start_upload_process(file):
    original_filename = secure_filename(file.filename)
    
    try:
        file_content = file.read()
        executor.submit(upload_rfp, file_content, original_filename)
        return jsonify({"message": "RFP Ingestion process started."}), 202
    except Exception as e:
        print(f"Error starting upload process: {str(e)}")
        return jsonify({"error": "Failed to start upload process"}), 500

def upload_file_to_blob(file_obj, filename):
    print("Entering upload_file_to_blob function")
    
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)
    container_client = blob_service_client.get_container_client(container_name)
    blob_client = container_client.get_blob_client(filename)

    if blob_client.exists():
        print(f"Blob {filename} already exists in {container_name}.")
        print(f"Overwriting existing blob {filename}")

    file_obj.seek(0)
    blob_client.upload_blob(file_obj, overwrite=True)

    print(f"File {filename} uploaded to {storage_account_name}/{container_name}/{filename}")
    return {"message": f"File {filename} uploaded successfully to Azure Blob Storage"}

if __name__ == "__main__":
    input_file = "xxx"
    input_blob = "xxx"
    
    upload_rfp(input_file)

    exit()