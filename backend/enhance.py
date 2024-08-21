
import os
from dotenv import load_dotenv



from langchain_openai import AzureChatOpenAI

from azure.core.credentials import AzureKeyCredential
from azure.storage.blob import BlobServiceClient
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult

from helper_functions import get_rfp_analysis_from_db
from prompts import enhancement_prompt

load_dotenv()

# Azure Blob Storage
connect_str = os.getenv("STORAGE_ACCOUNT_CONNECTION_STRING")
storage_account_name = os.getenv("STORAGE_ACCOUNT_NAME")
container_name = "resumes"

#Doc intelligence
form_recognizer_endpoint = os.getenv("FORM_RECOGNIZER_ENDPOINT")
form_recognizer_key = os.getenv("FORM_RECOGNIZER_KEY")



# Azure OpenAI
aoai_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
aoai_key = os.getenv("AZURE_OPENAI_API_KEY")
aoai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")

endpoint = form_recognizer_endpoint
credential = AzureKeyCredential(form_recognizer_key)
document_intelligence_client = DocumentIntelligenceClient(endpoint, credential)



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

def read_pdf(input_file):
    blob_url = f"https://{storage_account_name}.blob.core.windows.net/{container_name}/{input_file}"
    analyze_request = {
        "urlSource": blob_url
    }
    poller = document_intelligence_client.begin_analyze_document("prebuilt-layout", analyze_request=analyze_request)
    result: AnalyzeResult = poller.result()
    #print(result.content)
    
    

    #read result object into a full text variable
    full_text = result.content
    print("Successfully read the PDF from blob storage with doc intelligence and extracted text.")
    return full_text


def enhance_resume(resume_name, rfp_name):
    
    print (f"Enhancing resume {resume_name} for RFP {rfp_name}")
    #Read the resume from blob storage
    folder = "processed"
    blob_name = f"{folder}/{resume_name}"
    resume_text = read_pdf(blob_name)

    #Read the analysis of the RFP from Cosmos DB 
    analysis = get_rfp_analysis_from_db(rfp_name)

    #Prepare messages for LLM
    input_message = f"<RFP Analysis>\n {analysis}\n\n <Resume>\n {resume_text}"

    messages = [{"role": "system", "content": enhancement_prompt}]
    messages.append({"role": "user", "content": input_message})

    for message in messages:
        print(message)

    #Pass the messages to the LLM and get the response
    response = primary_llm.invoke(messages)
    print("\n\n\n" , response.content)

    #Use the response to create a new DOCX file


    #Upload the new DOCX file to blob storage


    #Return the name of the new DOCX file

def list_blobs_in_folder(container_client, folder_name):
    return [blob for blob in container_client.list_blobs() if blob.name.startswith(folder_name)]
    
#Main function
if __name__ == "__main__":

    resume_name = "Abhay Ashok 717569.docx"
    rfp_name = "Combined_Synopsis_and_Solicitation.pdf"
    
    enhance_resume(resume_name, rfp_name)

    
    

