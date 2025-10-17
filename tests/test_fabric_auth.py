"""Quick validation test for Fabric integration."""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.fabric_client import get_fabric_client
import config

def test_fabric_auth():
    """Test Azure authentication."""
    print("Testing Fabric authentication...")
    try:
        client = get_fabric_client()
        print(f"✅ Authenticated to OneLake")
        
        # Test workspace access
        fs = client.get_file_system_client(config.FABRIC_WORKSPACE_ID)
        print(f"✅ Workspace accessible: {config.FABRIC_WORKSPACE_ID}")
        return True
    except Exception as e:
        print(f"❌ Auth failed: {e}")
        return False

if __name__ == "__main__":
    success = test_fabric_auth()
    sys.exit(0 if success else 1)
