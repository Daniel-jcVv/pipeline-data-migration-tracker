"""
setup file tracker

script to initialize the file_tracker database.
Run this before starting the migration pipeline.

Usage:
    python scripts/setup_file_tracker.py
    python scripts/setup_file_tracker.py --db-path data/migration.db
    python scripts/setup_file_tracker.py --reset  # WARNING: Deletes all data
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline.file_tracker import FileTracker


def main():
    parser = argparse.ArgumentParser(
        description='initialize file tracker database'
    )
    parser.add_argument(
        '--db-path',
        type=str,
        default='data/migration.db',
        help='path to SQLite database file (default: data/migration.db)'
    )
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Reset tracker (delete all records) - USE WITH CAUTION'
    )

    args = parser.parse_args()

    # create connection string
    db_path = Path(args.db_path).absolute()
    connection_string = f'sqlite:///{db_path}'

    print("=" * 70)
    print("file tracker setup")
    print("=" * 70)
    print(f"Database: {db_path}")
    print()

    # Initialize tracker
    tracker = FileTracker(connection_string)

    # Reset if requested
    if args.reset:
        confirm = input("WARNING: This will delete ALL tracking data. Continue? (yes/no): ")
        if confirm.lower() == 'yes':
            if tracker.reset():
                print("tracker reset successfully")
            else:
                print("failed to reset tracker")
                sys.exit(1)
        else:
            print("reset cancelled")
            sys.exit(0)

    # initialize
    if tracker.initialize():
        print("File tracker initialized successfully!")
        print()

        # Show statistics
        stats = tracker.get_statistics()
        print("current statistics:")
        print(f"  Total files tracked: {stats['total_files']}")
        print(f"  Successfully loaded: {stats['loaded']}")
        print(f"  Failed: {stats['failed']}")
        print(f"  Total records: {stats.get('total_records', 0)}")
        print()

        print(f"Database location: {db_path}")
        print()
        print("You can now run the migration pipeline!")
    else:
        print("failed to initialize file tracker")
        sys.exit(1)


if __name__ == '__main__':
    main()
