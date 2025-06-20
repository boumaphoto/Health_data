# start_health.ps1

param(
    [ValidateSet("download", "normalize", "analyze", "insight")]
    [string]$phase = "download"
)

Write-Host "🟢 Starting PostgreSQL..."
Start-Service postgresql-x64-15   # Replace with your actual PostgreSQL service name

Write-Host "🐍 Activating Python virtual environment..."
$env:VIRTUAL_ENV = "$PSScriptRoot\venv"
. "$env:VIRTUAL_ENV\Scripts\Activate.ps1"

switch ($phase) {
    "download" {
        Write-Host "📥 Phase: Download new data"
        Write-Host "   Reminder: Export Apple Health and Lose It data to /data folder"
        # Optionally: run a download or unzip helper
    }
    "normalize" {
        Write-Host "🧼 Phase: Normalize data (ETL)"
        Write-Host "   Ready to run convert_apple_health.py, ingest_lose_it.py, etc."
    }
    "analyze" {
        Write-Host "📊 Phase: Analyze data"
        Write-Host "   You can now run analyze.py or open a Jupyter Notebook"
    }
    "insight" {
        Write-Host "💡 Phase: Develop insights"
        Write-Host "   Run export_for_doctor.py or create charts and summaries"
    }
}

# Optional: launch a PowerShell session so venv remains active
powershell
