"""Test Fabric authentication"""
import logging
from pathlib import Path
from dotenv import load_dotenv
from src.fabric_client import get_fabric_client
import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

load_dotenv()

if __name__ == '__main__':
    print("Testing Fabric authentication...")
    print(f"Mock mode: {config.MOCK_FABRIC}")
    
    try:
        if not config.MOCK_FABRIC:
            client = get_fabric_client()
            print("Authentication successful")
        else:
            print("Mock mode enabled - no real auth needed")
    except Exception as e:
        print(f"Auth failed: {e}")
