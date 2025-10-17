# 🔄 Data Migration Pipeline to Microsoft Fabric

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Paramiko](https://img.shields.io/badge/SFTP-Paramiko-green?logo=ssh&logoColor=white)](https://www.paramiko.org/)
[![SQLite](https://img.shields.io/badge/Database-SQLite-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Microsoft Fabric](https://img.shields.io/badge/Platform-Microsoft%20Fabric-0078D4?logo=microsoft&logoColor=white)](https://fabric.microsoft.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **ETL pipeline with idempotent file tracking system to prevent data reprocessing during migrations**

---

## 🎯 The Problem

During large-scale data migrations, pipeline failures are inevitable. When migrating 50+ CSV files from SFTP to Microsoft Fabric, a common challenge emerges:

### ❌ Without File Tracking
```
Execution 1: Processing 50 files... ❌ Fails at file #30
Execution 2: Reprocesses ALL 50 files (including 29 already migrated)
Result: Wasted time, potential duplicates, inefficient resource usage
```
---

## 💡 Solution Architecture

This project implements an **idempotent ETL pipeline** using a SQLite-based file tracker that maintains state across executions.

### Visual Flow

#### Before: Traditional Migration (Inefficient)
```
┌─────────────────────────────────────────────────────┐
│  SFTP Source: 50 CSV Files                          │
│  ├─ orders_001.csv  ├─ orders_026.csv               │
│  ├─ orders_002.csv  ├─ orders_027.csv               │
│  ├─ ...             ├─ ...                          │
│  └─ orders_025.csv  └─ orders_050.csv               │
└────────────┬────────────────────────────────────────┘
             │
             │ Pipeline Execution #1
             ▼
    ┌────────────────────┐
    │ Processing...      │
    │ ✓ File 1-25       │
    │ ✓ File 26-29      │
    │ ❌ FAILURE at 30   │
    └────────────────────┘
             │
             │ Pipeline Execution #2 (RE-RUN)
             ▼
    ┌────────────────────┐
    │ ⚠️  Reprocesses    │
    │    ALL 50 files!   │
    │                    │
    │ ❌ Duplicates      │
    │ ❌ Wasted time     │
    └────────────────────┘
```


### ✅ With Intelligent File Tracking
```
Execution 1: Processing 50 files... ❌ Fails at file #30
Execution 2: Skips 29 processed files, continues from #30
Result: Zero reprocessing, guaranteed idempotency, optimized pipeline
```


#### After: Smart Migration (Optimized)
```
┌─────────────────────────────────────────────────────┐
│  SFTP Source: 50 CSV Files                          │
└────────────┬────────────────────────────────────────┘
             │
             │ Step 1: List all files
             ▼
    ┌────────────────────┐
    │ Get Metadata       │  → [files 1-50]
    └────────┬───────────┘
             │
             │ Step 2: Check tracker
             ▼
    ┌────────────────────┐      ┌──────────────────┐
    │ Query file_tracker │ ←──→ │ SQLite Database  │
    │ Status: LOADED     │      │ ┌──────────────┐ │
    └────────┬───────────┘      │ │ files 1-29   │ │
             │                  │ │ Status: OK   │ │
             │                  │ └──────────────┘ │
             │                  └──────────────────┘
             │ Step 3: Filter processed
             ▼
    ┌────────────────────┐
    │ Smart Filter       │
    │ Already done: 29   │
    │ To process: 21     │  ✅ ONLY NEW FILES
    └────────┬───────────┘
             │
             │ Step 4: Process remaining
             ▼
    ┌────────────────────┐
    │ FOR EACH file:     │
    │ 1. Download        │
    │ 2. Load to Fabric  │
    │ 3. Mark processed  │
    └────────────────────┘
             │
             ▼
    ┌────────────────────┐
    │ ✅ Success         │
    │ No duplicates      │
    │ Time optimized     │
    └────────────────────┘
```

---

## 📊 Key Metrics & Results

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Files Reprocessed on Failure** | 50 (100%) | 0 (0%) | ✅ 100% reduction |
| **Pipeline Idempotency** | ❌ No | ✅ Yes | Guaranteed |
| **Average Recovery Time** | ~45 min | ~5 min | ⚡ 90% faster |
| **Duplicate Risk** | High | Zero | 🛡️ Eliminated |
| **Manual Intervention** | Required | None | 🤖 Automated |

---

## 🏗️ Technical Stack

### Core Technologies
- **Python 3.8+**: Main orchestration language
- **Paramiko**: SFTP client for secure file transfer
- **SQLite**: Lightweight database for state management
- **Microsoft Fabric**: Cloud data platform (Lakehouse + Warehouse)

### Architecture Pattern
- **Idempotent Design**: Safe to re-execute multiple times
- **State Management**: Persistent tracking with SQLite

---

## 📁 Project Structure

```
fabric-data-migration/
├── src/
│   ├── ingestion.py          # SFTP download
│   ├── fabric_client.py      # Upload to Fabric
│   └── file_tracker.py       # State management
├── scripts/
│   └── demo_idempotency.py   # Demo only
├── data/
│   ├── staging/              # Downloaded CSVs
│   └── tracker.db            # SQLite state
├── run_pipeline.py
├── config.py
├── requirements.txt
├── README.md
└── .env.example
```


## 🔄 PIPELINE FLOW - Update Data Flow
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ┌─────────────────┐
  │   Data Source   │  SFTP externo (fuera del proyecto)
  │   (50+ files)   │  Usuario: fabric / Path: data/raw/
  └────────┬────────┘
           │
  ┌────────▼────────┐
  │  Get Metadata   │  📄 src/ingestion.py
  │   (Reader)      │  → sftp.listdir() → 50 files
  └────────┬────────┘
           │
  ┌────────▼────────┐
  │     Lookup      │  📄 src/utils/file_tracker.py
  │   (Tracker)     │  → tracker.get_pending_files()
  │                 │  💾 data/metadata/file_tracker.db
  └────────┬────────┘  → 20 already MEDALLION_COMPLETE
           │
  ┌────────▼────────┐
  │     Filter      │  📄 src/utils/file_tracker.py (interno)
  │   (Filter)      │  → Retorna solo PENDING
  └────────┬────────┘  → 30 to process
           │
  ┌────────▼────────┐
  │    ForEach      │  📄 run_pipeline.py
  │  ┌──────────┐   │  
  │  │ Download │   │  → 📁 data/bronze/ (staging local)
  │  │ Upload   │   │  → 📄 src/fabric_client.py
  │  │ Track    │   │  → ☁️ Fabric: Files/migration/bronze/
  │  └──────────┘   │  → 💾 Update tracker
  └─────────────────┘




---

## 🚀 Quick Start

### Prerequisites
```bash
# Python 3.8 or higher
python --version

# Install dependencies
pip install -r requirements.txt
```

### Configuration
Create a `.env` file in the project root:
```bash
# SFTP Configuration
SFTP_HOST=your-sftp-server.com
SFTP_PORT=22
SFTP_USERNAME=your_username
SFTP_PASSWORD=your_pass
SFTP_REMOTE_PATH=/data/your_path/...

# Destination
LAKEHOUSE_PATH=data/lakehouse/bronze/

# Tracker Database
TRACKER_DB_PATH=data/file_tracker.db
```

### Execution

#### 1. Dry Run (Preview Mode)
Test the pipeline without downloading files:
```bash
python run_migration.py --dry-run
```

**Output:**
```
==================================================================
  DATA MIGRATION PIPELINE
==================================================================

STEP 1: Connecting to SFTP server...
✓ Connected to SFTP: your-server.com

STEP 2: Listing files on server...
✓ Found 50 CSV files

STEP 3: Checking already processed files...
  Already processed: 29 files

STEP 4: Filtering pending files...
📊 Summary:
   Total files: 50
   Already processed: 29
   To process: 21

DRY-RUN: Stopping here. No files were downloaded.
```

#### 2. Production Run
Execute the complete migration:
```bash
python run_migration.py
```

#### 3. Verify Idempotency
Run again to confirm no reprocessing:
```bash
python run_migration.py

# Output:
# All files are already processed!
# Nothing new to migrate.
```

---

## 🔧 Core Components

### 1. SFTP Connector (`sftp_connector.py`)

Handles secure file transfer operations with clean, functional programming:

```python
# Simple API design
sftp = connect_to_sftp(host, username, password)
files = list_csv_files(sftp, '/data/csv/')
download_file(sftp, remote_path, local_path)
close_connection(sftp)
```

**Key Features:**
- Automatic retry logic
- Connection pooling ready
- Error handling with context
- Secure credential management

### 2. File Tracker (`file_tracker_sv.py`)

State management system preventing reprocessing:

```python
# Initialize tracker
conn = init_tracker('data/file_tracker.db')

# Check processing status
if is_file_processed(conn, 'orders.csv'):
    print("Skipping: already migrated")
    
# Mark as completed
mark_as_processed(conn, 'orders.csv', status='LOADED')
```

**Database Schema:**
```sql
CREATE TABLE file_tracker (
    filename TEXT PRIMARY KEY,
    load_date TEXT NOT NULL,
    status TEXT NOT NULL,        -- LOADED, FAILED, PROCESSING
    file_size INTEGER,
    record_count INTEGER
);
```

### 3. Pipeline Orchestrator (`run_migration.py`)

Main execution flow with comprehensive logging:

```python
def run_migration_pipeline(config, dry_run=False):
    # 1. Connect to SFTP
    sftp = connect_to_sftp(...)
    
    # 2. List all files
    all_files = list_csv_files(sftp, path)
    
    # 3. Query processed files
    processed = get_processed_files(tracker_conn)
    
    # 4. Filter unprocessed
    to_process = filter_unprocessed_files(all_files, processed)
    
    # 5. Process each file
    for file_info in to_process:
        download_file(sftp, file_info['path'], local_path)
        load_to_warehouse(file_info)  # Fabric integration
        mark_as_processed(tracker_conn, file_info['name'])
```


---

## 🔄 Idempotency Demo

Demonstrates safe re-runs without reprocessing:

```bash
# Simulate partial failure (e.g., 32 success, 16 failed)
python scripts/demo_idempotency.py

# Output:
# ✅ Simulated failure: 16 files marked as FAILED
# 📊 After simulation:
#   FAILED: 16
#   MEDALLION_COMPLETE: 32

# Retry only failed files
python run_pipeline.py
# ✅ Processes 16 failed, skips 32 completed

# Verify no duplicates
python scripts/manage_tracker.py stats
# 📊 Processing Statistics:
#   MEDALLION_COMPLETE: 48
```

---


## 🎯 Key Engineering Concepts Demonstrated

### 1. Idempotency
The pipeline can be executed multiple times with identical results. The file tracker ensures that processed files are never re-ingested, making the system safe for automated retry logic.

### 2. State Management
Persistent state tracking with SQLite enables the pipeline to resume from the last successful checkpoint, reducing recovery time from minutes to seconds.

### 3. Separation of Concerns
Each module has a single responsibility: SFTP operations, state tracking, and orchestration are completely independent and testable.

### 4. Enterprise Patterns
- **Retry Logic**: Automatic recovery from transient failures
- **Logging**: Structured logging for observability
- **Configuration**: Environment-based config management
- **Error Handling**: Graceful degradation with meaningful errors


---


## 🔮 Roadmap

### Phase 1: Core Pipeline ✅ (Completed)
- [x] SFTP connector with Paramiko
- [x] File tracker with SQLite
- [x] Idempotent pipeline design
- [x] Dry-run capability

### Phase 2: Fabric Integration ✅ (Completed)
- [X] OneLake REST API integration
- [X] Direct upload to Lakehouse Files
- [X] Unit tests with pytest


### Phase 3: Advanced Features 📋 (Future)
- [ ] Parallel file processing (ThreadPoolExecutor)
- [ ] Pandera validation
- [ ] Monitoring dashboard
- [ ] Email alerts on failure
- [ ] Integration tests
- [ ] CI/CD with GitHub Actions


---

## 📚 Resources

- [Fabric Lakehouse Management](https://learn.microsoft.com/en-us/fabric/data-engineering/lakehouse-api)
- [OneLake Access API](https://learn.microsoft.com/en-us/fabric/onelake/onelake-access-api)
- [ETL Pipeline Patterns](https://learn.microsoft.com/en-us/fabric/data-engineering/load-data-lakehouse)


---

## 👤 Author

**Daniel Garcia Belman**  
Data Engineer | Python Developer | Big Data

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0077B5?logo=linkedin&logoColor=white)](www.linkedin.com/in/daniel-garcía-belman-99a298aa)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-181717?logo=github&logoColor=white)](https://github.com/Daniel-jcVv)
[![Email](https://img.shields.io/badge/Email-Contact-D14836?logo=gmail&logoColor=white)](mailto:daniel_ys1@outlook.com)

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

**Ora et labora, ahora**
**Soli Deo gloria**
My gratitude to the open-source community for generously sharing their knowledge.


---

