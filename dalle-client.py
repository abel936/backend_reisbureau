# (BB) Add references
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI
import requests
import os
import json  # <-- Je miste deze import

# (BB) Load environment variables
load_dotenv()

# (BB) Get config values from .env
api_version = os.getenv("OPENAI_API_VERSION")
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
model_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

# (BB) User input (eventueel later dynamisch)
input_text = "A cute robot eating pancakes in space"

# (BB) Initialize the client
token_provider = get_bearer_token_provider(
    DefaultAzureCredential(exclude_environment_credential=True,
        exclude_managed_identity_credential=True), 
    "https://cognitiveservices.azure.com/.default"
)

print(f'======================================================={token_provider}')
    
client = AzureOpenAI(
    api_version=api_version,
    azure_endpoint=endpoint,
    azure_ad_token_provider=token_provider
)

print(f'======================================================={client}')

# (BB) Generate an image
result = client.images.generate(
     model=model_deployment,
     prompt=input_text,
     n=1
)

json_response = json.loads(result.model_dump_json())
image_url = json_response["data"][0]["url"]

print(f'======================================================={result}')

print("Generated image URL:", image_url)
