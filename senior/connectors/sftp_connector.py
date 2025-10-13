"""
SFTP Connector
==============

Connector for SFTP data sources.
"""

import paramiko
import fnmatch
import os
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path

from .base_connector import BaseConnector


class SFTPConnector(BaseConnector):
    """
    SFTP connector for file operations.

    Example usage:
        config = {
            'host': 'localhost',
            'port': 22,
            'username': 'fabricdata',
            'password': 'FabricMigration2025!',
            'timeout': 30
        }

        with SFTPConnector(config) as sftp:
            files = sftp.list_files('/migration-files/csv/', '*.csv')
            for file in files:
                print(f"Found: {file['name']}")
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize SFTP connector.

        Args:
            config: Dictionary with keys:
                - host: SFTP server hostname or IP
                - port: SFTP server port (default: 22)
                - username: SFTP username
                - password: SFTP password (or use key_file)
                - key_file: Path to SSH private key (optional)
                - timeout: Connection timeout in seconds (default: 30)
        """
        super().__init__(config)
        self.client = None
        self.sftp = None

    def connect(self) -> bool:
        """
        Establish SFTP connection.

        Returns:
            bool: True if connection successful
        """
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            connect_kwargs = {
                'hostname': self.config['host'],
                'port': self.config.get('port', 22),
                'username': self.config['username'],
                'timeout': self.config.get('timeout', 30)
            }

            # Use password or key file
            if 'password' in self.config:
                connect_kwargs['password'] = self.config['password']
            elif 'key_file' in self.config:
                connect_kwargs['key_filename'] = self.config['key_file']

            self.client.connect(**connect_kwargs)
            self.sftp = self.client.open_sftp()
            self.connected = True

            return True

        except Exception as e:
            print(f"Failed to connect to SFTP: {e}")
            self.connected = False
            return False

    def disconnect(self) -> bool:
        """
        Close SFTP connection.

        Returns:
            bool: True if disconnection successful
        """
        try:
            if self.sftp:
                self.sftp.close()
            if self.client:
                self.client.close()
            self.connected = False
            return True

        except Exception as e:
            print(f"Error disconnecting from SFTP: {e}")
            return False

    def list_files(self, path: str, pattern: str = "*") -> List[Dict[str, Any]]:
        """
        List files in SFTP directory matching pattern.

        Args:
            path: Remote directory path
            pattern: File pattern (e.g., "*.csv")

        Returns:
            List of file metadata dictionaries
        """
        if not self.connected:
            raise ConnectionError("Not connected to SFTP server")

        files = []

        try:
            # List all files in directory
            for attr in self.sftp.listdir_attr(path):
                # Skip directories
                if not attr.st_mode or attr.st_mode & 0o170000 == 0o040000:
                    continue

                # Match pattern
                if fnmatch.fnmatch(attr.filename, pattern):
                    files.append({
                        'name': attr.filename,
                        'size': attr.st_size,
                        'modified': datetime.fromtimestamp(attr.st_mtime),
                        'path': f"{path.rstrip('/')}/{attr.filename}"
                    })

            return sorted(files, key=lambda x: x['modified'], reverse=True)

        except Exception as e:
            print(f"Error listing files: {e}")
            return []

    def download_file(self, remote_path: str, local_path: str) -> bool:
        """
        Download file from SFTP to local filesystem.

        Args:
            remote_path: Remote file path
            local_path: Local destination path

        Returns:
            bool: True if download successful
        """
        if not self.connected:
            raise ConnectionError("Not connected to SFTP server")

        try:
            # Create local directory if needed
            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            # Download file
            self.sftp.get(remote_path, local_path)
            return True

        except Exception as e:
            print(f"Error downloading file {remote_path}: {e}")
            return False

    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """
        Upload file from local filesystem to SFTP.

        Args:
            local_path: Local file path
            remote_path: Remote destination path

        Returns:
            bool: True if upload successful
        """
        if not self.connected:
            raise ConnectionError("Not connected to SFTP server")

        try:
            # Create remote directory if needed
            remote_dir = os.path.dirname(remote_path)
            try:
                self.sftp.stat(remote_dir)
            except FileNotFoundError:
                self._create_remote_dir(remote_dir)

            # Upload file
            self.sftp.put(local_path, remote_path)
            return True

        except Exception as e:
            print(f"Error uploading file {local_path}: {e}")
            return False

    def file_exists(self, path: str) -> bool:
        """
        Check if file exists on SFTP server.

        Args:
            path: Remote file path

        Returns:
            bool: True if file exists
        """
        if not self.connected:
            raise ConnectionError("Not connected to SFTP server")

        try:
            self.sftp.stat(path)
            return True
        except FileNotFoundError:
            return False

    def get_file_metadata(self, path: str) -> Dict[str, Any]:
        """
        Get metadata for specific file.

        Args:
            path: Remote file path

        Returns:
            Dictionary with file metadata
        """
        if not self.connected:
            raise ConnectionError("Not connected to SFTP server")

        try:
            attr = self.sftp.stat(path)
            return {
                'name': os.path.basename(path),
                'size': attr.st_size,
                'modified': datetime.fromtimestamp(attr.st_mtime),
                'path': path
            }
        except Exception as e:
            print(f"Error getting file metadata: {e}")
            return {}

    def _create_remote_dir(self, path: str):
        """
        Recursively create remote directory.

        Args:
            path: Remote directory path
        """
        dirs = path.split('/')
        current = ''

        for dir_name in dirs:
            if not dir_name:
                continue

            current = f"{current}/{dir_name}" if current else dir_name

            try:
                self.sftp.stat(current)
            except FileNotFoundError:
                self.sftp.mkdir(current)
