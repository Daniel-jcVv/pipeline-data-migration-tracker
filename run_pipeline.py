"""Main pipeline orchestrator."""
import logging
import argparse
from src.ingestion import init_tracker_db, download_from_sftp
from src.fabric_client import upload_to_fabric
from src.utils.file_tracker import FileTracker, FileStatus
import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

tracker = FileTracker(config.TRACKER_DB_PATH)

def run_pipeline(max_files=None):
    """
    Execute ETL pipeline: SFTP → Staging → Fabric.

    Args:
        max_files: Optional limit for testing (simulate partial failure)
    """
    logger.info("Starting pipeline...")
    if max_files:
        logger.warning(f"  TEST MODE: Processing max {max_files} files")

    init_tracker_db()

    # Download new files to staging (with limit if specified)
    new_files = download_from_sftp(max_files=max_files)
    logger.info(f"Downloaded {len(new_files)} new files")

    if not new_files:
        logger.info("No new files to process")
        return

    # Upload each file to Fabric
    for filename in new_files:
        logger.info(f"Processing {filename}...")

        try:
            staging_path = config.LOCAL_STAGING_PATH / filename
            fabric_dest = f"migration/{filename}"

            upload_to_fabric(staging_path, fabric_dest)
            logger.info(f"Uploaded to Fabric: {fabric_dest}")

            # Mark as loaded to Fabric
            file_size = staging_path.stat().st_size
            tracker.update_status(
                filename,
                FileStatus.LOADED_TO_FABRIC,
                file_size=file_size
            )
            
        except Exception as e:
            logger.error(f"Failed to process {filename}: {e}")
            tracker.mark_failed(filename, str(e))
            continue
    
    logger.info("Pipeline completed")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='SFTP to Fabric migration pipeline with idempotent file tracking'
    )
    parser.add_argument(
        '--max-files',
        type=int,
        help='Limit number of files to process (for testing partial failures)'
    )

    args = parser.parse_args()
    run_pipeline(max_files=args.max_files)
