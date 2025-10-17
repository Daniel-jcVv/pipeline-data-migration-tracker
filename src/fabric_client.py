"""Microsoft Fabric client using REST API."""
import logging
import requests
from azure.identity import ClientSecretCredential
from pathlib import Path
import config

logger = logging.getLogger(__name__)

def get_access_token() -> str:
    """Get Azure access token."""
    credential = ClientSecretCredential(
        tenant_id=config.AZURE_TENANT_ID,
        client_id=config.AZURE_CLIENT_ID,
        client_secret=config.AZURE_CLIENT_SECRET
    )
    token = credential.get_token("https://storage.azure.com/.default")
    return token.token

def upload_to_fabric(local_path: Path, fabric_path: str):
    """Upload file to Fabric Lakehouse using REST API."""
    logger.info(f"Uploading {local_path.name}...")
    
    token = get_access_token()
    
    # Use workspace name from FABRIC_LAKEHOUSE_PATH
    # abfss://datamigration@onelake...
    workspace_name = "datamigration"
    lakehouse_name = "migration_lakehouse"
    
    url = (
        f"https://onelake.dfs.fabric.microsoft.com/"
        f"{workspace_name}/{lakehouse_name}.Lakehouse/"
        f"Files/{fabric_path}"
    )
    
    headers = {
        "Authorization": f"Bearer {token}",
        "x-ms-version": "2023-11-03"
    }
    
    # Create file
    requests.put(f"{url}?resource=file", headers=headers)
    
    # Upload content
    with open(local_path, 'rb') as f:
        data = f.read()
    
    headers["Content-Length"] = str(len(data))
    requests.patch(f"{url}?action=append&position=0", headers=headers, data=data)
    
    # Flush
    headers["Content-Length"] = "0"
    response = requests.patch(f"{url}?action=flush&position={len(data)}", headers=headers)
    
    if response.status_code not in [200, 201]:
        raise Exception(f"Upload failed: {response.text}")
    
    logger.info(f"✅ Uploaded: Files/{fabric_path}")
