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
    $DockerAvailable = $false
}
else {
    Write-Host "[*] Checking Docker status..." -ForegroundColor Green
    try {
        $null = docker info 2>$null
        $DockerAvailable = ($LASTEXITCODE -eq 0)
    }
    catch {
        $DockerAvailable = $false
    }
    
    if (!$DockerAvailable) {
        Write-Host "[!] Docker is not running. Attempting to start Docker Desktop..." -ForegroundColor Yellow
        # Common installation paths for Docker Desktop
        $DockerPaths = @(
            "C:\Program Files\Docker\Docker\Docker Desktop.exe",
            "${env:ProgramFiles}\Docker\Docker\Docker Desktop.exe"
        )
        
        $FoundPath = $null
        foreach ($Path in $DockerPaths) {
            if (Test-Path $Path) {
                $FoundPath = $Path
                break
            }
        }

        if ($FoundPath) {
            Write-Host "[*] Launching Docker Desktop from $FoundPath..." -ForegroundColor Cyan
            Start-Process $FoundPath
            Write-Host "[*] Waiting for Docker to initialize (up to 90s)..." -ForegroundColor Cyan
            
            $Timeout = 90
            $Elapsed = 0
            while ($Elapsed -lt $Timeout) {
                Start-Sleep -Seconds 5
                $Elapsed += 5
                try {
                    $null = docker info 2>$null
                    if ($LASTEXITCODE -eq 0) {
                        $DockerAvailable = $true
                        Write-Host "[+] Docker is now ready!" -ForegroundColor Green
                        break
                    }
                }
                catch {}
                Write-Host "    ...still initializing ($Elapsed/$Timeout s)" -ForegroundColor Gray
            }
            
            if (!$DockerAvailable) {
                Write-Host "[!] Docker timed out. Please ensure it is running and has WSL2 or Hyper-V enabled." -ForegroundColor Red
            }
        }
        else {
            Write-Host "[!] Could not locate Docker Desktop executable in common paths." -ForegroundColor Red
            Write-Host "    Common locations searched: $DockerPaths" -ForegroundColor Gray
            Write-Host "    [TIP] If you use a different Redis service, the system will still attempt to connect to it at localhost:6379." -ForegroundColor Gray
        }
    }
}

# Check for Python
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "[!] Error: Python not found. Cannot start Brain or API." -ForegroundColor Red
    exit 1
}

# --- 2.5 Dependency Check ---
Write-Host "[*] Checking Python dependencies..." -ForegroundColor Green
$RequirementsFile = Join-Path $ProjectRoot "requirements.txt"
if (Test-Path $RequirementsFile) {
    # Check for redis as a proxy for all dependencies
    $OldPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue" # Don't stop on native command failure
    
    python -c "import redis, fastapi, uvicorn" 2>$null
    $CheckCode = $LASTEXITCODE
    
    if ($CheckCode -ne 0) {
        Write-Host "[!] Missing dependencies detected. Attempting to install..." -ForegroundColor Yellow
        python -m pip install -r $RequirementsFile
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[!] Warning: Dependency installation failed. System may not run correctly." -ForegroundColor Red
        }
        else {
            Write-Host "[+] Dependencies installed successfully." -ForegroundColor Green
        }
    }
    else {
        Write-Host "[+] All Python dependencies are present." -ForegroundColor Green
    }
    
    $ErrorActionPreference = $OldPreference
}



# --- 3. Start Infrastructure (Redis) ---
Write-Host "[*] Initializing Infrastructure (Redis)..." -ForegroundColor Green
if ($DockerAvailable -and (Test-Path "docker-compose.yml")) {
    try {
        docker-compose up -d redis
        Write-Host "[+] Redis is warming up..." -ForegroundColor Blue
        Start-Sleep -Seconds 2
    }
    catch {
        Write-Host "[!] Failed to start Redis via Docker. Attempting to proceed assuming local Redis..." -ForegroundColor Yellow
    }
}
else {
    Write-Host "[*] Skipping Docker-based Redis startup. Assuming local Redis is available." -ForegroundColor Gray
}

# --- 4. Launch System Components ---

# A. Start The Brain (Orchestration Layer)
Write-Host "[*] Launching Orchestration Layer (The Brain)..." -ForegroundColor Green
Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", "cd '$ProjectRoot'; python orchestration_layer/main.py" -WindowStyle Normal

# B. Start The API Layer
Write-Host "[*] Launching API Layer (FastAPI)..." -ForegroundColor Green
Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", "cd '$ProjectRoot'; python orchestration_layer/api.py" -WindowStyle Normal

# C. Start Discovery Engines (The Swarm)
Write-Host "[*] Launching Discovery Engine Swarm..." -ForegroundColor Green

# 1. Native Binary Engine
Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", "cd '$ProjectRoot'; python engines/native_binary/engine.py" -WindowStyle Normal

# 2. Web & API Engine
Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", "cd '$ProjectRoot'; python engines/web_api/api_engine.py" -WindowStyle Normal

# 3. Blockchain Engine
Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", "cd '$ProjectRoot'; python engines/blockchain/blockchain_engine.py" -WindowStyle Normal

Start-Sleep -Seconds 3


# --- 5. Launch Dashboard ---
Write-Host "[*] Opening MAVDP Discovery Dashboard..." -ForegroundColor Green
$DashboardPath = Join-Path $ProjectRoot "dashboard\index.html"
if (Test-Path $DashboardPath) {
    Start-Process $DashboardPath
}
else {
    Write-Host "[!] Dashboard file not found at $DashboardPath" -ForegroundColor Red
}

Write-Host ""
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "         System successfully initialized!           " -ForegroundColor Cyan
Write-Host "   Check the new terminal windows for active logs.  " -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "Press any key to close this orchestrator window..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
