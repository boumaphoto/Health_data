# Health_data
## Personal health data project readme 

## Personal Health Data Analytics 
###TL;DR This repo contains the Python + PostgreSQL tooling I’m building to turn raw exports from Apple Health, Lose It!, smartscale, and glucosemeter data into actionable insights (and doctor-friendly reports) by leveraging AI assisted data analytics that work to answer 4 questions. 


## What insights can I gain from the current data? 
## What insights does the data suggest? 
## What additional data is needed to create additional likely insights? 
## What data was collected that can be removed, and not collected in the future?

Shape 

1  Project Purpose 

Sitting in the chair listening to my doctor ask me questions about the glucose tests he had prescribed months earlier highlighted the separation I faced—he couldn’t see the readings I’d been dutifully logging, and I didn’t yet know how to make sense of them myself. That moment sparked this project: a mission to learn full-stack data analytics by turning scattered health metrics into a coherent story that both I—and, eventually, my doctor—can act on. 

* Learning objectives PostgreSQL · SQL · Python ETL · EDA · basic statistics · datadriven habit change. * Healthcare objectives correlate meals versus glucose response, track trends, and present clear summaries at checkups. 

2  Architecture Overview 

┌────────────┐              ┌─────────────┐                       ┌──────────────┐               ┌───────────────┐ 

│Raw Exports │     ───▶     │ETL (Scripts)│           ──▶         │PostgreSQL DB │       ─▶      │Analysis & Viz │ 

└────────────┘              └─────────────┘                       └──────────────┘               └───────────────┘ 

      ▲                           │                                      │                               │ 

      └─ Apple Health .zip         │                                      │                               │ 

      └─ Lose It! .csv             └─ `create_db_schema.py`               └─  notebooks /                 └─ `analysis.py` 

      └─ Smartscale .csv          └─ `convert_apple_health.py` 

      └─ Glucose .csv             └─ `import_loseit.py`, *etc.* 

Each ETL script converts a vendor-specific export into tidy, deduplicated rows, then loads them with ON CONFLICT DO NOTHING so reruns are idempotent. 

3  Repo Layout 

healthanalytics/ 

├─ scripts/                # all ETL + helper modules 

│  ├─ create_db_schema.py 

│  ├─ convert_apple_health.py 

│  ├─ import_loseit.py 

│  └─ … 

├─ docs/                   # whitepapers, design notes, ADRs 

├─ notebooks/              # Jupyter / VSCode notebooks for EDA 

├─ .env.example            # connection strings (NEVER commit real creds) 

├─ requirements.txt        # locked package versions 

├─ .gitignore              # venv/, __pycache__, data_exports/, *.zip … 

└─ README.md               # ← you are here 

4  Quick Start 

# clone & set up 

$ git clone https://github.com/<yourhandle>/healthanalytics.git 

$ cd healthanalytics 

$ python -m venv venv && source venv/bin/activate 

$ pip install -r requirements.txt 

 

# configure DB creds 

$ cp .env.example .env   # then edit 

 

# 1️⃣ create tables 

$ python scripts/create_db_schema.py 

# 2️⃣ ingest latest Apple export 

$ python scripts/convert_apple_health.py ~/Downloads/HealthExport.zip 

5  Detailed Setup 

5.1 Prerequisites 

    Python 3.11+x · pip 

    PostgreSQL 15+ running locally or reachable via network 

    Optional dev tools — DBeaver, vscodesqltools, make. 

5.2 Database 

CREATE USER health_user WITH PASSWORD '•••'; 

CREATE DATABASE health_data OWNER health_user; 

Then grant remote access if you analyse from a Windows desktop (see docs/db_setup.md). 

5.3 Environment Variables (.env) 

DB_HOST=localhost 

DB_NAME=health_data 

DB_USER=health_user 

DB_PASSWORD=••• 

The scripts read these with python-dotenv. 

6  ETL Workflows 

Script 
	

Source 
	

Destination table 
	

Natural unique key 

convert_apple_health.py 
	

export.xml inside Apple Health zip 
	

health_records, health_category_records, workouts 
	

(type, start_date, end_date, value) 

import_loseit.py 
	

Lose It! CSV 
	

food_log 
	

(log_date, meal_type, food_item) 

import_scale.py 
	

smartscale CSV 
	

body_measurements 
	

(measurement_date, source) 

import_glucose.py 
	

meter CSV 
	

blood_glucose_meter 
	

(reading_time, source, glucose_value) 

All tables enforce these keys with UNIQUE (…) + ON CONFLICT DO NOTHING so daily reexports are safe. 

7  Incremental Updates 

    Export new data from each device/app (ideally every 15 days). 

    Drop into data_exports/. 

    Run the matching ETL script — duplicates are skipped automatically. 

8  Analysis & Reporting 

Analyses live in notebooks/ or analysis.py and pull data via pandas.read_sql(). Preferred plots: matplotlib; saved as PNG then embedded in an Excel summary generated by export_for_doctor.py. 

9  Security & Privacy 

    .gitignore prevents committing raw exports or .env. 

    Use least privilege DB credentials. 

    Atrest encryption (disk or pgcrypto) is recommended for the server. 

10  Roadmap 

Planned Tasks 

    📦 Wrap ETL scripts in a single CLI entry-point (`healthetl ingest AppleExport.zip`) 

    🧪 Add pytest suite that checks row counts & key constraints after each ingest 

    📊 Build `export_for_doctor.py` that generates an Excel/PDF summary 

    🌐 Publish a private Streamlit dashboard for real-time trends 

Retrospective Highlights 

    Excel choked on scale. A single Apple Health export ballooned to > 3 million rows and ~30 s open times; sheet names also broke because of long HKQuantityTypeIdentifier… prefixes. 

    PostgreSQL handled 3.1 M rows effortlessly. Spinning up the first schema confirmed that moving to a database was the right call. 

    *Take-away:* move raw data to a database, keep Excel only for summaries.  

 

11    Contribution Guidelines 

    Fork → feature branch → PR. 

    Conventional Commit messages (feat:, fix: …). 

    Run black + ruff before pushing. 

12  License 

MIT (placeholder) 

13  Acknowledgements 

    Apple, Lose It!, and all device vendors for export APIs 

    OpenAI ChatGPT for pair programming 

    Everyone in the diabetes datanerd community 🙌 

 

Personal Journey (work in progress) 

A running diary of key milestones & lessons learned. Add yours here! 

Date                   Milestone                             Reflection 

20250521         First Apple Health ingest to Excel         Realised flat files won’t scale. 

20250601         PostgreSQL schema online                   Unique keys are lifesavers. 

2025-06-06       Started Github repo                        Had too many script versions 

…                …                                          … 

 
