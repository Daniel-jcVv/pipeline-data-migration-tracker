"""
File Filter
===========

Filters files based on processing status.
Implements the "Filter Activity" logic from Fabric pipelines.
"""

from typing import List, Dict, Any


class FileFilter:
    """
    Filter files to exclude already processed ones.

    This implements the Filter activity logic from the transcript:
    - Compare source files with processed files (from file_tracker)
    - Exclude files that have been processed
    - Return only files that need to be processed

    The filter expression from the transcript:
    ```
    @and(
        not(contains(
            string(activity('Lookup').output.value),
            item().name
        )),
        endswith(item().name, '.csv')
    )
    ```

    Example usage:
        # Get all files from source
        all_files = metadata_reader.get_file_list('/data/', '*.csv')

        # Get processed files from tracker
        processed = file_tracker.get_processed_files()

        # Filter out processed files
        filter = FileFilter()
        remaining = filter.exclude_processed(all_files, processed)

        print(f"Total files: {len(all_files)}")
        print(f"Already processed: {len(processed)}")
        print(f"Remaining to process: {len(remaining)}")
    """

    def exclude_processed(
        self,
        all_files: List[Dict[str, Any]],
        processed_files: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Filter out files that have already been processed.

        This is the core filtering logic from the transcript.

        Args:
            all_files: List of all file metadata from source
            processed_files: List of processed filenames from file_tracker

        Returns:
            List of files that have NOT been processed yet
        """
        # Convert processed list to set for O(1) lookup
        processed_set = set(processed_files)

        # Filter out processed files
        remaining = [
            file for file in all_files
            if file['name'] not in processed_set
        ]

        return remaining

    def filter_by_extension(
        self,
        files: List[Dict[str, Any]],
        extensions: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Filter files by extension.

        Args:
            files: List of file metadata
            extensions: List of allowed extensions (e.g., ['.csv', '.json'])

        Returns:
            Filtered list of files
        """
        # Normalize extensions to lowercase and ensure they start with '.'
        normalized_ext = [
            ext if ext.startswith('.') else f'.{ext}'
            for ext in extensions
        ]
        normalized_ext = [ext.lower() for ext in normalized_ext]

        return [
            file for file in files
            if any(file['name'].lower().endswith(ext) for ext in normalized_ext)
        ]

    def filter_by_pattern(
        self,
        files: List[Dict[str, Any]],
        pattern: str
    ) -> List[Dict[str, Any]]:
        """
        Filter files by name pattern (simple contains check).

        Args:
            files: List of file metadata
            pattern: Pattern to match in filename

        Returns:
            Filtered list of files
        """
        return [
            file for file in files
            if pattern.lower() in file['name'].lower()
        ]

    def get_processing_summary(
        self,
        all_files: List[Dict[str, Any]],
        processed_files: List[str]
    ) -> Dict[str, Any]:
        """
        Get summary of files to be processed.

        Args:
            all_files: List of all file metadata from source
            processed_files: List of processed filenames

        Returns:
            Dictionary with processing summary
        """
        remaining = self.exclude_processed(all_files, processed_files)

        return {
            'total_files': len(all_files),
            'processed_count': len(processed_files),
            'remaining_count': len(remaining),
            'processed_files': processed_files,
            'remaining_files': [f['name'] for f in remaining],
            'total_size': sum(f.get('size', 0) for f in all_files),
            'remaining_size': sum(f.get('size', 0) for f in remaining)
        }

    def split_into_batches(
        self,
        files: List[Dict[str, Any]],
        batch_size: int
    ) -> List[List[Dict[str, Any]]]:
        """
        Split files into batches for parallel processing.

        Useful for ForEach activities with batch processing.

        Args:
            files: List of file metadata
            batch_size: Number of files per batch

        Returns:
            List of file batches
        """
        batches = []
        for i in range(0, len(files), batch_size):
            batches.append(files[i:i + batch_size])

        return batches
