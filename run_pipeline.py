"""
Data Migration Pipeline to Microsoft Fabric

This script implements the complete migration flow:
1. Connect to SFTP (data source)
2. List available files
3. Check which ones have already been processed (file tracker)
4. Download only new files
5. Upload to Microsoft Fabric
6. Mark as processed

"""

import sys
import os
import logging

# Import centralized configuration
from src.config import Config

# Import modules (keep at top-level)
from src.connectors.sftp_connector import (
    connect_to_sftp, list_csv_files, download_file, close_connection
)
from src.services.file_tracker import (
    init_tracker,
    get_processed_files,
    filter_unprocessed_files,
    mark_as_processed,
    get_tracker_stats
)
from src.fabric_uploader import FabricUploader

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/pipeline/migration.log'),
        logging.StreamHandler()
    ]
)

# Silenciar logs verbosos
logging.getLogger('azure').setLevel(logging.WARNING)
logging.getLogger('paramiko').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Validate configuration on startup
try:
    Config.validate()
    logger.info("Configuration validated successfully")
except ValueError as e:
    logger.error(f"Configuration error: {e}")
    sys.exit(1)

# Get config as dictionary for legacy compatibility
config = Config.to_dict()


def print_header():
    """Print program header."""
    print("=" * 70)
    print("  DATA MIGRATION PIPELINE")
    print("  Microsoft Fabric - Data Migration Project")
    print("=" * 70)
    print()


def run_migration_pipeline(config, dry_run=False):
    """
    Execute the complete migration pipeline.

    Args:
        config: Dictionary with configuration (host, username, etc.)
        dry_run: If True, only shows what would be done without executing

    Returns:
        dict: Execution statistics
    """
    stats = {
        'total_files': 0,
        'already_processed': 0,
        'to_process': 0,
        'successfully_processed': 0,
        'failed': 0
    }

    print_header()

    if dry_run:
        logger.info("DRY-RUN MODE: Only showing what would be done")
        print("DRY-RUN MODE: Only showing what would be done\n")

    # STEP 1: Connect to SFTP
    logger.info("Connecting to SFTP server...")
    print("STEP 1: Connecting to SFTP server...")
    print("-" * 70)

    sftp = connect_to_sftp(
        host=config['sftp']['host'],
        username=config['sftp']['username'],
        password=config['sftp']['password']
    )

    if not sftp:
        logger.error("Could not connect to SFTP. Aborting.")
        print("Could not connect to SFTP. Aborting.")
        return stats

    logger.info(f"Connected to SFTP: {config['sftp']['host']}")
    print()

    # STEP 2: List files on SFTP
    logger.info("Listing files on server...")
    print("STEP 2: Listing files on server...")
    print("-" * 70)

    all_files = list_csv_files(sftp, config['sftp']['remote_path'])
    stats['total_files'] = len(all_files)

    if not all_files:
        logger.warning("No CSV files found")
        print("No CSV files found")
        close_connection(sftp)
        return stats

    logger.info(f"Found {len(all_files)} CSV files")
    print("\nFiles found:")
    for f in all_files:
        print(f"  {f['name']} - {f['size']:,} bytes")

    print()

    # STEP 3: Check already processed files
    logger.info("Checking already processed files...")
    print("STEP 3: Checking already processed files (File Tracker)...")
    print("-" * 70)

    tracker_conn = init_tracker(config['tracker']['db_path'])
    processed_files = get_processed_files(tracker_conn)
    stats['already_processed'] = len(processed_files)

    if processed_files:
        logger.info(f"Found {len(processed_files)} already processed files")
        print("\nAlready processed files:")
        for filename in processed_files:
            print(f"  {filename}")
    else:
        logger.info("No files processed yet (first execution)")
        print("  (none - first execution)")

    print()

    # STEP 4: Filter pending files
    logger.info("Filtering pending files...")
    print("STEP 4: Filtering pending files...")
    print("-" * 70)

    files_to_process = filter_unprocessed_files(all_files, processed_files)
    stats['to_process'] = len(files_to_process)

    if not files_to_process:
        logger.info("All files are already processed")
        print("\nAll files are already processed!")
        print("   Nothing new to migrate.")
        close_connection(sftp)
        tracker_conn.close()
        return stats

    logger.info(f"Found {len(files_to_process)} files to process")
    print("\nFiles to be processed:")
    for f in files_to_process:
        print(f"  {f['name']}")

    print()

    # If it's dry-run, stop here
    if dry_run:
        logger.info("Dry-run mode: stopping before download")
        print("DRY-RUN: Stopping here. No files were downloaded.")
        close_connection(sftp)
        tracker_conn.close()
        return stats

    # STEP 5: Process each file
    logger.info(f"Starting to process {len(files_to_process)} files...")
    print("STEP 5: Processing files...")
    print("-" * 70)

    # Create FabricUploader once (avoid per-file interactive auth)
    fabric_uploader = FabricUploader(
        lakehouse_path=config['destination']['lakehouse_path'],
        tenant_id=Config.FABRIC_TENANT_ID
    )

    for idx, file_info in enumerate(files_to_process, 1):
        filename = file_info['name']
        logger.info(f"[{idx}/{len(files_to_process)}] Processing: {filename}")
        print(f"\n[{idx}/{len(files_to_process)}] Processing: {filename}")

        try:
            # 5a. Download file to local bronze layer
            local_bronze_path = os.path.join(
                Config.LOCAL_BRONZE_PATH, filename
            )
            os.makedirs(Config.LOCAL_BRONZE_PATH, exist_ok=True)
            
            success = download_file(sftp, file_info['path'], local_bronze_path)

            if not success:
                raise Exception("Error downloading file")
            
            logger.info(f"Downloaded to: {local_bronze_path}")
            print(f"      → Downloaded to: {local_bronze_path}")

            # 5b. Upload to Fabric Lakehouse (reusing uploader instance)
            logger.info("Uploading to Fabric Lakehouse...")
            print("      → Uploading to Fabric Lakehouse...")

            upload_success = fabric_uploader.upload_file(
                local_file_path=local_bronze_path,
                remote_file_path=filename,
            )
            
            if not upload_success:
                raise Exception("Error uploading to Fabric")

            # 5c. Mark as processed in tracker
            mark_as_processed(
                tracker_conn,
                filename,
                status='LOADED_TO_FABRIC',
                file_size=file_info['size']
            )

            stats['successfully_processed'] += 1
            logger.info(f"✓ Successfully processed: {filename}")
            print(f"      ✓ COMPLETED: {filename}")

        except Exception as e:
            logger.error(f"✗ Failed to process {filename}: {e}")
            print(f"      ✗ Error: {e}")
            stats['failed'] += 1

            # Mark as failed in tracker
            mark_as_processed(
                tracker_conn,
                filename,
                status='FAILED',
                file_size=file_info.get('size', 0)
            )

    print()

    # STEP 6: Final summary
    logger.info("Pipeline execution completed")
    print("=" * 77)
    print("  EXECUTION SUMMARY")
    print("=" * 77)
    print(f"Total files at source:       {stats['total_files']}")
    print(f"Already processed before:    {stats['already_processed']}")
    print(f"New files to process:        {stats['to_process']}")
    print(f"Successfully processed:      {stats['successfully_processed']} ✓")
    print(f"Failed:                      {stats['failed']}")
    print()

    # Tracker statistics
    tracker_stats = get_tracker_stats(tracker_conn)
    print("File Tracker Statistics:")
    print(f"  Total tracked files: {tracker_stats['total_files']}")
    print(f"  By status: {tracker_stats['by_status']}")
    print()

    # Close connections
    close_connection(sftp)
    tracker_conn.close()

    return stats


