"""
AWS S3 Connector
================

Connector for AWS S3 data sources.
"""

import boto3
import fnmatch
import os
from typing import List, Dict, Any
from datetime import datetime
from botocore.exceptions import ClientError

from .base_connector import BaseConnector


class S3Connector(BaseConnector):
    """
    aws S3 connector for file operations.

    example usage:
        config = {
            'bucket_name': 'fabric-migration-data',
            'aws_access_key_id': 'AKIAIOSFODNN7EXAMPLE',
            'aws_secret_access_key': 'wJalrXUtnFEMI/K7MDENG/hjashjas',
            'region_name': 'us-east-1'
        }

        with S3Connector(config) as s3:
            files = s3.list_files('migration-data/csv/', '*.csv')
            for file in files:
                print(f"Found: {file['name']}")
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize S3 connector.

        Args:
            config: Dictionary with keys:
                - bucket_name: S3 bucket name
                - aws_access_key_id: AWS access key
                - aws_secret_access_key: AWS secret key
                - region_name: AWS region (default: us-east-1)
                - endpoint_url: Custom S3 endpoint (optional, for MinIO)
        """
        super().__init__(config)
        self.s3_client = None
        self.bucket_name = config.get('bucket_name')

    def connect(self) -> bool:
        """
        Establish S3 connection.

        Returns:
            bool: True if connection successful
        """
        try:
            session_kwargs = {
                'aws_access_key_id': self.config.get('aws_access_key_id'),
                'aws_secret_access_key': self.config.get('aws_secret_access_key'),
                'region_name': self.config.get('region_name', 'us-east-1')
            }

            # Support for MinIO or custom S3-compatible endpoints
            if 'endpoint_url' in self.config:
                self.s3_client = boto3.client('s3',
                    endpoint_url=self.config['endpoint_url'],
                    **session_kwargs
                )
            else:
                self.s3_client = boto3.client('s3', **session_kwargs)

            # Test connection by listing buckets
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            self.connected = True

            return True

        except Exception as e:
            print(f"Failed to connect to S3: {e}")
            self.connected = False
            return False

    def disconnect(self) -> bool:
        """
        close S3 connection.
        returns:
            bool: True if disconnection successful
        """
        # S3 client doesn't need explicit disconnection
        self.connected = False
        return True

    def list_files(self, path: str, pattern: str = "*") -> List[Dict[str, Any]]:
        """
        List files in S3 bucket/prefix matching pattern.

        Args:
            path: s3 prefix (folder path)
            pattern: File pattern (e.g., "*.csv")

        Returns:
            List of file metadata dictionaries
        """
        if not self.connected:
            raise ConnectionError("Not connected to S3")

        files = []

        try:
            # Ensure prefix ends with / for proper listing
            prefix = path.rstrip('/') + '/' if path else ''

            # List objects with pagination
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.bucket_name, Prefix=prefix)

            for page in pages:
                if 'Contents' not in page:
                    continue

                for obj in page['Contents']:
                    # Skip folders (keys ending with /)
                    if obj['Key'].endswith('/'):
                        continue

                    # Get filename from key
                    filename = os.path.basename(obj['Key'])

                    # Match pattern
                    if fnmatch.fnmatch(filename, pattern):
                        files.append({
                            'name': filename,
                            'size': obj['Size'],
                            'modified': obj['LastModified'],
                            'path': obj['Key']
                        })

            return sorted(files, key=lambda x: x['modified'], reverse=True)

        except Exception as e:
            print(f"Error listing files: {e}")
            return []

    def download_file(self, remote_path: str, local_path: str) -> bool:
        """
        Download file from S3 to local filesystem.

        Args:
            remote_path: S3 object key
            local_path: Local destination path

        Returns:
            bool: True if download successful
        """
        if not self.connected:
            raise ConnectionError("Not connected to S3")

        try:
            # create local directory if needed
            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            # download file
            self.s3_client.download_file(self.bucket_name, remote_path, local_path)
            return True

        except Exception as e:
            print(f"Error downloading file {remote_path}: {e}")
            return False

    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """
        Upload file from local filesystem to S3.

        Args:
            local_path: Local file path
            remote_path: S3 object key (destination)

        Returns:
            bool: True if upload successful
        """
        if not self.connected:
            raise ConnectionError("Not connected to S3")

        try:
            # Upload file
            self.s3_client.upload_file(local_path, self.bucket_name, remote_path)
            return True

        except Exception as e:
            print(f"Error uploading file {local_path}: {e}")
            return False

    def file_exists(self, path: str) -> bool:
        """
        Check if file exists in S3 bucket.

        Args:
            path: S3 object key

        Returns:
            bool: True if file exists
        """
        if not self.connected:
            raise ConnectionError("Not connected to S3")

        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=path)
            return True
        except ClientError:
            return False

    def get_file_metadata(self, path: str) -> Dict[str, Any]:
        """
        get metadata for specific file in S3.

        Args:
            path: S3 object key

        Returns:
            dictionary with file metadata
        """
        if not self.connected:
            raise ConnectionError("Not connected to S3")

        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=path)
            return {
                'name': os.path.basename(path),
                'size': response['ContentLength'],
                'modified': response['LastModified'],
                'path': path,
                'content_type': response.get('ContentType'),
                'etag': response.get('ETag')
            }
        except Exception as e:
            print(f"Error getting file metadata: {e}")
            return {}
