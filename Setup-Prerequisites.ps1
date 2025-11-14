#Requires -Version 7.0
#Requires -RunAsAdministrator

<#
.SYNOPSIS
    Setup script for Azure Storage Best Practices Analyzer prerequisites

.DESCRIPTION
    Checks and installs all required PowerShell modules and dependencies for running
    the Azure Storage Assessment tool. This script ensures:
    - PowerShell 7+ is installed
    - Required Azure PowerShell modules are installed
    - PDF generation dependencies are available
    - Proper permissions are configured

.EXAMPLE
    .\Setup-Prerequisites.ps1
    Run the setup with default settings

.EXAMPLE
    .\Setup-Prerequisites.ps1 -Force
    Force reinstall all modules even if they exist

.NOTES
    Author: Azure Storage Best Practices Analyzer
    Repository: https://github.com/mobieus10036/azure-storage-analyzer
    Version: 2.0.0
    Requires: PowerShell 7+, Administrator privileges
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [switch]$Force,
    
    [Parameter(Mandatory = $false)]
    [switch]$SkipAzureModules,
    
    [Parameter(Mandatory = $false)]
    [switch]$Quiet
)

# Script configuration
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

#region Helper Functions

function Write-SetupMessage {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message,
        
        [Parameter(Mandatory = $false)]
        [ValidateSet('Info', 'Success', 'Warning', 'Error', 'Header')]
        [string]$Type = 'Info'
    )
    
    if ($Quiet) { return }
    
    switch ($Type) {
        'Header' {
            Write-Host "`n$Message" -ForegroundColor Cyan
            Write-Host ("=" * $Message.Length) -ForegroundColor Cyan
        }
        'Success' {
            Write-Host "✓ $Message" -ForegroundColor Green
        }
        'Warning' {
            Write-Host "⚠ $Message" -ForegroundColor Yellow
        }
        'Error' {
            Write-Host "✗ $Message" -ForegroundColor Red
        }
        'Info' {
            Write-Host "  $Message" -ForegroundColor Gray
        }
    }
}

function Test-AdminPrivileges {
    $currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    return $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Test-PowerShellVersion {
    $requiredVersion = [Version]"7.0"
    $currentVersion = $PSVersionTable.PSVersion
    
    if ($currentVersion -ge $requiredVersion) {
        Write-SetupMessage "PowerShell version: $currentVersion" -Type Success
        return $true
    }
    else {
        Write-SetupMessage "PowerShell version $currentVersion is below required version $requiredVersion" -Type Error
        Write-SetupMessage "Download PowerShell 7+: https://aka.ms/powershell" -Type Warning
        return $false
    }
}

function Install-RequiredModule {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$ModuleName,
        
        [Parameter(Mandatory = $false)]
        [string]$MinimumVersion,
        
        [Parameter(Mandatory = $false)]
        [switch]$Force
    )
    
    Write-SetupMessage "Checking module: $ModuleName" -Type Info
    
    $module = Get-Module -ListAvailable -Name $ModuleName | Sort-Object Version -Descending | Select-Object -First 1
    
    if ($module -and -not $Force) {
        if ($MinimumVersion) {
            if ($module.Version -ge [Version]$MinimumVersion) {
                Write-SetupMessage "$ModuleName $($module.Version) is installed" -Type Success
                return $true
            }
            else {
                Write-SetupMessage "$ModuleName $($module.Version) is below minimum version $MinimumVersion" -Type Warning
                # Continue to update
            }
        }
        else {
            Write-SetupMessage "$ModuleName $($module.Version) is installed" -Type Success
            return $true
        }
    }
    
    try {
        Write-SetupMessage "Installing $ModuleName..." -Type Info
        
        if ($Force -and $module) {
            Update-Module -Name $ModuleName -Force -ErrorAction Stop
            Write-SetupMessage "$ModuleName updated successfully" -Type Success
        }
        else {
            Install-Module -Name $ModuleName -Scope CurrentUser -Force -AllowClobber -SkipPublisherCheck -ErrorAction Stop
            Write-SetupMessage "$ModuleName installed successfully" -Type Success
        }
        
        return $true
    }
    catch {
        Write-SetupMessage "Failed to install $ModuleName: $_" -Type Error
        return $false
    }
}

function Test-InternetConnection {
    try {
        $null = Test-Connection -ComputerName "www.powershellgallery.com" -Count 1 -Quiet -ErrorAction Stop
        Write-SetupMessage "Internet connection verified" -Type Success
        return $true
    }
    catch {
        Write-SetupMessage "No internet connection detected" -Type Error
        return $false
    }
}

function Install-PDFDependencies {
    Write-SetupMessage "Checking PDF generation dependencies..." -Type Info
    
    # Check for PSWriteHTML module (for HTML to PDF conversion support)
    $pdfModules = @(
        @{ Name = "PSWriteHTML"; MinVersion = "1.0" }
    )
    
    $allInstalled = $true
    foreach ($module in $pdfModules) {
        if (-not (Install-RequiredModule -ModuleName $module.Name -MinimumVersion $module.MinVersion -Force:$Force)) {
            $allInstalled = $false
        }
    }
    
    if ($allInstalled) {
        Write-SetupMessage "PDF dependencies are ready" -Type Success
    }
    else {
        Write-SetupMessage "Some PDF dependencies could not be installed" -Type Warning
        Write-SetupMessage "PDF reports may not be available" -Type Warning
    }
    
    return $allInstalled
}

