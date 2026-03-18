# MAVDP System Startup Script (PowerShell)
# This script automates the initialization of the MAVDP ecosystem.

$ErrorActionPreference = "Stop"
$ProjectRoot = Get-Location

# --- 1. Aesthetics & Header ---
Clear-Host
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "   MAVDP: Modular Autonomous Discovery Platform    " -ForegroundColor Cyan
Write-Host "            (System Startup Orchestrator)           " -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host ""

# --- 2. Prerequisite Checks ---

# Check for Docker
if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "[!] Warning: Docker not found. Redis might not start via docker-compose." -ForegroundColor Yellow
} else {
    Write-Host "[*] Checking Docker status..." -ForegroundColor Green
    $dockerInfo = docker info 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[!] Error: Docker is not running. Please start Docker Desktop." -ForegroundColor Red
        # We'll continue anyway, maybe Redis is running as a local service
    }
}

# Check for Python
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "[!] Error: Python not found. Cannot start Brain or API." -ForegroundColor Red
    exit 1
}

# --- 3. Start Infrastructure (Redis) ---
Write-Host "[*] Initializing Infrastructure (Redis)..." -ForegroundColor Green
if (Test-Path "docker-compose.yml") {
    try {
        docker-compose up -d redis
        Write-Host "[+] Redis is warming up..." -ForegroundColor Blue
        Start-Sleep -Seconds 2
    } catch {
        Write-Host "[!] Failed to start Redis via Docker. Attempting to proceed assuming local Redis..." -ForegroundColor Yellow
    }
}

# --- 4. Launch System Components ---

# A. Start The Brain (Orchestration Layer)
Write-Host "[*] Launching Orchestration Layer (The Brain)..." -ForegroundColor Green
Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", "cd '$ProjectRoot'; python orchestration_layer/main.py" -WindowStyle Normal

# B. Start The API Layer
Write-Host "[*] Launching API Layer (FastAPI)..." -ForegroundColor Green
Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", "cd '$ProjectRoot'; python orchestration_layer/api.py" -WindowStyle Normal

# C. Start Mock Engine (Telemetry Generator)
Write-Host "[*] Launching Mock Discovery Engine..." -ForegroundColor Green
Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", "cd '$ProjectRoot'; python test_engine.py" -WindowStyle Normal

Start-Sleep -Seconds 3

# --- 5. Launch Dashboard ---
Write-Host "[*] Opening MAVDP Discovery Dashboard..." -ForegroundColor Green
$DashboardPath = Join-Path $ProjectRoot "dashboard\index.html"
if (Test-Path $DashboardPath) {
    Start-Process $DashboardPath
} else {
    Write-Host "[!] Dashboard file not found at $DashboardPath" -ForegroundColor Red
}

Write-Host ""
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "         System successfully initialized!           " -ForegroundColor Cyan
Write-Host "   Check the new terminal windows for active logs.  " -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "Press any key to close this orchestrator window..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
