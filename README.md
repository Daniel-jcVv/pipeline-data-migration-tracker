# Data Migration to Microsoft Fabric

ETL pipeline para migrar datos de SFTP a Microsoft Fabric Lakehouse.

## Estructura

```
src/
├── ingestion.py          # SFTP + file tracking
├── transformations.py    # Bronze → Silver (PySpark)
└── fabric_client.py      # Upload a Fabric

run_pipeline.py           # Orchestrator principal
config.py                 # Configuración
tests/                    # Unit tests
```

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env      # Configurar credenciales
python run_pipeline.py
```

## Arquitectura

1. **Bronze**: Download desde SFTP
2. **Silver**: Limpieza (nulls, duplicados, trim)
3. **Upload**: Parquet a Fabric Lakehouse

**Idempotencia**: SQLite tracker evita reprocesamiento.

## Tests

```bash
pytest tests/
```
