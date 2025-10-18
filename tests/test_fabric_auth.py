"""Quick validation test for Fabric integration."""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.fabric_client import get_access_token
import config

def test_fabric_auth():
    """Test Azure authentication."""
    print("Testing Fabric authentication...")
    print(f"Tenant ID: {config.AZURE_TENANT_ID[:8]}...")
    print(f"Client ID: {config.AZURE_CLIENT_ID[:8]}...")

    try:
        token = get_access_token()
        print(f"✅ Authenticated to Azure")
        print(f"✅ Access token obtained (length: {len(token)} chars)")
        print(f"✅ Ready to access Fabric workspace: {config.FABRIC_WORKSPACE_ID}")
        print(f"✅ Lakehouse: {config.FABRIC_LAKEHOUSE_ID}")
        return True
    except Exception as e:
        print(f"❌ Auth failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_fabric_auth()
    sys.exit(0 if success else 1)
