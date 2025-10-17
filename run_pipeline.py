"""Main pipeline orchestrator."""
import logging
from src.ingestion import init_tracker_db, download_from_sftp
from src.fabric_client import upload_to_fabric
from src.utils.file_tracker import FileTracker, FileStatus
import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

tracker = FileTracker(config.TRACKER_DB_PATH)

def run_pipeline():
    """Execute ETL pipeline: SFTP → Staging → Fabric."""
    logger.info("Starting pipeline...")

    init_tracker_db()

    # Download new files to staging
    new_files = download_from_sftp()
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

            # Mark as complete
            file_size = staging_path.stat().st_size
            tracker.update_status(
                filename,
                FileStatus.COMPLETED,
                file_size=file_size
            )
            
        except Exception as e:
            logger.error(f"Failed to process {filename}: {e}")
            tracker.mark_failed(filename, str(e))
            continue
    
    logger.info("Pipeline completed")

if __name__ == "__main__":
    run_pipeline()
