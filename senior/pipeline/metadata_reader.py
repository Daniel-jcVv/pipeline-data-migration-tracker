"""
Metadata Reader
===============

Reads file metadata from data sources.
Equivalent to "Get Metadata" activity in Fabric pipelines.
"""

from typing import List, Dict, Any
from ..connectors.base_connector import BaseConnector


class MetadataReader:
    """
    Read file metadata from data sources.

    This class wraps connector functionality to provide a clean interface
    for reading file lists, similar to Fabric's Get Metadata activity.

    Example usage:
        from src.connectors import SFTPConnector

        config = {...}
        connector = SFTPConnector(config)

        reader = MetadataReader(connector)
        files = reader.get_file_list('/migration-files/csv/', '*.csv')

        for file in files:
            print(f"File: {file['name']}, Size: {file['size']}")
    """

    def __init__(self, connector: BaseConnector):
        """
        Initialize Metadata Reader with a connector.

        Args:
            connector: An instance of a BaseConnector subclass
        """
        self.connector = connector

    def get_file_list(
        self,
        path: str,
        pattern: str = "*",
        sort_by: str = "modified",
        reverse: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get list of files from data source.

        This is the equivalent of the "Get Metadata" activity with
        "Child Items" field list in Fabric pipelines.

        Args:
            path: Directory path to list files from
            pattern: File pattern to match (e.g., "*.csv", "*.json")
            sort_by: Field to sort by ('name', 'size', 'modified')
            reverse: Sort in reverse order (newest first if sort_by='modified')

        Returns:
            List of dictionaries containing file metadata
        """
        # Ensure connector is connected
        if not self.connector.connected:
            self.connector.connect()

        # Get file list from connector
        files = self.connector.list_files(path, pattern)

        # Sort if requested
        if sort_by and files:
            files = sorted(files, key=lambda x: x.get(sort_by, ''), reverse=reverse)

        return files

    def get_file_count(self, path: str, pattern: str = "*") -> int:
        """
        Get count of files matching pattern.

        Args:
            path: Directory path
            pattern: File pattern to match

        Returns:
            Number of files found
        """
        files = self.get_file_list(path, pattern)
        return len(files)

    def get_total_size(self, path: str, pattern: str = "*") -> int:
        """
        Get total size of all files matching pattern.

        Args:
            path: Directory path
            pattern: File pattern to match

        Returns:
            Total size in bytes
        """
        files = self.get_file_list(path, pattern)
        return sum(f.get('size', 0) for f in files)

    def get_file_names_only(self, path: str, pattern: str = "*") -> List[str]:
        """
        Get only the filenames (without full metadata).

        Useful for quick checks or filtering.

        Args:
            path: Directory path
            pattern: File pattern to match

        Returns:
            List of filenames
        """
        files = self.get_file_list(path, pattern)
        return [f['name'] for f in files]

    def filter_by_size(
        self,
        files: List[Dict[str, Any]],
        min_size: int = 0,
        max_size: int = None
    ) -> List[Dict[str, Any]]:
        """
        Filter files by size.

        Args:
            files: List of file metadata
            min_size: Minimum size in bytes
            max_size: Maximum size in bytes (None for no limit)

        Returns:
            Filtered list of files
        """
        filtered = [f for f in files if f.get('size', 0) >= min_size]

        if max_size is not None:
            filtered = [f for f in filtered if f.get('size', 0) <= max_size]

        return filtered

    def filter_by_date(
        self,
        files: List[Dict[str, Any]],
        after: Any = None,
        before: Any = None
    ) -> List[Dict[str, Any]]:
        """
        Filter files by modification date.

        Args:
            files: List of file metadata
            after: Only include files modified after this datetime
            before: Only include files modified before this datetime

        Returns:
            Filtered list of files
        """
        filtered = files

        if after:
            filtered = [f for f in filtered if f.get('modified') and f['modified'] >= after]

        if before:
            filtered = [f for f in filtered if f.get('modified') and f['modified'] <= before]

        return filtered
