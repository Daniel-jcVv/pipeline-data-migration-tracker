"""
Data Migration Project for Microsoft Fabric
============================================

This package provides tools and utilities for migrating data from various sources
(SFTP, S3, etc.) to Microsoft Fabric Lakehouse and Warehouse.

Architecture:
- Bronze Layer: Raw data ingestion
- Silver Layer: Cleaned and normalized data
- Gold Layer: Aggregated business metrics

Key Features:
- File tracking to avoid reprocessing
- Multiple source connectors (SFTP, S3)
- Medallion architecture implementation
- Idempotent pipeline execution
"""

__version__ = "1.0.0"
__author__ = "Data Engineering Team"
