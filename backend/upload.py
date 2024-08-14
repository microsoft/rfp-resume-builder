
import os  
from dotenv import load_dotenv  
import re
from concurrent.futures import ThreadPoolExecutor
import time
from werkzeug.datastructures import FileStorage
from io import BytesIO
import json
import threading
from global_vars import add_in_progress_upload, remove_in_progress_upload, set_upload_error

from langchain_openai import AzureChatOpenAI

from prompts import *

from azure.core.credentials import AzureKeyCredential  
from azure.identity import DefaultAzureCredential, ClientSecretCredential

from azure.ai.formrecognizer import DocumentAnalysisClient, AnalyzeResult 
from azure.eventhub import EventHubProducerClient, EventData   
import azure.cosmos.documents as documents
import azure.cosmos.cosmos_client as cosmos_client
import azure.cosmos.exceptions as exceptions
from azure.cosmos.partition_key import PartitionKey
from azure.storage.blob import BlobServiceClient


from flask import jsonify
from werkzeug.utils import secure_filename
import concurrent.futures
import io


# Create a ThreadPoolExecutor
executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)

load_dotenv()

form_recognizer_endpoint = os.getenv("FORM_RECOGNIZER_ENDPOINT")
form_recognizer_key = os.getenv("FORM_RECOGNIZER_KEY")


connect_str = os.getenv("STORAGE_ACCOUNT_CONNECTION_STRING")
container_name = os.getenv("STORAGE_ACCOUNT_CONTAINER")
storage_account_name = os.getenv("STORAGE_ACCOUNT_NAME")




document_analysis_client = DocumentAnalysisClient(
    endpoint=form_recognizer_endpoint, credential=AzureKeyCredential(form_recognizer_key)
)

aoai_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
aoai_key = os.getenv("AZURE_OPENAI_API_KEY")
aoai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")


COSMOS_HOST = os.getenv("COSMOS_HOST")
COSMOS_MASTER_KEY = os.getenv("COSMOS_MASTER_KEY")
COSMOS_DATABASE_ID = os.getenv("COSMOS_DATABASE_ID")
COSMOS_CONTAINER_ID = os.getenv("COSMOS_CONTAINER_ID")


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




# def upload_file_to_blob(file_obj):
#     """
#     Uploads a file to Azure Blob Storage
#     Inputs:
#     - file_obj: the file object to upload
#     - connect_str: the connection string for Azure Blob Storage
#     - container_name: the name of the container in Azure Blob Storage
#     - storage_account_name: the name of the storage account
#     """
    
#     # Create the BlobServiceClient object
#     blob_service_client = BlobServiceClient.from_connection_string(connect_str)

#     # Create a container client
#     container_client = blob_service_client.get_container_client(container_name)

#     # Extract the file name from the file object
#     file_name = file_obj.filename



#     # Create blob client
#     blob_client = blob_service_client.get_blob_client(container=container_name, blob=file_name)
#     # Create a blob client using the file name as the blob name
#     blob_client = container_client.get_blob_client(file_obj.filename)

#     if blob_client.exists():
#         print(f"Blob {file_name} already exists in {container_name}.")
#         # Handle the case where the blob exists (e.g., skip, overwrite, or prompt the user)
#         # For this example, we'll skip the upload
#         return {"message": f"File {file_name} already exists in Azure Blob Storage"}
#     # Upload the file
#     blob_client.upload_blob(file_obj.read(), overwrite=True)

        

#     # Upload the file
#     #blob_client.upload_blob(file_obj.stream, overwrite=True)

#     print(f"File {file_name} uploaded to {storage_account_name}/{container_name}/{file_name}")
#     return {"message": f"File {file_obj.filename} uploaded successfully to Azure Blob Storage"}



def inference(llm, messages, step, json_mode=False):
    
        start_time = time.time()
        # messages = [{"role": "system", "content": "You are a helpful AI assistant. always respond in json format with your thought process and answer."}]
        # messages.append([{"role": "user", "content": "What is 2+2?"}])

        # if json_mode:
        #     llm.bind(response_format={"type": "json_object"})
            


        raw_response = llm.invoke(messages)
        end_time = time.time()
        latency = end_time - start_time
        
        response = raw_response.content
        #print("Response: ", response)

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
        #step_telemetry.append(telemetry)
        #cosmos_db.write_to_cosmos(telemetry)
        return response




  

