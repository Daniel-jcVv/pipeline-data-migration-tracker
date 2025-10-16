"""Main pipeline orchestrator."""
import logging
from src.ingestion import init_tracker_db, download_from_sftp, mark_as_processed
from src.transformations import process_bronze_to_silver
from src.fabric_client import upload_to_fabric

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def run_pipeline():
    """Execute ETL pipeline: SFTP -> Bronze -> Silver -> Fabric."""
    logger.info("Starting pipeline...")
    
    # Initialize tracker
    init_tracker_db()
    
    # Step 1: Download new files from SFTP server
    new_files = download_from_sftp()
    logger.info(f"Downloaded {len(new_files)} new files")
    
    if not new_files:
        logger.info("No new files to process")
        return
    
    # Step 2: Process each file
    for filename in new_files:
        logger.info(f"Processing {filename}...")
        
        try:
            # Transform Bronze -> Silver
            silver_path = process_bronze_to_silver(filename)
            logger.info(f"Transformed to {silver_path}")
            
            # Upload to Fabric
            fabric_dest = f"silver/{silver_path.name}"
            upload_to_fabric(silver_path, fabric_dest)
            logger.info(f"Uploaded to Fabric: {fabric_dest}")
            
            # Mark as processed
            mark_as_processed(filename)
            
        except Exception as e:
            logger.error(f"Failed to process {filename}: {e}")
            continue
    
    logger.info("Pipeline completed")

if __name__ == "__main__":
    run_pipeline()
