"""CLI utility for monitoring and managing file tracker."""
import argparse
import sys
from pathlib import Path
from tabulate import tabulate
import config
from src.utils.file_tracker import FileTracker, FileStatus


def show_stats(tracker: FileTracker):
    """Display processing statistics."""
    stats = tracker.get_processing_stats()
    print("\n📊 Processing Statistics:")
    print(tabulate(
        [[status, count] for status, count in stats.items()],
        headers=["Status", "Count"],
        tablefmt="grid"
    ))


def show_failed(tracker: FileTracker):
    """Display failed files with errors."""
    failed = tracker.get_failed_files()
    if not failed:
        print("\n✅ No failed files")
        return
    
    print(f"\n❌ Failed Files ({len(failed)}):")
    print(tabulate(
        [[f['file_name'], f['error_message'][:50], f['last_updated']] 
         for f in failed],
        headers=["File", "Error", "Last Updated"],
        tablefmt="grid"
    ))


def reset_file(tracker: FileTracker, filename: str):
    """Reset a file to PENDING status."""
    tracker.reset_file(filename)
    print(f"✅ Reset {filename} to PENDING")


def main():
    parser = argparse.ArgumentParser(description="File Tracker Management")
    parser.add_argument("action", choices=["stats", "failed", "reset"],
                       help="Action to perform")
    parser.add_argument("--file", help="Filename (for reset action)")
    
    args = parser.parse_args()
    tracker = FileTracker(config.TRACKER_DB_PATH)
    
    if args.action == "stats":
        show_stats(tracker)
    elif args.action == "failed":
        show_failed(tracker)
    elif args.action == "reset":
        if not args.file:
            print("❌ --file required for reset action")
            sys.exit(1)
        reset_file(tracker, args.file)


if __name__ == "__main__":
    main()