def write_to_cosmos(container, json):
    
    client = cosmos_client.CosmosClient(COSMOS_HOST, {'masterKey': COSMOS_MASTER_KEY}, user_agent="CosmosDBAgent", user_agent_overwrite=True)
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
    



    try:
        container.create_item(body=json)
        print('\nSuccess writing to cosmos...\n')
    except exceptions.CosmosHttpResponseError as e:
        print("Error writing to cosmos")
        print(f"Status code: {e.status_code}, Error message: {e.message}")
    except Exception as e:
        print("An unexpected error occurred")
        print(str(e))




# RDC - Refactor to use blob storage
def read_pdf(input_file):  
        """
        Function to read the PDF file from Azure Blob Storage and analyze it using Azure Document Intelligence
        Input:
        - input_file: name of the PDF to use 
        Output:
        - result: The result object from Azure Document Intelligence
        """
        
        # we need to use the document_analysis_client.begin_analyze_document_from_url method to read the PDF from blob storage
        blob_url = f"https://{storage_account_name}.blob.core.windows.net/{container_name}/{input_file}"

        # blob_url2 = "https://stgrfpdemo.blob.core.windows.net/rfp/MD_RFP_SUBSET%201.pdf"
        # poller = document_analysis_client.begin_analyze_document_from_url(model_id="prebuilt-layout", document_url=input_file)
        
        # poller = document_analysis_client.begin_analyze_document("prebuilt-layout", AnalyzeDocumentRequest(url_source=blob_url))       
        
        poller = document_analysis_client.begin_analyze_document_from_url("prebuilt-layout", blob_url)  

        result = poller.result()
        print("Successfully read the PDF from blob storage and analyzed.")
        return result








def upload_rfp(file_content, original_filename):
    try:
        print(f"Starting to process file: {original_filename}")
        add_in_progress_upload(original_filename)

        # Create a BytesIO object for blob storage upload
        blob_file = io.BytesIO(file_content)
        
        # Upload to blob storage
        upload_file_to_blob(blob_file, original_filename)
        print("File uploaded to blob storage")

        # Process the file
        print("Reading PDF")
        #pdf_file = io.BytesIO(file_content)
        adi_result_object = read_pdf(original_filename)
        print("PDF read complete")

        
        

        #Extract the skills and experience from the RFP via the LLM 
        skills_and_experience = "dummy string"

        

        print("Uploading to Cosmos DB")
        write_to_cosmos(COSMOS_CONTAINER_ID, skills_and_experience)
        print("Upload to Cosmos DB complete")
        
        remove_in_progress_upload(original_filename)
        print("In-progress upload removed")

    except Exception as e:
        print(f"Error processing RFP {original_filename}: {str(e)}")
        set_upload_error(original_filename)

    return

def start_upload_process(file):
    original_filename = secure_filename(file.filename)
    
    try:
        # Read file content
        file_content = file.read()
        
        # Submit the task to the thread pool
        executor.submit(upload_rfp, file_content, original_filename)
        
        return jsonify({"message": "RFP Ingestion process started."}), 202
    except Exception as e:
        print(f"Error starting upload process: {str(e)}")
        return jsonify({"error": "Failed to start upload process"}), 500

def upload_file_to_blob(file_obj, filename):
    """
    Uploads a file to Azure Blob Storage
    Inputs:
    - file_obj: BytesIO object containing file content
    - filename: name of the file in blob storage
    """
    print("Entering upload_file_to_blob function")
    
    # Create the BlobServiceClient object
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)

    # Create a container client
    container_client = blob_service_client.get_container_client(container_name)

    # Create blob client
    blob_client = container_client.get_blob_client(filename)

    if blob_client.exists():
        print(f"Blob {filename} already exists in {container_name}.")
        print(f"Overwriting existing blob {filename}")

    # Upload the file
    file_obj.seek(0)
    blob_client.upload_blob(file_obj, overwrite=True)

    print(f"File {filename} uploaded to {storage_account_name}/{container_name}/{filename}")
    return {"message": f"File {filename} uploaded successfully to Azure Blob Storage"}

if __name__ == "__main__":
    

    input_file = "xxx"
    input_blob = "xxx"
    
    
    upload_rfp(input_file)



    exit()