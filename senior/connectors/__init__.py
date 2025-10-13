"""
Connectors module
++++++++++++++++++++++++++

this module provides connectors for different data sources:
- SFTP connector
- aws S3 connector
- Base connector (abstract interface)
"""

from .base_connector import BaseConnector
from .sftp_connector import SFTPConnector
from .s3_connector import S3Connector

__all__ = ["BaseConnector", "SFTPConnector", "S3Connector"]
