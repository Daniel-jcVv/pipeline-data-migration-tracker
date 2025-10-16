"""Unit tests for transformations."""
import pytest
from pyspark.sql import SparkSession
from src.transformations import clean_data, get_spark

@pytest.fixture(scope="module")
def spark():
    return get_spark()

def test_clean_data_removes_nulls(spark):
    """Test null removal."""
    data = [("John", 30), (None, 25), ("Jane", None)]
    df = spark.createDataFrame(data, ["name", "age"])
    
    cleaned = clean_data(df)
    assert cleaned.count() == 1  # Only complete row

def test_clean_data_removes_duplicates(spark):
    """Test duplicate removal."""
    data = [("John", 30), ("John", 30), ("Jane", 25)]
    df = spark.createDataFrame(data, ["name", "age"])
    
    cleaned = clean_data(df)
    assert cleaned.count() == 2
