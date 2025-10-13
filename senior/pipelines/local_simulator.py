"""
Local pipeline simulator
Simulates fabric data pipeline locally for testing.

This script implements the same logic as the Fabric pipeline:
1. Get Metadata - List all files from source
2. Lookup - Get processed files from file_tracker
3. Filter - exclude already processed files
4. ForEach - process each remaining file:
   a. copy to Lakehouse (local directory)
   b. copy to Warehouse (simulated)
   c. update file_tracker

Usage:
    python pipelines/local_simulator.py --source sftp --config config/sftp_config.yaml
    python pipelines/local_simulator.py --source s3 --config config/s3_config.yaml
    python pipelines/local_simulator.py --dry-run  # Preview without processing
"""

import argparse
import sys
import yaml
from pathlib import Path
from datetime import datetime
import shutil

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.connectors import SFTPConnector, S3Connector
from src.pipeline import FileTracker, MetadataReader, FileFilter
from src.utils import setup_logger


def load_config(config_path: str) -> dict:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def simulate_pipeline(
    source_type: str,
    config: dict,
    dry_run: bool = False,
    file_pattern: str = "*.csv"
):
    """
    simulate the complete fabric data pipeline locally.

    Args:
        source_type: 'sftp' or 's3'
        config: configuration dictionary
        dry_run: If true, only preview without processing
        file_pattern:file pattern to match (e.g., '*.csv')
    """
    logger = setup_logger("pipeline_simulator", log_file="logs/pipeline.log")

    logger.info("=" * 70)
    logger.info("DATA MIGRATION PIPELINE SIMULATOR")
    logger.info("=" * 70)
    logger.info(f"Source Type: {source_type.upper()}")
    logger.info(f"Dry Run: {dry_run}")
    logger.info(f"File Pattern: {file_pattern}")
    logger.info("")

    # Step 0: initialize components
    logger.info("Step 0: Initializing components...")

    # Create connector
    if source_type == 'sftp':
        connector = SFTPConnector(config['source'])
    elif source_type == 's3':
        connector = S3Connector(config['source'])
    else:
        raise ValueError(f"Unknown source type: {source_type}")

    # Initialize file tracker
    tracker = FileTracker(config['file_tracker']['connection_string'])
    tracker.initialize()

    # Create metadata reader and filter
    reader = MetadataReader(connector)
    file_filter = FileFilter()

    # Create output directories
    lakehouse_path = Path(config['destination']['lakehouse_path'])
    lakehouse_path.mkdir(parents=True, exist_ok=True)

    logger.info("Components initialized")
    logger.info("")

    # Step 1: Get metadata (list all files from source)
    logger.info("Step 1: Get metadata - reading file list from source...")

    try:
        connector.connect()
        all_files = reader.get_file_list(
            config['source']['path'],
            file_pattern
        )
        logger.info(f"Found {len(all_files)} files in source")

        for file in all_files:
            logger.info(f"  - {file['name']} ({file['size']} bytes)")

    except Exception as e:
        logger.error(f"Failed to read file list: {e}")
        return False

    logger.info("")

    # Step 2: Lookup (Get processed files from file_tracker)
    logger.info("Step 2: Lookup - reading processed files from tracker...")

    processed_files = tracker.get_processed_files()
    logger.info(f"✓ Found {len(processed_files)} processed files")

    for filename in processed_files:
        logger.info(f"  - {filename}")

    logger.info("")

    # Step 3: Filter (exclude already processed files)
    logger.info("Step 3: filter - filtering out processed files...")

    remaining_files = file_filter.exclude_processed(all_files, processed_files)
    logger.info(f"{len(remaining_files)} files remaining to process")

    if not remaining_files:
        logger.info("no new files to process. All files are up to date")
        return True

    # Get processing summary
    summary = file_filter.get_processing_summary(all_files, processed_files)
    logger.info(f"")
    logger.info(f"Processing Summary:")
    logger.info(f"  Total files in source: {summary['total_files']}")
    logger.info(f"  Already processed: {summary['processed_count']}")
    logger.info(f"  Remaining to process: {summary['remaining_count']}")
    logger.info(f"  Total size to process: {summary['remaining_size']:,} bytes")
    logger.info("")

    # Stop here if dry run
    if dry_run:
        logger.info("DRY RUN - stopping here without processing files")
        logger.info("")
        logger.info("files that would be processed:")
        for file in remaining_files:
            logger.info(f"  - {file['name']}")
        return True

    # Step 4: ForEach (process each file)
    logger.info("Step 4: ForEach - processing files...")
    logger.info("")

    success_count = 0
    fail_count = 0

    for idx, file in enumerate(remaining_files, 1):
        filename = file['name']
        logger.info(f"[{idx}/{len(remaining_files)}] Processing: {filename}")

        try:
            # 4a: copy to lakehouse (download file)
            logger.info(f" --> copying to lakehouse...")
            local_path = lakehouse_path / filename

            if connector.download_file(file['path'], str(local_path)):
                logger.info(f"  copied to Lakehouse: {local_path}")
            else:
                raise Exception("failed to download file")

            # 4b: copy to warehouse (simulated)
            logger.info(f" --> loading to warehouse...")
            # In real fabric, this would be a copy data activity to warehouse table
            # For simulation, we just log it
            logger.info(f"  loaded to warehouse table")

            # 4c: Update file_tracker
            logger.info(f" --> updating file tracker...")
            if tracker.mark_processed(
                filename=filename,
                status='LOADED',
                file_size_bytes=file['size'],
                source_path=file['path']
            ):
                logger.info(f"  File tracker updated")
            else:
                raise Exception("failed to update file tracker")

            logger.info(f" successfully processed: {filename}")
            success_count += 1

        except Exception as e:
            logger.error(f"failed to process {filename}: {e}")
            fail_count += 1

            # Mark as failed in tracker
            tracker.mark_processed(
                filename=filename,
                status='FAILED',
                file_size_bytes=file['size'],
                source_path=file['path']
            )

        logger.info("")

    # final summary
    logger.info("=" * 70)
    logger.info("PIPELINE EXECUTION COMPLETE")
    logger.info("=" * 70)
    logger.info(f"total files processed: {success_count + fail_count}")
    logger.info(f"successful: {success_count}")
    logger.info(f"failed: {fail_count}")
    logger.info("")

    # Show tracker statistics
    stats = tracker.get_statistics()
    logger.info("file tracker statistics:")
    logger.info(f"  total files tracked: {stats['total_files']}")
    logger.info(f"  successfully loaded: {stats['loaded']}")
    logger.info(f"  failed: {stats['failed']}")
    logger.info("")

    # Cleanup
    connector.disconnect()
    tracker.close()

    return fail_count == 0


def main():
    parser = argparse.ArgumentParser(
        description='Simulate fabric data pipeline locally'
    )
    parser.add_argument(
        '--source',
        type=str,
        choices=['sftp', 's3'],
        required=True,
        help='Source type (sftp or s3)'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config/config.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--pattern',
        type=str,
        default='*.csv',
        help='File pattern to match (default: *.csv)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='preview without processing files'
    )

    args = parser.parse_args()

    # Load configuration
    try:
        config = load_config(args.config)
    except FileNotFoundError:
        print(f"Config file not found: {args.config}")
        print(f"Create it using config/.env.example as a template")
        sys.exit(1)

    # run pipeline
    success = simulate_pipeline(
        source_type=args.source,
        config=config,
        dry_run=args.dry_run,
        file_pattern=args.pattern
    )

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
