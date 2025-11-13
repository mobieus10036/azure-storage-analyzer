# Azure Storage Assessment Toolkit - Setup Script

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 78) -ForegroundColor Cyan
Write-Host "Azure Storage Assessment Toolkit - Setup" -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "Checking Python version..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.9 or higher from https://www.python.org/" -ForegroundColor Red
    exit 1
}

Write-Host "Found: $pythonVersion" -ForegroundColor Green

# Check if version is 3.9+
$versionMatch = $pythonVersion -match "Python (\d+)\.(\d+)"
if ($versionMatch) {
    $major = [int]$Matches[1]
    $minor = [int]$Matches[2]
    
    if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 9)) {
        Write-Host "ERROR: Python 3.9 or higher is required" -ForegroundColor Red
        Write-Host "Current version: $pythonVersion" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""

# Check Azure CLI
Write-Host "Checking Azure CLI..." -ForegroundColor Yellow
$azVersion = az version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "WARNING: Azure CLI is not installed" -ForegroundColor Yellow
    Write-Host "You can install it from: https://docs.microsoft.com/cli/azure/install-azure-cli" -ForegroundColor Yellow
    Write-Host "Or use other authentication methods (service principal, managed identity)" -ForegroundColor Yellow
} else {
    Write-Host "Azure CLI is installed" -ForegroundColor Green
}

Write-Host ""

# Create virtual environment
Write-Host "Creating virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "Virtual environment already exists, skipping creation" -ForegroundColor Yellow
} else {
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
    Write-Host "Virtual environment created successfully" -ForegroundColor Green
}

Write-Host ""

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

Write-Host ""

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet

Write-Host ""

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
    exit 1
}

Write-Host "Dependencies installed successfully" -ForegroundColor Green

Write-Host ""

# Check if config.yaml exists
if (-not (Test-Path "config.yaml")) {
    Write-Host "NOTE: config.yaml not found, using default configuration" -ForegroundColor Yellow
}

Write-Host ""
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Authenticate with Azure: az login" -ForegroundColor White
Write-Host "2. Run assessment: python assess_storage.py" -ForegroundColor White
Write-Host "3. Check reports in ./reports directory" -ForegroundColor White
Write-Host ""
Write-Host "For help: python assess_storage.py --help" -ForegroundColor White
Write-Host "Documentation: docs/QUICKSTART.md" -ForegroundColor White
Write-Host ""
