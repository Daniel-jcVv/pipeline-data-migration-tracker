"""
Validation Utilities
====================

Validation functions for files, configurations, and data.
"""

import os
from typing import Dict, Any, List
from pathlib import Path


def validate_file(file_path: str, required_extensions: List[str] = None) -> bool:
    """
    Validate that a file exists and has correct extension.

    Args:
        file_path: Path to file
        required_extensions: List of allowed extensions (e.g., ['.csv', '.json'])

    Returns:
        bool: True if file is valid

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file has wrong extension
    """
    path = Path(file_path)

    # Check existence
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Check if it's a file (not directory)
    if not path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    # Check extension if required
    if required_extensions:
        ext = path.suffix.lower()
        if ext not in [e.lower() for e in required_extensions]:
            raise ValueError(
                f"Invalid file extension: {ext}. "
                f"Expected one of: {', '.join(required_extensions)}"
            )

    return True


def validate_config(config: Dict[str, Any], required_keys: List[str]) -> bool:
    """
    Validate that configuration has all required keys.

    Args:
        config: Configuration dictionary
        required_keys: List of required key names

    Returns:
        bool: True if configuration is valid

    Raises:
        ValueError: If required keys are missing
    """
    missing_keys = [key for key in required_keys if key not in config]

    if missing_keys:
        raise ValueError(
            f"Missing required configuration keys: {', '.join(missing_keys)}"
        )

    return True


def validate_connection_config(config: Dict[str, Any], connector_type: str) -> bool:
    """
    Validate connector-specific configuration.

    Args:
        config: Configuration dictionary
        connector_type: Type of connector ('sftp', 's3')

    Returns:
        bool: True if configuration is valid

    Raises:
        ValueError: If configuration is invalid
    """
    if connector_type == 'sftp':
        required = ['host', 'username']
        if 'password' not in config and 'key_file' not in config:
            raise ValueError("SFTP config must have 'password' or 'key_file'")

    elif connector_type == 's3':
        required = ['bucket_name', 'aws_access_key_id', 'aws_secret_access_key']

    else:
        raise ValueError(f"Unknown connector type: {connector_type}")

    return validate_config(config, required)


def validate_path_structure(base_path: str, required_subdirs: List[str] = None) -> bool:
    """
    Validate directory structure.

    Args:
        base_path: Base directory path
        required_subdirs: List of required subdirectories

    Returns:
        bool: True if structure is valid

    Raises:
        NotADirectoryError: If base path is not a directory
        FileNotFoundError: If required subdirectories are missing
    """
    base = Path(base_path)

    if not base.exists():
        raise FileNotFoundError(f"Base path not found: {base_path}")

    if not base.is_dir():
        raise NotADirectoryError(f"Base path is not a directory: {base_path}")

    if required_subdirs:
        missing_dirs = []
        for subdir in required_subdirs:
            subdir_path = base / subdir
            if not subdir_path.exists() or not subdir_path.is_dir():
                missing_dirs.append(subdir)

        if missing_dirs:
            raise FileNotFoundError(
                f"Missing required subdirectories: {', '.join(missing_dirs)}"
            )

    return True
