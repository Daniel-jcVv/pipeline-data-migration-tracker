"""
Test Fabric Authentication
Prueba diferentes métodos de autenticación con Microsoft Fabric
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Agregar directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from src.fabric_uploader import FabricUploader

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

load_dotenv()

def test_connection():
    print("=" * 60)
    print("TEST: Fabric Authentication")
    print("=" * 60)
    
    lakehouse_path = os.getenv('LAKEHOUSE_PATH')
    tenant_id = os.getenv('FABRIC_TENANT_ID')
    
    print(f"\nLAKEHOUSE_PATH: {lakehouse_path}")
    print(f"FABRIC_TENANT_ID: {tenant_id}")
    
    if not lakehouse_path:
        print("\n❌ Error: LAKEHOUSE_PATH no configurado en .env")
        return
    
    print("\n🔐 Intentando conectar a Fabric...")
    print("(Si se abre navegador, inicia sesión con tu cuenta Microsoft)")
    
    try:
        uploader = FabricUploader(
            lakehouse_path=lakehouse_path,
            tenant_id=tenant_id
        )
        print("\n✅ Autenticación exitosa!")
        print("✅ Service client creado correctamente")
        
    except Exception as e:
        print(f"\n❌ Error en autenticación: {e}")
        print("\nPrueba estos pasos:")
        print("1. Verifica tu .env tiene LAKEHOUSE_PATH correcto")
        print("2. Ejecuta: az login")
        print("3. O permite que se abra el navegador para login interactivo")

if __name__ == '__main__':
    test_connection()