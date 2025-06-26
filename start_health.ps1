# start_health.ps1 - Run health data workflow in PowerShell
Write-Host "=== Starting Personal Health Data Workflow ===`n"

# Step 1: Ensure PostgreSQL is running (manual on most dev setups)
Write-Host "[1/4] (Manual) Ensure PostgreSQL is running." -ForegroundColor Yellow

# Step 2: Activate Python virtual environment
$venvPath = Join-Path $PSScriptRoot "venv\Scripts\Activate.ps1"

if (Test-Path $venvPath) {
    Write-Host "[2/4] Activating Python virtual environment..." -ForegroundColor Green
    . $venvPath
}
else {
    Write-Host "[2/4] Virtual environment not found. Creating one..." -ForegroundColor Yellow
    python -m venv venv
    if (Test-Path $venvPath) {
        . $venvPath
    }
    else {
        Write-Error "❌ Failed to create virtual environment. Exiting."
        exit 1
    }
}

# Step 3: Install required Python packages
Write-Host "[3/4] Installing Python packages from requirements.txt..." -ForegroundColor Green
pip install -r requirements.txt

# Step 4: Run the ingestion pipeline
Write-Host "[4/4] Running data ingestion script..." -ForegroundColor Green
python .\ingest_data.py --all

# Done
Write-Host "`n🎉 Done! Data ingestion completed." -ForegroundColor Cyan
