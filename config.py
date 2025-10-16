"""Configuration management for data migration pipeline."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# SFTP
SFTP_HOST = os.getenv("SFTP_HOST", "localhost")
SFTP_PORT = int(os.getenv("SFTP_PORT", "22"))
SFTP_USERNAME = os.getenv("SFTP_USERNAME")
SFTP_PASSWORD = os.getenv("SFTP_PASSWORD")
SFTP_SERVER_PATH = os.getenv("SFTP_SERVER_PATH", "data/raw")

# Local paths
LOCAL_BRONZE_PATH = Path(os.getenv("LOCAL_BRONZE_PATH", "data/bronze"))
LOCAL_SILVER_PATH = Path(os.getenv("LOCAL_SILVER_PATH", "data/silver"))
TRACKER_DB_PATH = Path(os.getenv("TRACKER_DB_PATH", "data/metadata/file_tracker.db"))

# Azure/Fabric
FABRIC_WORKSPACE_ID = os.getenv("FABRIC_WORKSPACE_ID")
FABRIC_LAKEHOUSE_ID = os.getenv("FABRIC_LAKEHOUSE_ID")
AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")

# Mock mode
MOCK_FABRIC = os.getenv("MOCK_FABRIC", "false").lower() == "true"
MOCK_FABRIC_PATH = Path(os.getenv("MOCK_FABRIC_PATH", "data/fabric-mock"))