#endregion

#region Main Setup Logic

try {
    # Display header
    Write-Host "`n╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║  Azure Storage Best Practices Analyzer - Setup                ║" -ForegroundColor Cyan
    Write-Host "║  Prerequisites Installation                                    ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan
    
    # Check PowerShell version
    Write-SetupMessage "CHECKING PREREQUISITES" -Type Header
    
    if (-not (Test-PowerShellVersion)) {
        throw "PowerShell 7 or higher is required"
    }
    
    # Check admin privileges (not required but recommended)
    if (-not (Test-AdminPrivileges)) {
        Write-SetupMessage "Running without administrator privileges" -Type Warning
        Write-SetupMessage "Modules will be installed for current user only" -Type Info
    }
    else {
        Write-SetupMessage "Running with administrator privileges" -Type Success
    }
    
    # Check internet connection
    if (-not (Test-InternetConnection)) {
        throw "Internet connection is required to download modules"
    }
    
    # Install Azure PowerShell modules
    if (-not $SkipAzureModules) {
        Write-Host ""
        Write-SetupMessage "INSTALLING AZURE MODULES" -Type Header
        
        $azureModules = @(
            @{ Name = "Az.Accounts"; MinVersion = "2.0.0" }
            @{ Name = "Az.Storage"; MinVersion = "5.0.0" }
            @{ Name = "Az.Resources"; MinVersion = "6.0.0" }
            @{ Name = "Az.Monitor"; MinVersion = "4.0.0" }
            @{ Name = "Az.Security"; MinVersion = "1.0.0" }
        )
        
        $failedModules = @()
        foreach ($module in $azureModules) {
            if (-not (Install-RequiredModule -ModuleName $module.Name -MinimumVersion $module.MinVersion -Force:$Force)) {
                $failedModules += $module.Name
            }
        }
        
        if ($failedModules.Count -gt 0) {
            throw "Failed to install required Azure modules: $($failedModules -join ', ')"
        }
    }
    
    # Install PDF generation dependencies
    Write-Host ""
    Write-SetupMessage "INSTALLING PDF GENERATION MODULES" -Type Header
    Install-PDFDependencies | Out-Null
    
    # Install additional helpful modules
    Write-Host ""
    Write-SetupMessage "INSTALLING OPTIONAL MODULES" -Type Header
    
    $optionalModules = @(
        @{ Name = "ImportExcel"; MinVersion = "7.0" }
        @{ Name = "PSWriteColor"; MinVersion = "1.0" }
    )
    
    foreach ($module in $optionalModules) {
        Install-RequiredModule -ModuleName $module.Name -MinimumVersion $module.MinVersion -Force:$Force | Out-Null
    }
    
    # Verify installation
    Write-Host ""
    Write-SetupMessage "VERIFYING INSTALLATION" -Type Header
    
    $requiredModules = @('Az.Accounts', 'Az.Storage', 'Az.Resources', 'Az.Monitor')
    $allVerified = $true
    
    foreach ($moduleName in $requiredModules) {
        $module = Get-Module -ListAvailable -Name $moduleName | Select-Object -First 1
        if ($module) {
            Write-SetupMessage "$moduleName $($module.Version)" -Type Success
        }
        else {
            Write-SetupMessage "$moduleName not found" -Type Error
            $allVerified = $false
        }
    }
    
    if (-not $allVerified) {
        throw "Installation verification failed"
    }
    
    # Create output directory
    $reportsDir = Join-Path $PSScriptRoot "reports"
    if (-not (Test-Path $reportsDir)) {
        New-Item -Path $reportsDir -ItemType Directory -Force | Out-Null
        Write-SetupMessage "Created reports directory: $reportsDir" -Type Success
    }
    
    # Success summary
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║  Setup Complete!                                              ║" -ForegroundColor Green
    Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Connect to Azure: " -ForegroundColor Gray -NoNewline
    Write-Host "Connect-AzAccount" -ForegroundColor White
    Write-Host "  2. Run assessment: " -ForegroundColor Gray -NoNewline
    Write-Host ".\Invoke-StorageAssessment.ps1" -ForegroundColor White
    Write-Host ""
    
    exit 0
}
catch {
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Red
    Write-Host "║  Setup Failed                                                 ║" -ForegroundColor Red
    Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Red
    Write-Host ""
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "  • Ensure PowerShell 7+ is installed: https://aka.ms/powershell" -ForegroundColor Gray
    Write-Host "  • Check internet connectivity" -ForegroundColor Gray
    Write-Host "  • Try running as Administrator" -ForegroundColor Gray
    Write-Host "  • Check PowerShell Gallery access: Test-Connection www.powershellgallery.com" -ForegroundColor Gray
    Write-Host ""
    
    exit 1
}

#endregion
