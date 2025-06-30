# Health_data

## Personal Health Data Analytics: From Raw Data to Actionable Insights

### TL;DR
This repository provides the Python and PostgreSQL tooling to transform raw health data exports (Apple Health, Lose It!, smart scales, glucose meters) into a structured, queryable database. The goal is to enable deep analysis, data-driven habit change, and generate doctor-friendly reports by answering key questions:

*   **What insights can I gain from the current data?**
*   **What insights does the data suggest?**
*   **What additional data is needed to create additional likely insights?**
*   **What data was collected that can be removed, and not collected in the future?**

### 1. Project Purpose

Sitting in the chair listening to my doctor ask me questions about the glucose tests he had prescribed months earlier highlighted the separation I faced—he couldn’t see the readings I’d been dutifully logging, and I didn’t yet know how to make sense of them myself. That moment sparked this project: a mission to learn full-stack data analytics by turning scattered health metrics into a coherent story that both I—and, eventually, my doctor—can act on.

**Learning Objectives:** PostgreSQL · SQL · Python ETL · EDA · basic statistics · data-driven habit change.
**Healthcare Objectives:** Correlate meals versus glucose response, track trends, and present clear summaries at checkups.

### 2. Architecture Overview

```
┌────────────┐              ┌─────────────┐              ┌──────────────┐              ┌───────────────┐
│Raw Exports │     ───▶     │ETL (Scripts)│     ───▶     │PostgreSQL DB │     ───▶     │Analysis & Viz │
└────────────┘              └─────────────┘              └──────────────┘              └───────────────┘
      ▲                           │                              │                              │
      └─ Apple Health .zip        │                              │                              │
      └─ Lose It! .csv            └─ `create_health_database.py`  └─ `execute_sql.py`            └─ `analyze.py`
      └─ Smartscale .csv          └─ `convert_apple_health.py`  └─ `get_table_schema.py`      └─ `export_for_doctor.py`
      └─ Glucose .csv             └─ `ingest_loseit.py`         └─ `list_db_tables.py`
                                  └─ `ingest_glucose_data.py`
                                  └─ `scale_ingest.py`
                                  └─ SQL Normalization Scripts
```

Each ETL script converts a vendor-specific export into tidy, deduplicated rows, then loads them with `ON CONFLICT DO NOTHING` so reruns are idempotent. Normalization scripts further refine the database structure for improved integrity and query performance.

### 3. Repo Layout

```
health_data/
├─ apple_health_excel/       # Apple Health data processing (legacy/alternative)
├─ Brief Apple health data plan # High-level plan
├─ check_table_counts.py     # Utility to check table row counts
├─ convert_apple_health.py   # Apple Health ingestion script
├─ create_health_database.py # Database schema creation script
├─ ingest_data.py            # General data ingestion utility
├─ ingest_glucose_data.py    # Glucose data ingestion script
├─ ingest_loseit.py          # Lose It! data ingestion script
├─ scale_ingest.py           # Smart scale data ingestion script
├─ start_health.ps1          # PowerShell script for Windows quick start
├─ .env.example              # Example environment variables (NEVER commit real creds)
├─ requirements.txt          # Locked Python package versions
├─ __pycache__/              # Python cache (ignored by git)
├─ .git/                     # Git repository data (ignored by git)
├─ .idea/                    # IDE configuration (ignored by git)
├─ documents/                # Whitepapers, design notes, user documentation
│  ├─ Personal Health Project Workflow.txt
│  ├─ research health data analytics.txt
│  └─ user documentation.txt
├─ venv/                     # Python virtual environment (ignored by git)
├─ README.md                 # ← you are here
├─ list_db_tables.py         # Utility to list database tables
├─ get_table_schema.py       # Utility to get table schema
├─ execute_sql.py            # Utility to execute SQL files
├─ *.sql                     # SQL normalization scripts
```

### 4. Quick Start

**Clone & Set Up:**
```bash
$ git clone https://github.com/<yourhandle>/Health_data.git
$ cd Health_data
$ python -m venv venv && source venv/bin/activate
$ pip install -r requirements.txt
```

**Configure DB Credentials:**
```bash
$ cp .env.example .env   # then edit with your actual credentials and file paths
```

**Windows Quick Start (PowerShell):**
For a one-click setup and data ingestion on Windows, use `start_health.ps1`. Ensure your `.env` is configured.
```powershell
.\start_health.ps1
```

**Manual Setup & Ingestion:**
1.  **Create Tables:**
    ```bash
    $ python create_health_database.py
    ```
2.  **Ingest Latest Data:**
    ```bash
    $ python convert_apple_health.py
    $ python ingest_loseit.py
    $ python ingest_glucose_data.py
    $ python scale_ingest.py
    ```
3.  **Normalize Tables (Optional, but Recommended):**
    Run the SQL normalization scripts using `execute_sql.py` in the order they were created (e.g., `create_meal_types_table.sql`, `populate_meal_types.sql`, etc.).

### 5. Detailed Setup

#### 5.1 Prerequisites
*   Python 3.8+
*   PostgreSQL 15+ running locally or reachable via network
*   Optional dev tools: DBeaver (GUI for database interaction), VSCode SQL Tools.

#### 5.2 Database
```sql
CREATE USER health_user WITH PASSWORD 'your_secure_password';
CREATE DATABASE health_data OWNER health_user;
```
Then grant remote access if you analyze from a Windows desktop (see `documents/user documentation.txt` for more details).

