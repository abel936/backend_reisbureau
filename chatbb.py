from openai import OpenAI
from dotenv import load_dotenv
import os, base64, uuid
from datetime import datetime, timedelta
from azure.storage.blob import (
    BlobServiceClient, ContentSettings,
    generate_blob_sas, BlobSasPermissions
)


def Afb_generen_met_url():
    load_dotenv()

    apikey = os.getenv("OPENAI_API_KEY")
    if not apikey:
        raise RuntimeError("Zet OPENAI_API_KEY in je .env")
    
    client = OpenAI(api_key=apikey)

    prompt = input("Wat voor afbeelding wil je genereren? ")

    #prompt = "Genereer een afbeelding van een strandvakantie in Curacao."

    # (BB) genereer de afbeelding
    result = client.images.generate(
        model= "gpt-image-1",
        prompt = prompt,
        size = "1024x1024",
        n=1
    )
    
    # (BB) Haal de base64 payload op en decodeer naar bytes
    img_b64 = result.data[0].b64_json
    img_bytes = base64.b64decode(img_b64)

    # (BB) maak een unieke bestandsnaam met UUID
    unique_name = f"{uuid.uuid4().hex}.png"
    
    with open(unique_name, "wb") as f:
        f.write(img_bytes)

    
    # (BB) koppelen met azure storage account
    conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    container_name = os.getenv("AZURE_STORAGE_CONTAINER", "images")

    svc = BlobServiceClient.from_connection_string(conn_str)
    container_client = svc.get_container_client(container_name)
    try:
        container_client.create_container()
    except Exception:
        pass

    # (BB) het maken van een unieke naam
    blob_name = f"{uuid.uuid4().hex}.png"
    blob_client = container_client.get_blob_client(blob_name)
    blob_client.upload_blob(img_bytes, overwrite=True, content_settings=ContentSettings(content_type="image/png"))

    # (BB) SAS-token (24 uur geldig, tijdelijke beveiligde toegangssleutel)
    sas = generate_blob_sas(
        account_name=svc.account_name,
        container_name=container_name,
        blob_name=blob_name,
        account_key=svc.credential.account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(hours=24)
    )

    
    image_url = f"https://{svc.account_name}.blob.core.windows.net/{container_name}/{blob_name}?{sas}"

    return image_url, unique_name
    

if __name__ == "__main__":
    Afb_generen_met_url()
