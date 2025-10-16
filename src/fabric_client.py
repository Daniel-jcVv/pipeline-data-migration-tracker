"""Microsoft Fabric client for file uploads."""
import logging
from azure.identity import ClientSecretCredential
from azure.storage.filedatalake import DataLakeServiceClient
from pathlib import Path
import config

logger = logging.getLogger(__name__)

def get_fabric_client() -> DataLakeServiceClient:
    """Authenticate and return Fabric client."""
    logger.info("Authenticating to Azure...")
    credential = ClientSecretCredential(
        tenant_id=config.AZURE_TENANT_ID,
        client_id=config.AZURE_CLIENT_ID,
        client_secret=config.AZURE_CLIENT_SECRET
    )
    
    account_url = "https://onelake.dfs.fabric.microsoft.com"
    return DataLakeServiceClient(account_url, credential=credential)

def upload_to_fabric(local_path: Path, fabric_path: str):
    """
    Upload file to Fabric Lakehouse.
    
    Args:
        local_path: Local file to upload (e.g., data/silver/ventas.parquet)
        fabric_path: Destination path in Lakehouse Files/ folder
                     (e.g., "silver/ventas.parquet")
                     Will be uploaded to: OneLake/{workspace}/{lakehouse}/Files/{fabric_path}
    
    Example:
        upload_to_fabric(
            Path("data/silver/sales.parquet"),
            "silver/sales.parquet"
        )
        # Result: https://onelake.../workspace_id/lakehouse_id/Files/silver/sales.parquet
    """
    logger.info(f"Uploading {local_path.name} to Fabric...")
    
    if config.MOCK_FABRIC:
        # Mock mode: copy to local folder for development
        mock_dest = config.MOCK_FABRIC_PATH / fabric_path
        mock_dest.parent.mkdir(parents=True, exist_ok=True)
        import shutil
        shutil.copy(local_path, mock_dest)
        logger.info(f"[MOCK] Copied to {mock_dest}")
        return
    
    # Real Fabric upload
    client = get_fabric_client()
    
    # Construct full OneLake path: workspace_id/lakehouse_id.Lakehouse/Files/
    full_path = f"{config.FABRIC_WORKSPACE_ID}/{config.FABRIC_LAKEHOUSE_ID}.Lakehouse/Files/{fabric_path}"
    
    # Get filesystem (workspace container)
    filesystem = client.get_file_system_client(config.FABRIC_WORKSPACE_ID)
    
    # Get file client with full lakehouse path
    file_client = filesystem.get_file_client(
        f"{config.FABRIC_LAKEHOUSE_ID}.Lakehouse/Files/{fabric_path}"
    )
    
    # Upload with overwrite
    with open(local_path, 'rb') as f:
        file_client.upload_data(f, overwrite=True)
    
    logger.info(f"✅ Uploaded to OneLake: {full_path}")
