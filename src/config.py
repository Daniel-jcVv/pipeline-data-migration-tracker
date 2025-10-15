"""
Configuration Management for Data Migration Pipeline

Centralizes all configuration from environment variables with validation.
Follows 12-Factor App methodology for secure and flexible config management.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """
    Central configuration class for the data migration pipeline.
    
    All configurations are loaded from environment variables, providing:
    - Security: No hardcoded credentials
    - Flexibility: Easy to change between dev/staging/prod
    - Validation: Ensures required configs are present
    """
    
    # SFTP Configuration
    SFTP_HOST = os.getenv('SFTP_HOST')
    SFTP_PORT = int(os.getenv('SFTP_PORT', 22))
    SFTP_USERNAME = os.getenv('SFTP_USERNAME')
    SFTP_PASSWORD = os.getenv('SFTP_PASSWORD')
    SFTP_SERVER_PATH = os.getenv('SFTP_SERVER_PATH')
    
    # Microsoft Fabric Configuration
    FABRIC_TENANT_ID = os.getenv('FABRIC_TENANT_ID')
    FABRIC_WORKSPACE_ID = os.getenv('FABRIC_WORKSPACE_ID')
    FABRIC_LAKEHOUSE_ID = os.getenv('FABRIC_LAKEHOUSE_ID')
    LAKEHOUSE_PATH = os.getenv('LAKEHOUSE_PATH', 'data/lakehouse/bronze/')
    
    # File Tracker Configuration
    TRACKER_DB_PATH = os.getenv('TRACKER_DB_PATH', 'data/file_tracker.db')
    # Local bronze directory (where files are downloaded before upload)
    LOCAL_BRONZE_PATH = os.getenv('LOCAL_BRONZE_PATH', 'data/lakehouse/bronze')
    
    @classmethod
    def validate(cls):
        """
        Validate that all required configuration values are present.
        
        Raises:
            ValueError: If any required configuration is missing
        """
        required_configs = {
            'SFTP_HOST': cls.SFTP_HOST,
            'SFTP_USERNAME': cls.SFTP_USERNAME,
            'SFTP_PASSWORD': cls.SFTP_PASSWORD,
            'SFTP_SERVER_PATH': cls.SFTP_SERVER_PATH,
        }
        
        missing = [key for key, value in required_configs.items() if not value]
        
        if missing:
            raise ValueError(
                f"Missing required configuration: {', '.join(missing)}\n"
                f"Please check your .env file."
            )
        
        return True
    
    @classmethod
    def to_dict(cls):
        """
        Convert configuration to dictionary format (legacy support).
        
        Returns:
            dict: Configuration grouped by component
        """
        return {
            'sftp': {
                'host': cls.SFTP_HOST,
                'port': cls.SFTP_PORT,
                'username': cls.SFTP_USERNAME,
                'password': cls.SFTP_PASSWORD,
                'remote_path': cls.SFTP_SERVER_PATH
            },
            'destination': {
                'lakehouse_path': cls.LAKEHOUSE_PATH
            },
            'tracker': {
                'db_path': cls.TRACKER_DB_PATH
            },
            'fabric': {
                'tenant_id': cls.FABRIC_TENANT_ID,
                'workspace_id': cls.FABRIC_WORKSPACE_ID,
                'lakehouse_id': cls.FABRIC_LAKEHOUSE_ID
            }
        }
