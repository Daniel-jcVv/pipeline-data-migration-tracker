"""
Fabric Uploader Module
This module handles uploading files to Microsoft Fabric Lakehouse.
"""

import os
from azure.identity import (
    DefaultAzureCredential,
    InteractiveBrowserCredential,
    DeviceCodeCredential,
    ClientSecretCredential,
)
from azure.storage.filedatalake import DataLakeServiceClient
import shutil
from dotenv import load_dotenv
from pathlib import Path
from typing import Optional
import logging
from tenacity import (
    retry,
    wait_exponential,
    stop_after_attempt,
    retry_if_exception_type,
)
import sys

logger = logging.getLogger(__name__)


class FabricUploader:
    def __init__(self, lakehouse_path: str, tenant_id: Optional[str] = None):
        """
        Initialize the FabricUploader with the Lakehouse path and optional tenant ID.
        """
        self.lakehouse_path = lakehouse_path
        self.tenant_id = tenant_id
        # Mock mode: when MOCK_FABRIC=true, don't attempt to use Azure SDK
        self.mock = os.getenv("MOCK_FABRIC", "false").lower() in ("1", "true")
        self.mock_base = os.getenv("MOCK_FABRIC_PATH", "data/fabric-mock")
        if self.mock:
            # ensure mock directory exists
            os.makedirs(self.mock_base, exist_ok=True)
            self.service_client = None
            logger.info(
                f"MOCK_FABRIC enabled: uploads will be written to "
                f"{self.mock_base}"
            )
        else:
            self.service_client = self._create_service_client()

    def _create_service_client(self) -> DataLakeServiceClient:
        """
        Create a DataLakeServiceClient using Interactive Browser
        Authentication.
        """
        try:
            # Credential selection logic (flexible for dev and prod)
            # Priority:
            # 1) ClientSecretCredential (service principal via AZURE_CLIENT_*)
            # 2) DefaultAzureCredential (managed identity / env variables)
            # 3) DeviceCodeCredential (developer-friendly device code flow)
            # 4) InteractiveBrowserCredential (fallback)
            logger.info("� Selecting Azure credential for Fabric uploader...")

            client_id = os.getenv("AZURE_CLIENT_ID")
            client_secret = os.getenv("AZURE_CLIENT_SECRET")
            tenant_id_env = os.getenv("AZURE_TENANT_ID") or self.tenant_id

            use_default = os.getenv(
                "USE_DEFAULT_CREDENTIAL", "false"
            ).lower() in ("1", "true")
            use_device_code = os.getenv(
                "USE_DEVICE_CODE", "false"
            ).lower() in ("1", "true")

            credential = None

            # 1) Client secret (service principal)
            if client_id and client_secret and tenant_id_env:
                logger.info("Using ClientSecretCredential (service principal)")
                credential = ClientSecretCredential(
                    tenant_id=tenant_id_env,
                    client_id=client_id,
                    client_secret=client_secret,
                )
            # 2) DefaultAzureCredential (e.g., managed identity or environment)
            elif use_default:
                logger.info("Using DefaultAzureCredential")
                credential = DefaultAzureCredential()
            # 3) Device code flow
            elif use_device_code:
                logger.info("Using DeviceCodeCredential (device code flow)")
                if tenant_id_env and tenant_id_env.strip():
                    credential = DeviceCodeCredential(tenant_id=tenant_id_env)
                else:
                    credential = DeviceCodeCredential()
            # 4) Fallback: interactive browser
            else:
                logger.info(
                    "Falling back to InteractiveBrowserCredential "
                    "(will open browser)"
                )
                if tenant_id_env and tenant_id_env.strip():
                    credential = InteractiveBrowserCredential(
                        tenant_id=tenant_id_env
                    )
                else:
                    credential = InteractiveBrowserCredential()
            
            # Parse lakehouse_path to get account_url
            # Parse lakehouse_path to build account_url.
            # Example format:
            # abfss://workspace@onelake.dfs.fabric.microsoft.com/
            #   lakehouse.Lakehouse/Files/path
            if "@" in self.lakehouse_path:
                account_url = (
                    "https://"
                    + self.lakehouse_path.split("@")[1].split("/")[0]
                )
            else:
                account_url = self.lakehouse_path

            service_client = DataLakeServiceClient(
                account_url=account_url,
                credential=credential,
            )
            logger.info("✅ Autenticación exitosa!")
            logger.info(f"✅ Service client creado para: {account_url}")
            return service_client
        except Exception as e:
            logger.error(f"❌ Failed to create DataLakeServiceClient: {e}")
            raise

    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(Exception),
    )
    def upload_file(self, local_file_path: str, remote_file_path: str) -> bool:
        """
        Upload a file to the Lakehouse with retries on failure.
        
        Args:
            local_file_path: Path to local file
            remote_file_path: Destination path in Fabric (just filename)
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # If mock mode is enabled, copy file to mock directory and
            # pretend it's uploaded
            if self.mock:
                # preserve any nested path in remote_file_path
                dest_path = os.path.join(
                    self.mock_base, remote_file_path
                )
                dest_dir = os.path.dirname(dest_path)
                if dest_dir:
                    os.makedirs(dest_dir, exist_ok=True)
                shutil.copy2(local_file_path, dest_path)
                file_size = Path(local_file_path).stat().st_size
                logger.info(
                    f"✅ [MOCK] Copied {local_file_path} -> {dest_path} "
                    f"({file_size:,} bytes)"
                )
                return True

            # Parse LAKEHOUSE_PATH to extract filesystem and path
            # Format: abfss://workspace@<account>.dfs.fabric.microsoft.com/
            # lakehouse.Lakehouse/Files/path
            parts = self.lakehouse_path.replace("abfss://", "").split("/")
            filesystem = parts[0].split("@")[0]  # workspace name
            lakehouse_path = "/".join(parts[1:])
            # lakehouse.Lakehouse/Files/path
            
            file_system_client = (
                self.service_client.get_file_system_client(
                    file_system=filesystem
                )
            )
            
            # Full path in Fabric
            full_remote_path = f"{lakehouse_path}/{remote_file_path}"
            file_client = file_system_client.get_file_client(full_remote_path)

            with open(local_file_path, "rb") as data:
                file_client.upload_data(data, overwrite=True)
            
            file_size = Path(local_file_path).stat().st_size
            logger.info(
                f"✅ Successfully uploaded {local_file_path} to "
                f"{full_remote_path} ({file_size:,} bytes)"
            )
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to upload {local_file_path}: {e}")
            return False
        

if __name__ == "__main__":
    load_dotenv()
    lakehouse_path = os.getenv("LAKEHOUSE_PATH")
    tenant_id = os.getenv("FABRIC_TENANT_ID")

    if not lakehouse_path:
        logger.error("LAKEHOUSE_PATH is not set in environment variables.")
        sys.exit(1)

    uploader = FabricUploader(
        lakehouse_path=lakehouse_path, tenant_id=tenant_id
    )
    test_file = "data/lakehouse/bronze/test_upload.csv"
    if Path(test_file).exists():
        uploader.upload_file(
            local_file_path=test_file, remote_file_path="test_upload.csv"
        )
    else:
        logger.error(f"Test file {test_file} does not exist.")


# Example usage:
# uploader = FabricUploader(lakehouse_path="abfss://datamigration@on
# .lake.fabric.microsoft.com/migration_lakehouse.Lakehouse/Files/migration",
# tenant_id="your-tenant-id")
# uploader.upload_file(local_file_path="path/to/local/file.csv", \
#     remote_file_path="file in/lakehouse.csv")
# Note: Ensure that the environment variables are set correctly in your
# .env file or environment.
# Required variables: LAKEHOUSE_PATH, FABRIC_TENANT_ID (optional)
# Also ensure that the Azure Identity and Azure Storage File Data Lake
# packages are installed:
# pip install azure-identity azure-storage-file-datalake python-dotenv \
#     tenacity logging
# Configure logging as needed for your application.
# This module uploads files to Microsoft Fabric Lakehouse with retry logic.
# Handle exceptions and logging according to your application's needs.
# Example .env entries:
# LAKEHOUSE_PATH=abfss://
# FABRIC_TENANT_ID=your-tenant-id
# SFTP_HOST=your-sftp-host
# SFTP_PORT=your-sftp-port
# SFTP_USERNAME=your-sftp-username
# SFTP_PASSWORD=your-sftp-password
# SFTP_REMOTE_PATH=your-sftp-remote-path
# TRACKER_DB_PATH=path/to/your/tracker.db
# Adjust the @retry parameters for your use case.
# Current: exponential backoff with 3 attempts.
# Ensure local and remote paths are correct when calling upload_file.
# This assumes the Lakehouse is accessible with the provided credentials.
# Test uploads in a safe environment before deploying to production.

