## Escenario real de fallo:

### Ejecución 1 (fallo simulado):

50 archivos en SFTP
Pipeline empieza a procesar...
  ✅ File 1-30 → descargados, subidos a Fabric, marcados LOADED_TO_FABRIC
  ❌ File 31 → ERROR (simulado) → marcado FAILED
  ⏭️  File 32-50 → NO procesados (quedan PENDING)

Resultado:
  - Fabric: 30 archivos
  - tracker.db: 30 LOADED_TO_FABRIC, 1 FAILED, 19 PENDING

### Ejecución 2 (retry automático):

Pipeline lee tracker.db
  ⏭️  File 1-30 → SKIP (ya LOADED_TO_FABRIC)
  🔄 File 31 → RETRY (estaba FAILED)
  🆕 File 32-50 → PROCESS (estaban PENDING)

Resultado:
  - Fabric: 50 archivos (30 viejos + 20 nuevos)
  - tracker.db: 50 LOADED_TO_FABRIC

