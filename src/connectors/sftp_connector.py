"""
SFTP Connector

Connects to SFTP server and lists/downloads CSV files.
"""

import paramiko
import os
from datetime import datetime


def connect_to_sftp(host, username, password, port=22):
    """
    Connect to SFTP server.

    Args:
        host: SFTP server address
        username: Username
        password: Password
        port: Port (default 22)

    Returns:
        sftp_client: Connected SFTP client
    """
    try:
        # Create SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Connect
        ssh.connect(
            hostname=host, username=username, password=password, port=port
        )
        sftp = ssh.open_sftp()

        print(f"Connected to SFTP: {host}")
        return sftp

    except Exception as e:
        print(f"Error connecting to SFTP: {e}")
        return None


def list_csv_files(sftp_client, remote_path):
    """
    List all CSV files in a remote folder.

    Args:
        sftp_client: Connected SFTP client
        remote_path: Remote path (e.g., '/migration-files/csv/')

    Returns:
        list: List of dictionaries with file info
    """
    files = []

    try:
        # List files in folder
        for file_attr in sftp_client.listdir_attr(remote_path):
            filename = file_attr.filename

            # Only CSV files
            if filename.endswith('.csv'):
                files.append({
                    'name': filename,
                    'size': file_attr.st_size,
                    'modified': datetime.fromtimestamp(file_attr.st_mtime),
                    'path': f"{remote_path}/{filename}"
                })

        print(f"✓ Found {len(files)} CSV files")
        return files

    except Exception as e:
        print(f"✗ Error listing files: {e}")
        return []


def download_file(sftp_client, remote_path, local_path):
    """
    Download a file from SFTP server.

    Args:
        sftp_client: Connected SFTP client
        remote_path: File path on server
        local_path: Where to save locally

    Returns:
        bool: True if downloaded successfully
    """
    try:
        # Create local directory if it doesn't exist
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        # Download file
        sftp_client.get(remote_path, local_path)
        print(f"Downloaded: {os.path.basename(remote_path)}")
        return True

    except Exception as e:
        print(f"Error downloading file: {e}")
        return False


def close_connection(sftp_client):
    """Close SFTP connection."""
    try:
        if sftp_client:
            sftp_client.close()
            print("SFTP connection closed")
    except:
        pass


# ============================================
# Usage example
# ============================================
if __name__ == '__main__':
    import os
    from dotenv import load_dotenv

    # Load credentials from .env
    load_dotenv()

    # Configuration from environment variables
    config = {
        'host': os.getenv('SFTP_HOST'),
        'username': os.getenv('SFTP_USERNAME'),
        'password': os.getenv('SFTP_PASSWORD'),
        'remote_path': os.getenv('SFTP_REMOTE_PATH')
    }

    # 1. Connect
    sftp = connect_to_sftp(
        host=config['host'],
        username=config['username'],
        password=config['password']
    )

    if sftp:
        # 2. List files
        files = list_csv_files(sftp, config['remote_path'])

        print("\nFiles found:")
        for f in files:
            print(f"  - {f['name']} ({f['size']} bytes)")

        # 3. Download first file (example)
        if files:
            first_file = files[0]
            download_file(
                sftp,
                first_file['path'],
                f"data/downloads/{first_file['name']}"
            )

        # 4. Close connection
        close_connection(sftp)