#### 5.3 Environment Variables (.env)
```
DB_HOST=localhost
DB_NAME=health_data
DB_USER=health_user
DB_PASSWORD=your_secure_password
APPLE_HEALTH_ZIP_PATH=/path/to/your/HealthExport.zip
LOSEIT_CSV_PATH=/path/to/your/loseit_export.csv
BLOODSUGAR_CSV_PATH=/path/to/your/bloodsugar_export.csv
SCALE_CSV_PATH=/path/to/your/scale_export.csv
```
The scripts read these with `python-dotenv`.

### 6. ETL Workflows

| Script                      | Source                               | Destination Table(s)                               | Natural Unique Key (Example)        |
| :-------------------------- | :----------------------------------- | :------------------------------------------------- | :---------------------------------- |
| `convert_apple_health.py`   | `export.xml` inside Apple Health zip | `health_records`, `health_category_records`, `workouts` | `(type, start_date, end_date, value)` |
| `ingest_loseit.py`          | Lose It! CSV                         | `food_log`                                         | `(log_date, meal_type, food_item)`  |
| `scale_ingest.py`           | Smartscale CSV                       | `body_measurements`                                | `(measurement_date, source)`        |
| `ingest_glucose_data.py`    | Glucose meter CSV                    | `blood_glucose_meter`                              | `(reading_time, source, glucose_value)` |

All tables enforce these keys with `UNIQUE (...) + ON CONFLICT DO NOTHING` so daily re-exports are safe.

### 7. Normalization & Data Integrity

This project emphasizes database normalization to reduce redundancy and improve data integrity. Key steps include:

*   **Creating Lookup Tables:** For categorical data (e.g., `meal_types`, `reading_contexts`, `meal_relations`), separate tables are created to store unique values, referenced by foreign keys in the main data tables.
*   **Separating Entities:** Distinct entities like `food_items` are moved to their own tables.
*   **Consistent Timestamps:** All timestamps are stored in UTC using PostgreSQL's `TIMESTAMP WITH TIME ZONE` to ensure accurate time-series analysis.

Utility scripts like `execute_sql.py`, `list_db_tables.py`, and `get_table_schema.py` facilitate database management and schema inspection during normalization.

### 8. Incremental Updates

*   Export new data from each device/app (ideally every 15 days).
*   Place new export files in the configured data paths.
*   Run the matching ETL script — duplicates are skipped automatically due to `ON CONFLICT DO NOTHING`.

### 9. Analysis & Reporting

Analyses live in notebooks/ or `analyze.py` and pull data via `pandas.read_sql()`. Preferred plots: `matplotlib`; saved as PNG then embedded in an Excel summary generated by `export_for_doctor.py`.

**Key Insights & Analysis Types:**
*   **Postprandial Glucose Spikes:** Identify when and why blood glucose spikes after meals.
*   **Problematic Foods/Meals:** Pinpoint specific foods causing disproportionate glucose elevations.
*   **Effectiveness of Post-Meal Exercise:** Analyze the impact of activity on glucose levels.
*   **Basal vs. Bolus Imbalances:** For insulin users, understand if highs/lows relate to background insulin needs or mealtime dosing.
*   **Hypoglycemia Patterns:** Recognize patterns in low blood sugar events for safety.
*   **Glucose Variability & Stability:** Understand swings between highs and lows.
*   **Time-in-Range (TIR) Shortfalls:** Identify periods where glucose is outside target range.
*   **Correlations:** Explore relationships between sleep, stress, physical activity, weight, and glucose.

### 10. Security & Privacy

*   `.gitignore` prevents committing raw exports or `.env` files.
*   Use least privilege DB credentials.
*   At-rest encryption (disk or `pgcrypto`) is recommended for the server.

### 11. Roadmap

**Planned Tasks:**
*   📦 Wrap ETL scripts in a single CLI entry-point (`healthetl ingest AppleExport.zip`)
*   🧪 Add `pytest` suite that checks row counts & key constraints after each ingest
*   📊 Build `export_for_doctor.py` that generates an Excel/PDF summary
*   🌐 Publish a private Streamlit dashboard for real-time trends

**Retrospective Highlights:**
*   Excel choked on scale. A single Apple Health export ballooned to > 3 million rows and ~30s open times; sheet names also broke because of long `HKQuantityTypeIdentifier` prefixes.
*   PostgreSQL handled 3.1M rows effortlessly. Spinning up the first schema confirmed that moving to a database was the right call.
*   *Take-away:* move raw data to a database, keep Excel only for summaries.

### 12. Contribution Guidelines

*   Fork → feature branch → PR.
*   Conventional Commit messages (`feat:`, `fix:`, etc.).
*   Run `black` + `ruff` before pushing.

### 13. License

MIT (placeholder)

### 14. Acknowledgements

*   Apple, Lose It!, and all device vendors for export APIs
*   OpenAI ChatGPT for pair programming
*   Everyone in the diabetes datanerd community 🙌

### Personal Journey (work in progress)

A running diary of key milestones & lessons learned. Add yours here!

| Date       | Milestone                          | Reflection                                  |
| :--------- | :--------------------------------- | :------------------------------------------ |
| 20250521   | First Apple Health ingest to Excel | Realised flat files won’t scale.            |
| 20250601   | PostgreSQL schema online           | Unique keys are lifesavers.                 |
| 2025-06-06 | Started Github repo                | Had too many script versions                |
| ...        | ...                                | ...                                         |