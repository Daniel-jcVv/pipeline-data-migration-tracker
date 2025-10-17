"""Data transformations: Bronze → Silver."""
import logging
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, trim
from pathlib import Path
import config
from src.utils.file_tracker import FileTracker, FileStatus

logger = logging.getLogger(__name__)
tracker = FileTracker(config.TRACKER_DB_PATH)


def get_spark() -> SparkSession:
    """Initialize Spark session."""
    return SparkSession.builder \
        .appName("DataMigration") \
        .config("spark.driver.memory", "2g") \
        .getOrCreate()


def clean_data(df: DataFrame) -> DataFrame:
    """Apply basic cleaning: nulls, duplicates, trim."""
    df = df.na.drop()
    
    for col_name, dtype in df.dtypes:
        if dtype == 'string':
            df = df.withColumn(col_name, trim(col(col_name)))
    
    df = df.dropDuplicates()
    return df


def process_bronze_to_silver(filename: str) -> Path:
    """
    Transform bronze CSV to clean silver CSV.
    Updates tracker state to SILVER_CLEANED on success.
    """
    logger.info(f"Transforming {filename}...")
    spark = get_spark()
    bronze_path = config.LOCAL_BRONZE_PATH / filename
    
    try:
        # Read and clean
        df = spark.read.csv(str(bronze_path), header=True, inferSchema=True)
        rows_before = df.count()
        df_clean = clean_data(df)
        rows_after = df_clean.count()
        logger.info(f"Cleaned: {rows_before} → {rows_after} rows")
        
        # Write silver CSV (single file for Fabric upload)
        silver_path = config.LOCAL_SILVER_PATH / filename
        silver_path.parent.mkdir(parents=True, exist_ok=True)
        df_clean.coalesce(1).write.mode("overwrite").csv(
            str(silver_path.parent / f"{filename}.tmp"),
            header=True
        )
        
        # Move the part file to final name
        import glob
        part_file = glob.glob(str(silver_path.parent / f"{filename}.tmp/part-*.csv"))[0]
        import shutil
        shutil.move(part_file, silver_path)
        shutil.rmtree(silver_path.parent / f"{filename}.tmp")
        
        # Update tracker
        tracker.update_status(
            filename,
            FileStatus.SILVER_CLEANED,
            record_count=rows_after
        )
        
        logger.info(f"Saved to {silver_path}")
        return silver_path
        
    except Exception as e:
        logger.error(f"Transformation failed: {e}")
        tracker.mark_failed(filename, str(e))
        raise