def main():
    """Main function."""
    logger.info("=" * 70)
    logger.info("Starting Data Migration Pipeline")
    logger.info("=" * 70)

    # Check if it's dry-run
    dry_run = '--dry-run' in sys.argv

    # Execute pipeline
    stats = run_migration_pipeline(config, dry_run=dry_run)

    # Exit / final message logic
    if stats['failed'] > 0:
        logger.warning("Pipeline completed with errors")
        print("Pipeline completed with errors")
        sys.exit(1)

    # If this was a dry-run, report that nothing was changed and exit 0
    if dry_run:
        logger.info("Pipeline completed (dry-run) - no files were changed")
        print("Pipeline completed (dry-run). No files were changed.")
        sys.exit(0)

    # No files found or nothing to process
    if stats['to_process'] == 0 and stats['successfully_processed'] == 0:
        logger.info("Pipeline completed: no files found or to process")
        print("Pipeline completed: no files were found or to process.")
        sys.exit(0)

    # Files were found but none were successfully processed
    if stats['to_process'] > 0 and stats['successfully_processed'] == 0:
        logger.warning(
            "Pipeline completed but no files were successfully processed"
        )
        print("Pipeline completed but no files were successfully processed")
        # Use exit code 2 to indicate an execution where work was attempted
        # but no files were successfully processed (not an internal error).
        sys.exit(2)

    # Normal successful run
    logger.info("Pipeline completed successfully")
    print("Pipeline completed successfully!")
    sys.exit(0)


if __name__ == '__main__':
    main()
