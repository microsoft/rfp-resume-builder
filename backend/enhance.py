
import os
from dotenv import load_dotenv


from langchain_openai import AzureChatOpenAI

from azure.core.credentials import AzureKeyCredential
from azure.storage.blob import BlobServiceClient, BlobClient
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult, AnalyzeDocumentRequest

from typing import List, Dict
from docx import Document
from io import BytesIO

from helper_functions import get_rfp_analysis_from_db
from prompts import reorder_work_experience_prompt

load_dotenv()

# Azure Blob Storage
connect_str = os.getenv("STORAGE_ACCOUNT_CONNECTION_STRING")
storage_account_name = os.getenv("STORAGE_ACCOUNT_NAME")
container_name = "sampleresumes"

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
    blob_name = f"{folder}/{resume_name}.docx"
    #blob_name = resume_name + ".docx"

    blob_url = f"https://{storage_account_name}.blob.core.windows.net/{container_name}/{blob_name}"
    blob_client = BlobClient.from_blob_url(blob_url=blob_url)
    with open(file=os.path.join('./', blob_name), mode="wb") as data:
        blob_client.download_blob().readinto(data)

    #Read the analysis of the RFP from Cosmos DB 
    analysis = get_rfp_analysis_from_db(rfp_name)

    #Use the analysis to create a new DOCX file
    with open('./' + blob_name, 'rb') as file:
        byte_stream = file.read()

    byte_stream_io = BytesIO(byte_stream)
    document = Document(byte_stream_io)
    print(len(document.paragraphs))
    work_experience_paragraph_number = 0
    prior_work_experience_paragraph_number = 0
    paragraph_counter = 0


    for paragraph in document.paragraphs:
        if "Work Experience" in paragraph.text:
            work_experience_paragraph_number = paragraph_counter
            print("Work Experience Paragraph Number: " + str(work_experience_paragraph_number))

        if "Prior to CDM Smith" in paragraph.text:
            prior_work_experience_paragraph_number = paragraph_counter
            print("Prior Experience Paragraph Number: " + str(prior_work_experience_paragraph_number))

        paragraph_counter += 1

    work_experience_string = ""
    paragraph_number = 1
    for i in range(work_experience_paragraph_number + 1, prior_work_experience_paragraph_number):
        work_experience_string = work_experience_string + str(paragraph_number) + ". " + document.paragraphs[work_experience_paragraph_number+paragraph_number].text + "\n\n"
        paragraph_number += 1

    print(work_experience_string)

    #Prepare messages for LLM
    work_experience_message = f"<RFP Analysis>\n {analysis}\n\n <Work Experience>\n {work_experience_string}"

    messages = [{"role": "system", "content": reorder_work_experience_prompt}]
    messages.append({"role": "user", "content": work_experience_message})
    response = primary_llm.invoke(messages)

    #Convert the LLM response into list so that it can be used to replace the document paragraphs   
    list_of_work_experience = response.content.split("\n\n")

    print(len(list_of_work_experience))
    print(response)

    #Use the liss to replace the document paragraphs
    paragraph_counter = 1
    for i in range(work_experience_paragraph_number + 1, prior_work_experience_paragraph_number):
        work_text = list_of_work_experience[paragraph_counter].partition(". ")[2]
        document.paragraphs[i].text = work_text
        paragraph_counter += 1

    print("New Document")
    for paragraph in document.paragraphs:
        print(paragraph.text)

    #Save the new DOCX file
    output_file = resume_name + "_enhanced_resume.docx"
    document.save("./" + output_file)

    #Upload the new DOCX file to blob storage
    blob_url = f"https://{storage_account_name}.blob.core.windows.net/{container_name}/{output_file}"
    blob_client = BlobClient.from_blob_url(blob_url=blob_url)
    with open(file=os.path.join('./', output_file), mode="rb") as data:
        blob_client = blob_client.upload_blob(data=data, overwrite=True)

    return output_file
    
#Main function
if __name__ == "__main__":

    resume_name = "Abhay Ashok 717569"
    rfp_name = "Combined_Synopsis_and_Solicitation.pdf"
    
    enhance_resume(resume_name, rfp_name)