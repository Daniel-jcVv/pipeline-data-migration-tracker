"""
Base connector
==============

Abstract base class for all data source connectors.
Defines the interface that all connectors must implement.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime


class BaseConnector(ABC):
    """
    Abstract base class for data source connectors.

    All concrete connectors (SFTP, S3, etc.) must inherit from this class
    and implement all abstract methods.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the connector with configuration.

        Args:
            config: dictionary containing connection parameters
        """
        self.config = config
        self.connection = None
        self.connected = False

    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to the data source.

        Returns:
            bool: True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """
        close connection to the data source.

        Returns:
            bool: True if disconnection successful, False otherwise
        """
        pass

    @abstractmethod
    def list_files(self, path: str, pattern: str = "*") -> List[Dict[str, Any]]:
        """
        List files in the specified path matching the pattern.

        This is equivalent to the "get metadata" activity in fabric pipelines.

        Args:
            path: Directory path to list files from
            pattern: file pattern to match (e.g., "*.csv", "*.json")

        Returns:
            List of dictionaries containing file metadata:
            - name: filename
            - size: file size in bytes
            - modified: last modified timestamp
            - path: full path to file
        """
        pass

    @abstractmethod
    def download_file(self, remote_path: str, local_path: str) -> bool:
        """
        Download a file from the data source to local filesystem.

        Args:
            remote_path: Path to file in the data source
            local_path: Local path where file should be saved

        Returns:
            bool: True if download successful, False otherwise
        """
        pass

    @abstractmethod
    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """
        Upload a file from local filesystem to the data source.

        Args:
            local_path: Local path to file to upload
            remote_path: Destination path in the data source

        Returns:
            bool: True if upload successful, False otherwise
        """
        pass

    @abstractmethod
    def file_exists(self, path: str) -> bool:
        """
        Check if a file exists in the data source.

        Args:
            path: Path to file

        Returns:
            bool: True if file exists, False otherwise
        """
        pass

    @abstractmethod
    def get_file_metadata(self, path: str) -> Dict[str, Any]:
        """
        Get metadata for a specific file.

        Args:
            path: Path to file

        Returns:
            Dictionary containing file metadata (name, size, modified, etc.)
        """
        pass

    def __enter__(self):
        """Context manager entry - connect to source."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """context manager exit - disconnect from source."""
        self.disconnect()
