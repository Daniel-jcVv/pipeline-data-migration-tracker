"""SFTP ingestion with state tracking."""
import paramiko
import logging
from pathlib import Path
from typing import List
import config
from src.utils.file_tracker import FileTracker, FileStatus

logger = logging.getLogger(__name__)

# Initialize global tracker
tracker = FileTracker(config.TRACKER_DB_PATH)


def init_tracker_db():
    """Initialize file tracking database."""
    tracker.init_db()


def download_from_sftp() -> List[str]:
    """
    Download new files from SFTP to local staging folder.

    Returns:
        List of newly downloaded filenames
    """
    logger.info(f"Connecting to SFTP: {config.SFTP_HOST}:{config.SFTP_PORT}")
    config.LOCAL_STAGING_PATH.mkdir(parents=True, exist_ok=True)
    
    # Connect to SFTP
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        hostname=config.SFTP_HOST,
        port=config.SFTP_PORT,
        username=config.SFTP_USERNAME,
        password=config.SFTP_PASSWORD
    )
    
    sftp = ssh.open_sftp()
    logger.info(f"Scanning {config.SFTP_SERVER_PATH}...")
    
    # Get available CSV files
    available_files = [
        f for f in sftp.listdir(config.SFTP_SERVER_PATH)
        if f.endswith('.csv')
    ]
    
    # Filter pending files using tracker
    pending_files = tracker.get_pending_files(available_files)
    
    # Download pending files
    downloaded = []
    for filename in pending_files:
        try:
            remote_path = f"{config.SFTP_SERVER_PATH}/{filename}"
            local_path = config.LOCAL_STAGING_PATH / filename

            sftp.get(remote_path, str(local_path))
            file_size = local_path.stat().st_size

            # Mark as DOWNLOADED
            tracker.update_status(
                filename,
                FileStatus.DOWNLOADED,
                file_size=file_size
            )
            
            downloaded.append(filename)
            logger.info(f"Downloaded: {filename} ({file_size:,} bytes)")
            
        except Exception as e:
            logger.error(f"Failed to download {filename}: {e}")
            tracker.mark_failed(filename, str(e))
            continue
    
    sftp.close()
    ssh.close()
    
    logger.info(f"Downloaded {len(downloaded)}/{len(pending_files)} files")
    return downloaded


def mark_as_processed(filename: str, record_count: int = None):
    """Mark file as fully processed (COMPLETED)."""
    tracker.update_status(
        filename,
        FileStatus.COMPLETED,
        record_count=record_count
    )
