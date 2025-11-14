#Requires -Version 7.0
#Requires -Modules Az.Storage, Az.Accounts, Az.Resources, Az.Monitor

<#
.SYNOPSIS
    Azure Storage Account Best Practices Assessment Tool

.DESCRIPTION
    Comprehensive PowerShell-based assessment tool for evaluating Azure Storage Accounts
    against enterprise security, governance, resiliency, and operational best practices.
    
    This all-in-one script includes:
    - Security posture assessment
    - Resiliency and DR validation  
    - Operational best practices checking
    - Data lifecycle analysis
    - Rich terminal output with colors and progress
    - PDF report generation
    
    Built for Azure Cloud Architects and Platform Engineers.
    Repository: https://github.com/mobieus10036/azure-storage-analyzer

.PARAMETER SubscriptionId
    Specific Azure subscription ID to assess

.PARAMETER ResourceGroupName
    Specific resource group to assess

.PARAMETER StorageAccountName
    Specific storage account to assess

.PARAMETER ConfigPath
    Path to configuration file. Default: .\config.json

.PARAMETER OutputPath
    Directory for assessment reports. Default: .\reports

.PARAMETER GeneratePDF
    Generate PDF report (requires PSWriteHTML module)

.PARAMETER Quick
    Run quick assessment (reduced depth, faster)

.PARAMETER Verbose
    Enable detailed logging

.EXAMPLE
    .\Invoke-StorageAssessment.ps1
    Run full assessment with default settings

.EXAMPLE
    .\Invoke-StorageAssessment.ps1 -GeneratePDF
    Run assessment and generate PDF report

.EXAMPLE
    .\Invoke-StorageAssessment.ps1 -StorageAccountName "mystorageacct" -Verbose
    Assess single storage account with detailed logging

.NOTES
    Author: Azure Storage Best Practices Analyzer
    Version: 2.0.0
    Repository: https://github.com/mobieus10036/azure-storage-analyzer
    Requires: PowerShell 7+, Az.Storage, Az.Accounts, Az.Resources, Az.Monitor modules
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$SubscriptionId,
    
    [Parameter(Mandatory = $false)]
    [string]$ResourceGroupName,
    
    [Parameter(Mandatory = $false)]
    [string]$StorageAccountName,
    
    [Parameter(Mandatory = $false)]
    [string]$ConfigPath = ".\config.json",
    
    [Parameter(Mandatory = $false)]
    [string]$OutputPath = ".\reports",
    
    [Parameter(Mandatory = $false)]
    [switch]$GeneratePDF,
    
    [Parameter(Mandatory = $false)]
    [switch]$Quick
)

#region Script Variables

$Script:StartTime = Get-Date
$Script:AssessmentId = Get-Date -Format "yyyyMMdd_HHmmss"
$Script:AssessmentResults = @{
    Metadata = @{
        AssessmentId = $Script:AssessmentId
        Timestamp = $Script:StartTime
        Version = "2.0.0"
        Repository = "https://github.com/mobieus10036/azure-storage-analyzer"
    }
    StorageAccounts = @()
    Summary = @{
        TotalAccounts = 0
        TotalFindings = 0
        CriticalFindings = 0
        HighFindings = 0
        MediumFindings = 0
        LowFindings = 0
        InfoFindings = 0
    }
}

# Severity colors
$Script:SeverityColors = @{
    Critical = 'Red'
    High = 'DarkRed'
    Medium = 'Yellow'
    Low = 'DarkYellow'
    Info = 'Gray'
}

#endregion

#region Display and Logging Functions

function Write-AssessmentHeader {
    Clear-Host
    Write-Host "`n╔══════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║                                                                  ║" -ForegroundColor Cyan
    Write-Host "║      Azure Storage Best Practices Analyzer                      ║" -ForegroundColor Cyan
    Write-Host "║      Enterprise Security, Governance & Resiliency Assessment     ║" -ForegroundColor Cyan
    Write-Host "║                                                                  ║" -ForegroundColor Cyan
    Write-Host "╚══════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan
}

function Write-Section {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Title,
        
        [Parameter(Mandatory = $false)]
        [string]$Color = 'Cyan'
    )
    
    Write-Host "`n┌─────────────────────────────────────────────────────────────┐" -ForegroundColor $Color
    Write-Host "│ $($Title.PadRight(59)) │" -ForegroundColor $Color
    Write-Host "└─────────────────────────────────────────────────────────────┘" -ForegroundColor $Color
}

function Write-Status {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message,
        
        [Parameter(Mandatory = $false)]
        [ValidateSet('Info', 'Success', 'Warning', 'Error', 'Progress')]
        [string]$Type = 'Info'
    )
    
    $icon = switch ($Type) {
        'Success' { '✓'; $color = 'Green' }
        'Warning' { '⚠'; $color = 'Yellow' }
        'Error' { '✗'; $color = 'Red' }
        'Progress' { '▶'; $color = 'Cyan' }
        default { '•'; $color = 'Gray' }
    }
    
    Write-Host "$icon $Message" -ForegroundColor $color
}

function Write-Finding {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Severity,
        
        [Parameter(Mandatory = $true)]
        [string]$Message,
        
        [Parameter(Mandatory = $false)]
        [string]$Resource = ""
    )
    
    $color = $Script:SeverityColors[$Severity]
    $severityText = "[$($Severity.ToUpper().PadRight(8))]"
    
    Write-Host "  $severityText " -ForegroundColor $color -NoNewline
    
    if ($Resource) {
        Write-Host "$Resource - " -ForegroundColor White -NoNewline
    }
    
    Write-Host $Message -ForegroundColor Gray
}

function Write-ProgressBar {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [int]$Current,
        
        [Parameter(Mandatory = $true)]
        [int]$Total,
        
        [Parameter(Mandatory = $true)]
        [string]$Activity
    )
    
    $percentComplete = [math]::Round(($Current / $Total) * 100)
    $barLength = 50
    $filledLength = [math]::Round(($percentComplete / 100) * $barLength)
    $emptyLength = $barLength - $filledLength
    
    $bar = "█" * $filledLength + "░" * $emptyLength
    
    Write-Host "`r$Activity [$bar] $percentComplete% ($Current/$Total)" -NoNewline -ForegroundColor Cyan
}

#endregion

#region Azure Connection and Context

function Initialize-AzureConnection {
    Write-Section "Azure Connection" -Color 'Cyan'
    
    try {
        $context = Get-AzContext -ErrorAction SilentlyContinue
        
        if (-not $context) {
            Write-Status "Not connected to Azure" -Type Warning
            Write-Status "Initiating Azure authentication..." -Type Progress
            Connect-AzAccount -ErrorAction Stop | Out-Null
            $context = Get-AzContext
        }
        
        Write-Status "Connected to Azure" -Type Success
        Write-Host "  Account:      $($context.Account.Id)" -ForegroundColor Gray
        Write-Host "  Subscription: $($context.Subscription.Name)" -ForegroundColor Gray
        Write-Host "  Tenant:       $($context.Tenant.Id)" -ForegroundColor Gray
        
        # Set subscription if specified
        if ($SubscriptionId -and $context.Subscription.Id -ne $SubscriptionId) {
            Write-Status "Switching to subscription: $SubscriptionId" -Type Progress
            Set-AzContext -SubscriptionId $SubscriptionId -ErrorAction Stop | Out-Null
            $context = Get-AzContext
        }
        
        $Script:AssessmentResults.Metadata.Subscription = @{
            Id = $context.Subscription.Id
            Name = $context.Subscription.Name
            TenantId = $context.Tenant.Id
        }
        
        return $context
    }
    catch {
        Write-Status "Failed to connect to Azure: $_" -Type Error
        throw
    }
}

#endregion

#region Configuration Management

function Get-AssessmentConfig {
    if (Test-Path $ConfigPath) {
        Write-Status "Loading configuration from: $ConfigPath" -Type Info
        try {
            $config = Get-Content -Path $ConfigPath -Raw | ConvertFrom-Json
            Write-Status "Configuration loaded" -Type Success
            return $config
        }
        catch {
            Write-Status "Failed to load configuration, using defaults" -Type Warning
        }
    }
    else {
        Write-Status "No configuration file found, using defaults" -Type Info
    }
    
    # Return default configuration
    return [PSCustomObject]@{
        Security = [PSCustomObject]@{
            CheckPublicAccess = $true
            CheckPrivateEndpoints = $true
            CheckDefender = $true
            CheckEncryption = $true
            CheckEncryptionKeyManagement = $true
            MinimumTLSVersion = "TLS1_2"
            CheckSharedKeyAccess = $true
            CheckNetworkRules = $true
            MinimumLogRetentionDays = 90
        }
        Resiliency = [PSCustomObject]@{
            CheckReplication = $true
            MinimumReplicationForProduction = "ZRS"
            CheckBackupPolicies = $true
            MinimumRetentionDays = 30
            CheckSoftDelete = $true
            CheckVersioning = $true
            CheckPointInTimeRestore = $true
        }
        Operational = [PSCustomObject]@{
            CheckNaming = $true
            NamingPattern = "^st[a-z0-9]{3,22}$"
            CheckTags = $true
            RequiredTags = @('Environment', 'Owner', 'DataClassification')
            CheckManagedIdentity = $true
            CheckDiagnosticSettings = $true
            CheckMonitoring = $true
        }
        Governance = [PSCustomObject]@{
            CheckRBAC = $true
            CheckResourceLocks = $true
            MaxOwnerRoleAssignments = 2
        }
        Lifecycle = [PSCustomObject]@{
            CheckLifecyclePolicies = $true
            CheckVersionHygiene = $true
            StaleDataThresholdDays = 90
        }
    }
}

#endregion

#region Storage Account Discovery

function Get-TargetStorageAccounts {
    Write-Section "Storage Account Discovery" -Color 'Cyan'
    
    try {
        $accounts = @()
        
        if ($StorageAccountName) {
            Write-Status "Searching for specific account: $StorageAccountName" -Type Progress
            
            if ($ResourceGroupName) {
                $accounts = @(Get-AzStorageAccount -ResourceGroupName $ResourceGroupName -Name $StorageAccountName -ErrorAction Stop)
            }
            else {
                $allAccounts = Get-AzStorageAccount
                $accounts = @($allAccounts | Where-Object { $_.StorageAccountName -eq $StorageAccountName })
            }
        }
        elseif ($ResourceGroupName) {
            Write-Status "Discovering accounts in resource group: $ResourceGroupName" -Type Progress
            $accounts = @(Get-AzStorageAccount -ResourceGroupName $ResourceGroupName -ErrorAction Stop)
        }
        else {
            Write-Status "Discovering all storage accounts in subscription..." -Type Progress
            $accounts = @(Get-AzStorageAccount)
        }
        
        if ($accounts.Count -eq 0) {
            Write-Status "No storage accounts found" -Type Warning
            return @()
        }
        
        Write-Status "Found $($accounts.Count) storage account(s) to assess" -Type Success
        
        foreach ($account in $accounts) {
            Write-Host "  • $($account.StorageAccountName) " -ForegroundColor Gray -NoNewline
            Write-Host "[$($account.Location)]" -ForegroundColor DarkGray -NoNewline
            Write-Host " {$($account.Sku.Name)}" -ForegroundColor DarkGray
        }
        
        return $accounts
    }
    catch {
        Write-Status "Failed to discover storage accounts: $_" -Type Error
        throw
    }
}

#endregion

#region Assessment Logic - Security

function Test-SecurityPosture {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        $StorageAccount,
        
        [Parameter(Mandatory = $true)]
        $Config
    )
    
    $findings = @()
    $secConfig = $Config.Security
    
    # Check public access
    if ($secConfig.CheckPublicAccess) {
        if ($StorageAccount.AllowBlobPublicAccess -eq $true) {
            $findings += [PSCustomObject]@{
                Category = "Security"
                Severity = "High"
                Type = "Public Access"
                Finding = "Public blob access is enabled at storage account level"
                Recommendation = "Disable public blob access unless specifically required"
                Remediation = "Set AllowBlobPublicAccess to false"
            }
        }
    }
    
    # Check HTTPS-only
    if ($StorageAccount.EnableHttpsTrafficOnly -ne $true) {
        $findings += [PSCustomObject]@{
            Category = "Security"
            Severity = "Critical"
            Type = "Encryption in Transit"
            Finding = "HTTPS-only traffic is not enforced"
            Recommendation = "Enable HTTPS-only traffic to protect data in transit"
            Remediation = "Set EnableHttpsTrafficOnly to true"
        }
    }
    
    # Check TLS version
    if ($secConfig.CheckEncryption -and $StorageAccount.MinimumTlsVersion) {
        $currentTLS = $StorageAccount.MinimumTlsVersion
        $requiredTLS = $secConfig.MinimumTLSVersion
        
        if ($currentTLS -ne $requiredTLS -and $currentTLS -notin @('TLS1_2', 'TLS1_3')) {
            $findings += [PSCustomObject]@{
                Category = "Security"
                Severity = "High"
                Type = "TLS Version"
                Finding = "Minimum TLS version is $currentTLS (should be TLS 1.2 or higher)"
                Recommendation = "Set minimum TLS version to TLS 1.2"
                Remediation = "Update MinimumTlsVersion to TLS1_2"
            }
        }
    }
    
    # Check Encryption at Rest
    if ($secConfig.CheckEncryption) {
        if ($StorageAccount.Encryption.Services.Blob.Enabled -ne $true) {
            $findings += [PSCustomObject]@{
                Category = "Security"
                Severity = "Critical"
                Type = "Encryption at Rest"
                Finding = "Blob encryption at rest is not enabled"
                Recommendation = "Enable encryption at rest for all storage services"
                Remediation = "Encryption should be enabled by default - investigate why it's disabled"
            }
        }
        
        if ($StorageAccount.Encryption.Services.File.Enabled -ne $true) {
            $findings += [PSCustomObject]@{
                Category = "Security"
                Severity = "Critical"
                Type = "Encryption at Rest"
                Finding = "File service encryption at rest is not enabled"
                Recommendation = "Enable encryption at rest for file services"
                Remediation = "Encryption should be enabled by default - investigate why it's disabled"
            }
        }
    }
    
    # Check Customer-Managed Keys (CMK)
    if ($secConfig.CheckEncryptionKeyManagement) {
        if ($StorageAccount.Encryption.KeySource -eq 'Microsoft.Storage') {
            $severity = if ($StorageAccount.Tags.DataClassification -in @('Confidential', 'Restricted')) { 'High' } else { 'Medium' }
            $findings += [PSCustomObject]@{
                Category = "Security"
                Severity = $severity
                Type = "Encryption Key Management"
                Finding = "Using Microsoft-managed keys instead of customer-managed keys"
                Recommendation = "Consider using customer-managed keys (CMK) for enhanced control and compliance"
                Remediation = "Configure CMK via Azure Key Vault for sensitive data"
            }
        }
        elseif ($StorageAccount.Encryption.KeySource -eq 'Microsoft.Keyvault') {
            # Verify key vault configuration
            if (-not $StorageAccount.Encryption.KeyVaultProperties.KeyName) {
                $findings += [PSCustomObject]@{
                    Category = "Security"
                    Severity = "High"
                    Type = "Encryption Key Management"
                    Finding = "CMK configured but key vault properties are incomplete"
                    Recommendation = "Verify Key Vault configuration and key accessibility"
                    Remediation = "Review Key Vault settings and ensure proper access policies"
                }
            }
        }
    }
    
    # Check Shared Key access
    if ($secConfig.CheckSharedKeyAccess) {
        if ($StorageAccount.AllowSharedKeyAccess -ne $false) {
            $findings += [PSCustomObject]@{
                Category = "Security"
                Severity = "Medium"
                Type = "Authentication"
                Finding = "Shared Key (access key) authentication is enabled"
                Recommendation = "Consider disabling shared key access and use Azure AD authentication only"
                Remediation = "Set AllowSharedKeyAccess to false after ensuring apps use Azure AD"
            }
        }
    }
    
    # Check network rules
    if ($secConfig.CheckNetworkRules) {
        if ($StorageAccount.NetworkRuleSet.DefaultAction -eq 'Allow') {
            $findings += [PSCustomObject]@{
                Category = "Security"
                Severity = "Critical"
                Type = "Network Access"
                Finding = "Storage account allows access from all networks"
                Recommendation = "Restrict network access to specific virtual networks or IP ranges"
                Remediation = "Configure firewall rules and set default action to Deny"
            }
        }
    }
    
    # Check private endpoints
    if ($secConfig.CheckPrivateEndpoints) {
        if (-not $StorageAccount.PrivateEndpointConnections -or $StorageAccount.PrivateEndpointConnections.Count -eq 0) {
            $severity = if ($StorageAccount.Tags.Environment -eq 'Production') { 'High' } else { 'Medium' }
            $findings += [PSCustomObject]@{
                Category = "Security"
                Severity = $severity
                Type = "Network Isolation"
                Finding = "No private endpoints configured"
                Recommendation = "Implement private endpoints for network isolation and zero-trust architecture"
                Remediation = "Create private endpoint in target VNet and configure DNS records"
            }
        }
    }
    
    return $findings
}

#endregion

#region Assessment Logic - Resiliency

function Test-ResiliencyPosture {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        $StorageAccount,
        
        [Parameter(Mandatory = $true)]
        $Config
    )
    
    $findings = @()
    $resConfig = $Config.Resiliency
    
    # Check replication
    if ($resConfig.CheckReplication) {
        $replication = $StorageAccount.Sku.Name
        $environment = $StorageAccount.Tags.Environment
        
        if ($environment -eq 'Production') {
            $minimumReplication = $resConfig.MinimumReplicationForProduction
            
            $replicationLevels = @{
                'Standard_LRS' = 1
                'Standard_ZRS' = 2
                'Standard_GRS' = 3
                'Standard_RAGRS' = 4
                'Standard_GZRS' = 5
                'Standard_RAGZRS' = 6
                'Premium_LRS' = 1
                'Premium_ZRS' = 2
            }
            
            $currentLevel = $replicationLevels[$replication]
            $requiredLevel = switch ($minimumReplication) {
                'LRS' { 1 }
                'ZRS' { 2 }
                'GRS' { 3 }
                'RA-GRS' { 4 }
                'GZRS' { 5 }
                'RA-GZRS' { 6 }
                default { 2 }
            }
            
            if ($currentLevel -lt $requiredLevel) {
                $findings += [PSCustomObject]@{
                    Category = "Resiliency"
                    Severity = "High"
                    Type = "Replication"
                    Finding = "Production storage using $replication, minimum requirement is $minimumReplication"
                    Recommendation = "Upgrade replication to $minimumReplication or higher for production workloads"
                    Remediation = "Change storage account replication to meet production requirements"
                }
            }
        }
    }
    
    # Check soft delete and versioning
    if ($resConfig.CheckSoftDelete -or $resConfig.CheckVersioning) {
        try {
            $blobServiceProperties = Get-AzStorageBlobServiceProperty -ResourceGroupName $StorageAccount.ResourceGroupName -StorageAccountName $StorageAccount.StorageAccountName -ErrorAction Stop
            
            # Check blob soft delete
            if ($resConfig.CheckSoftDelete) {
                if (-not $blobServiceProperties.DeleteRetentionPolicy.Enabled) {
                    $findings += [PSCustomObject]@{
                        Category = "Resiliency"
                        Severity = "High"
                        Type = "Data Protection"
                        Finding = "Blob soft delete is not enabled"
                        Recommendation = "Enable soft delete with minimum $($resConfig.MinimumRetentionDays)-day retention"
                        Remediation = "Enable-AzStorageBlobDeleteRetentionPolicy -RetentionDays $($resConfig.MinimumRetentionDays)"
                    }
                }
                elseif ($blobServiceProperties.DeleteRetentionPolicy.Days -lt $resConfig.MinimumRetentionDays) {
                    $findings += [PSCustomObject]@{
                        Category = "Resiliency"
                        Severity = "Medium"
                        Type = "Data Protection"
                        Finding = "Soft delete retention ($($blobServiceProperties.DeleteRetentionPolicy.Days) days) is below minimum ($($resConfig.MinimumRetentionDays) days)"
                        Recommendation = "Increase retention period to meet compliance requirements"
                        Remediation = "Update-AzStorageBlobServiceProperty -RetentionDays $($resConfig.MinimumRetentionDays)"
                    }
                }
                
                # Check container soft delete
                if (-not $blobServiceProperties.ContainerDeleteRetentionPolicy.Enabled) {
                    $findings += [PSCustomObject]@{
                        Category = "Resiliency"
                        Severity = "Medium"
                        Type = "Data Protection"
                        Finding = "Container soft delete is not enabled"
                        Recommendation = "Enable container soft delete for protection against accidental deletion"
                        Remediation = "Enable-AzStorageContainerDeleteRetentionPolicy -RetentionDays 7"
                    }
                }
            }
            
            # Check versioning
            if ($resConfig.CheckVersioning) {
                if (-not $blobServiceProperties.IsVersioningEnabled) {
                    $findings += [PSCustomObject]@{
                        Category = "Resiliency"
                        Severity = "Medium"
                        Type = "Data Protection"
                        Finding = "Blob versioning is not enabled"
                        Recommendation = "Enable versioning for automatic version tracking and point-in-time recovery"
                        Remediation = "Update-AzStorageBlobServiceProperty -IsVersioningEnabled `$true"
                    }
                }
            }
            
            # Check point-in-time restore
            if ($resConfig.CheckPointInTimeRestore) {
                if (-not $blobServiceProperties.RestorePolicy.Enabled) {
                    $severity = if ($StorageAccount.Tags.Environment -eq 'Production') { 'Medium' } else { 'Low' }
                    $findings += [PSCustomObject]@{
                        Category = "Resiliency"
                        Severity = $severity
                        Type = "Data Protection"
                        Finding = "Point-in-time restore is not enabled"
                        Recommendation = "Enable point-in-time restore for production accounts (requires versioning and change feed)"
                        Remediation = "Enable-AzStorageBlobRestorePolicy -RestoreDays 6"
                    }
                }
            }
        }
        catch {
            Write-Status "Unable to retrieve blob service properties for $($StorageAccount.StorageAccountName): $_" -Type Warning
            $findings += [PSCustomObject]@{
                Category = "Resiliency"
                Severity = "Info"
                Type = "Data Protection"
                Finding = "Could not verify soft delete and versioning settings"
                Recommendation = "Verify blob service properties manually - possible permission issue"
                Remediation = "Ensure sufficient permissions to read storage account configuration"
            }
        }
    }
    
    return $findings
}

#endregion

#region Assessment Logic - Operational

function Test-OperationalBestPractices {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        $StorageAccount,
        
        [Parameter(Mandatory = $true)]
        $Config
    )
    
    $findings = @()
    $opConfig = $Config.Operational
    
    # Check naming conventions
    if ($opConfig.CheckNaming -and $opConfig.NamingPattern) {
        $accountName = $StorageAccount.StorageAccountName
        
        if ($accountName -notmatch $opConfig.NamingPattern) {
            $findings += [PSCustomObject]@{
                Category = "Operational"
                Severity = "Low"
                Type = "Naming"
                Finding = "Storage account name does not match naming convention"
                Recommendation = "Follow naming convention pattern: $($opConfig.NamingPattern)"
                Remediation = "Enforce naming standards for new storage accounts"
            }
        }
    }
    
    # Check required tags
    if ($opConfig.CheckTags -and $opConfig.RequiredTags) {
        $missingTags = @()
        
        foreach ($requiredTag in $opConfig.RequiredTags) {
            if (-not $StorageAccount.Tags -or -not $StorageAccount.Tags.ContainsKey($requiredTag)) {
                $missingTags += $requiredTag
            }
        }
        
        if ($missingTags.Count -gt 0) {
            $findings += [PSCustomObject]@{
                Category = "Operational"
                Severity = "Medium"
                Type = "Tagging"
                Finding = "Missing required tags: $($missingTags -join ', ')"
                Recommendation = "Add required tags for governance and cost management"
                Remediation = "Implement Azure Policy to enforce required tags"
            }
        }
    }
    
    # Check managed identity
    if ($opConfig.CheckManagedIdentity) {
        if (-not $StorageAccount.Identity -or $StorageAccount.Identity.Type -eq 'None') {
            $findings += [PSCustomObject]@{
                Category = "Operational"
                Severity = "Info"
                Type = "Identity"
                Finding = "No managed identity configured"
                Recommendation = "Consider using managed identity for accessing other Azure resources"
                Remediation = "Enable system-assigned or user-assigned managed identity"
            }
        }
    }
    
    # Check for legacy account types
    if ($StorageAccount.Kind -eq 'Storage') {
        $findings += [PSCustomObject]@{
            Category = "Operational"
            Severity = "High"
            Type = "Legacy Configuration"
            Finding = "Classic storage account type (Storage) detected"
            Recommendation = "Migrate to StorageV2 (general-purpose v2) for full feature support"
            Remediation = "Upgrade to StorageV2 account kind"
        }
    }
    
    # Check diagnostic settings
    if ($opConfig.CheckDiagnosticSettings) {
        try {
            $diagnostics = Get-AzDiagnosticSetting -ResourceId $StorageAccount.Id -ErrorAction SilentlyContinue
            
            if (-not $diagnostics -or $diagnostics.Count -eq 0) {
                $severity = if ($StorageAccount.Tags.Environment -eq 'Production') { 'High' } else { 'Medium' }
                $findings += [PSCustomObject]@{
                    Category = "Operational"
                    Severity = $severity
                    Type = "Monitoring"
                    Finding = "No diagnostic settings configured"
                    Recommendation = "Enable diagnostic logging to Log Analytics workspace or Storage account"
                    Remediation = "Configure diagnostic settings for auditing, monitoring, and compliance"
                }
            }
            else {
                # Check if logs and metrics are being captured
                $hasLogs = $false
                $hasMetrics = $false
                
                foreach ($setting in $diagnostics) {
                    if ($setting.Logs.Count -gt 0 -and ($setting.Logs | Where-Object { $_.Enabled }).Count -gt 0) {
                        $hasLogs = $true
                    }
                    if ($setting.Metrics.Count -gt 0 -and ($setting.Metrics | Where-Object { $_.Enabled }).Count -gt 0) {
                        $hasMetrics = $true
                    }
                }
                
                if (-not $hasLogs) {
                    $findings += [PSCustomObject]@{
                        Category = "Operational"
                        Severity = "Medium"
                        Type = "Monitoring"
                        Finding = "Diagnostic settings exist but no logs are enabled"
                        Recommendation = "Enable log collection for audit and troubleshooting"
                        Remediation = "Enable StorageRead, StorageWrite, and StorageDelete logs"
                    }
                }
                
                if (-not $hasMetrics) {
                    $findings += [PSCustomObject]@{
                        Category = "Operational"
                        Severity = "Low"
                        Type = "Monitoring"
                        Finding = "Diagnostic settings exist but no metrics are enabled"
                        Recommendation = "Enable metrics collection for performance monitoring"
                        Remediation = "Enable Transaction and Capacity metrics"
                    }
                }
            }
        }
        catch {
            Write-Status "Unable to retrieve diagnostic settings: $_" -Type Warning
        }
    }
    
    # Check if Classic Metrics are disabled (should use Azure Monitor metrics)
    if ($opConfig.CheckMonitoring) {
        # Informational recommendation for Azure Monitor
        $findings += [PSCustomObject]@{
            Category = "Operational"
            Severity = "Info"
            Type = "Monitoring"
            Finding = "Verify Azure Monitor integration for metrics and alerts"
            Recommendation = "Use Azure Monitor for metrics, alerts, and dashboards (not classic Storage Analytics)"
            Remediation = "Configure Azure Monitor alerts for capacity, availability, and latency"
        }
    }
    
    return $findings
}

#endregion

#region Assessment Logic - Lifecycle

function Test-LifecycleManagement {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        $StorageAccount,
        
        [Parameter(Mandatory = $true)]
        $Config
    )
    
    $findings = @()
    $lfConfig = $Config.Lifecycle
    
    # Check lifecycle policies
    if ($lfConfig.CheckLifecyclePolicies) {
        try {
            $managementPolicy = Get-AzStorageAccountManagementPolicy `
                -ResourceGroupName $StorageAccount.ResourceGroupName `
                -StorageAccountName $StorageAccount.StorageAccountName `
                -ErrorAction SilentlyContinue
            
            if (-not $managementPolicy) {
                $severity = if ($StorageAccount.Sku.Name -like 'Standard_*') { 'Medium' } else { 'Low' }
                $findings += [PSCustomObject]@{
                    Category = "Lifecycle"
                    Severity = $severity
                    Type = "Cost Optimization"
                    Finding = "No lifecycle management policy configured"
                    Recommendation = "Configure lifecycle policies for automatic tiering to cool/archive and data deletion"
                    Remediation = "Create lifecycle management rules based on access patterns to reduce costs"
                }
            }
            else {
                # Analyze policy completeness
                $rules = $managementPolicy.Policy.Rules
                $hasDeleteRule = $false
                $hasTieringRule = $false
                $hasSnapshotManagement = $false
                $hasVersionManagement = $false
                
                foreach ($rule in $rules) {
                    $actions = $rule.Definition.Actions
                    
                    if ($actions.BaseBlob.Delete) {
                        $hasDeleteRule = $true
                    }
                    if ($actions.BaseBlob.TierToCool -or $actions.BaseBlob.TierToArchive) {
                        $hasTieringRule = $true
                    }
                    if ($actions.Snapshot.Delete) {
                        $hasSnapshotManagement = $true
                    }
                    if ($actions.Version.Delete -or $actions.Version.TierToCool -or $actions.Version.TierToArchive) {
                        $hasVersionManagement = $true
                    }
                }
                
                if (-not $hasTieringRule) {
                    $findings += [PSCustomObject]@{
                        Category = "Lifecycle"
                        Severity = "Low"
                        Type = "Cost Optimization"
                        Finding = "Lifecycle policy exists but lacks tiering rules"
                        Recommendation = "Add rules to tier infrequently accessed data to Cool or Archive storage"
                        Remediation = "Configure tier transitions: Hot → Cool (30 days), Cool → Archive (90 days)"
                    }
                }
                
                if (-not $hasSnapshotManagement) {
                    $findings += [PSCustomObject]@{
                        Category = "Lifecycle"
                        Severity = "Info"
                        Type = "Data Hygiene"
                        Finding = "No lifecycle rules for snapshot cleanup"
                        Recommendation = "Consider adding rules to delete old snapshots"
                        Remediation = "Add snapshot deletion rules to prevent unnecessary storage costs"
                    }
                }
                
                if (-not $hasVersionManagement -and $lfConfig.CheckVersionHygiene) {
                    $findings += [PSCustomObject]@{
                        Category = "Lifecycle"
                        Severity = "Info"
                        Type = "Data Hygiene"
                        Finding = "No lifecycle rules for version management"
                        Recommendation = "If versioning is enabled, add rules to manage old versions"
                        Remediation = "Configure version cleanup: delete or tier non-current versions after X days"
                    }
                }
            }
        }
        catch {
            Write-Status "Unable to retrieve lifecycle policies for $($StorageAccount.StorageAccountName): $_" -Type Warning
            $findings += [PSCustomObject]@{
                Category = "Lifecycle"
                Severity = "Info"
                Type = "Lifecycle Management"
                Finding = "Could not verify lifecycle management policies"
                Recommendation = "Verify lifecycle policies manually - possible permission issue"
                Remediation = "Ensure sufficient permissions to read management policies"
            }
        }
    }
    
    return $findings
}

#endregion

#region Assessment Logic - Governance

function Test-GovernanceControls {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        $StorageAccount,
        
        [Parameter(Mandatory = $true)]
        $Config
    )
    
    $findings = @()
    $govConfig = $Config.Governance
    
    # Check RBAC assignments
    if ($govConfig.CheckRBAC) {
        try {
            $roleAssignments = Get-AzRoleAssignment -Scope $StorageAccount.Id -ErrorAction SilentlyContinue
            
            if ($roleAssignments) {
                # Check for excessive Owner role assignments
                $ownerAssignments = $roleAssignments | Where-Object { $_.RoleDefinitionName -eq 'Owner' }
                $maxOwners = if ($govConfig.MaxOwnerRoleAssignments) { $govConfig.MaxOwnerRoleAssignments } else { 2 }
                
                if ($ownerAssignments.Count -gt $maxOwners) {
                    $findings += [PSCustomObject]@{
                        Category = "Governance"
                        Severity = "Medium"
                        Type = "Access Control"
                        Finding = "$($ownerAssignments.Count) Owner role assignments detected (recommended maximum: $maxOwners)"
                        Recommendation = "Review and minimize Owner role assignments - apply principle of least privilege"
                        Remediation = "Use more specific roles like Storage Blob Data Contributor instead of Owner"
                    }
                }
                
                # Check for user accounts vs service principals
                $userAssignments = $roleAssignments | Where-Object { $_.ObjectType -eq 'User' -and $_.RoleDefinitionName -in @('Owner', 'Contributor') }
                if ($userAssignments.Count -gt 3) {
                    $findings += [PSCustomObject]@{
                        Category = "Governance"
                        Severity = "Low"
                        Type = "Access Control"
                        Finding = "$($userAssignments.Count) individual user accounts have Owner/Contributor access"
                        Recommendation = "Consider using groups or managed identities instead of individual user accounts"
                        Remediation = "Assign roles to Azure AD groups for easier management"
                    }
                }
            }
        }
        catch {
            Write-Status "Unable to retrieve RBAC assignments: $_" -Type Warning
        }
    }
    
    # Check resource locks
    if ($govConfig.CheckResourceLocks) {
        try {
            $locks = Get-AzResourceLock -ResourceGroupName $StorageAccount.ResourceGroupName `
                -ResourceName $StorageAccount.StorageAccountName `
                -ResourceType 'Microsoft.Storage/storageAccounts' `
                -ErrorAction SilentlyContinue
            
            if (-not $locks -or $locks.Count -eq 0) {
                $severity = if ($StorageAccount.Tags.Environment -eq 'Production') { 'Medium' } else { 'Low' }
                $findings += [PSCustomObject]@{
                    Category = "Governance"
                    Severity = $severity
                    Type = "Resource Protection"
                    Finding = "No resource locks configured"
                    Recommendation = "Apply CanNotDelete lock to prevent accidental deletion of production storage accounts"
                    Remediation = "New-AzResourceLock -LockLevel CanNotDelete -LockName 'DoNotDelete'"
                }
            }
            else {
                # Check lock level
                $hasCanNotDelete = $locks | Where-Object { $_.Properties.Level -eq 'CanNotDelete' }
                if (-not $hasCanNotDelete -and $StorageAccount.Tags.Environment -eq 'Production') {
                    $findings += [PSCustomObject]@{
                        Category = "Governance"
                        Severity = "Low"
                        Type = "Resource Protection"
                        Finding = "Resource lock exists but is not set to CanNotDelete level"
                        Recommendation = "Upgrade lock to CanNotDelete for production resources"
                        Remediation = "Update lock level to CanNotDelete for better protection"
                    }
                }
            }
        }
        catch {
            Write-Status "Unable to retrieve resource locks: $_" -Type Warning
        }
    }
    
    return $findings
}

#endregion

#region Main Assessment Execution

function Invoke-StorageAccountAssessment {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        $StorageAccount,
        
        [Parameter(Mandatory = $true)]
        $Config
    )
    
    Write-Host "`n  Assessing: " -NoNewline -ForegroundColor Gray
    Write-Host $StorageAccount.StorageAccountName -ForegroundColor White
    
    $allFindings = @()
    
    # Security assessment
    Write-Host "    • Security posture..." -ForegroundColor Gray
    $securityFindings = Test-SecurityPosture -StorageAccount $StorageAccount -Config $Config
    $allFindings += $securityFindings
    
    # Resiliency assessment
    Write-Host "    • Resiliency & DR..." -ForegroundColor Gray
    $resiliencyFindings = Test-ResiliencyPosture -StorageAccount $StorageAccount -Config $Config
    $allFindings += $resiliencyFindings
    
    # Operational assessment
    Write-Host "    • Operational practices..." -ForegroundColor Gray
    $operationalFindings = Test-OperationalBestPractices -StorageAccount $StorageAccount -Config $Config
    $allFindings += $operationalFindings
    
    # Lifecycle assessment
    if (-not $Quick) {
        Write-Host "    • Lifecycle management..." -ForegroundColor Gray
        $lifecycleFindings = Test-LifecycleManagement -StorageAccount $StorageAccount -Config $Config
        $allFindings += $lifecycleFindings
    }
    
    # Governance assessment
    if (-not $Quick) {
        Write-Host "    • Governance controls..." -ForegroundColor Gray
        $governanceFindings = Test-GovernanceControls -StorageAccount $StorageAccount -Config $Config
        $allFindings += $governanceFindings
    }
    
    # Calculate scores
    $criticalCount = ($allFindings | Where-Object { $_.Severity -eq 'Critical' }).Count
    $highCount = ($allFindings | Where-Object { $_.Severity -eq 'High' }).Count
    $mediumCount = ($allFindings | Where-Object { $_.Severity -eq 'Medium' }).Count
    $lowCount = ($allFindings | Where-Object { $_.Severity -eq 'Low' }).Count
    
    # Enhanced scoring with better weighting and minimum floor
    $score = 100 - ($criticalCount * 20) - ($highCount * 12) - ($mediumCount * 5) - ($lowCount * 2)
    $score = [math]::Max(10, [math]::Min(100, $score))  # Floor at 10, ceiling at 100
    
    # Display summary
    $scoreColor = if ($score -ge 80) { 'Green' } elseif ($score -ge 60) { 'Yellow' } else { 'Red' }
    Write-Host "    Score: " -NoNewline -ForegroundColor Gray
    Write-Host "$score/100" -ForegroundColor $scoreColor
    Write-Host "    Findings: " -NoNewline -ForegroundColor Gray
    Write-Host "$($allFindings.Count) total" -ForegroundColor Gray
    
    if ($criticalCount -gt 0) {
        Write-Host "      " -NoNewline
        Write-Host "[$criticalCount Critical]" -ForegroundColor Red -NoNewline
    }
    if ($highCount -gt 0) {
        Write-Host " [$highCount High]" -ForegroundColor DarkRed -NoNewline
    }
    if ($mediumCount -gt 0) {
        Write-Host " [$mediumCount Medium]" -ForegroundColor Yellow
    }
    else {
        Write-Host ""
    }
    
    return [PSCustomObject]@{
        StorageAccount = $StorageAccount.StorageAccountName
        ResourceGroup = $StorageAccount.ResourceGroupName
        Location = $StorageAccount.Location
        Sku = $StorageAccount.Sku.Name
        Kind = $StorageAccount.Kind
        Tags = $StorageAccount.Tags
        Score = $score
        Findings = $allFindings
        Summary = @{
            Total = $allFindings.Count
            Critical = $criticalCount
            High = $highCount
            Medium = $mediumCount
            Low = $lowCount
            Info = ($allFindings | Where-Object { $_.Severity -eq 'Info' }).Count
        }
    }
}

#endregion

#region Report Generation

function Export-AssessmentReport {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        $Results,
        
        [Parameter(Mandatory = $true)]
        [string]$OutputPath
    )
    
    Write-Section "Generating Reports" -Color 'Cyan'
    
    # Ensure output directory exists
    if (-not (Test-Path $OutputPath)) {
        New-Item -Path $OutputPath -ItemType Directory -Force | Out-Null
    }
    
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $reportPrefix = "StorageAssessment_$timestamp"
    
    # JSON Report
    try {
        $jsonPath = Join-Path $OutputPath "$reportPrefix.json"
        $Results | ConvertTo-Json -Depth 10 | Out-File -FilePath $jsonPath -Encoding UTF8
        Write-Status "JSON report: $jsonPath" -Type Success
    }
    catch {
        Write-Status "Failed to generate JSON report: $_" -Type Error
    }
    
    # CSV Report (findings)
    try {
        $csvPath = Join-Path $OutputPath "$reportPrefix.csv"
        $allFindings = $Results.StorageAccounts | ForEach-Object {
            $account = $_.StorageAccount
            $_.Findings | ForEach-Object {
                [PSCustomObject]@{
                    StorageAccount = $account
                    Category = $_.Category
                    Severity = $_.Severity
                    Type = $_.Type
                    Finding = $_.Finding
                    Recommendation = $_.Recommendation
                    Remediation = $_.Remediation
                }
            }
        }
        $allFindings | Export-Csv -Path $csvPath -NoTypeInformation -Encoding UTF8
        Write-Status "CSV report: $csvPath" -Type Success
    }
    catch {
        Write-Status "Failed to generate CSV report: $_" -Type Error
    }
    
    # HTML Report (using calm industrial theme)
    try {
        $htmlPath = Join-Path $OutputPath "$reportPrefix.html"
        $htmlContent = New-IndustrialPDFReport -Results $Results
        $htmlContent | Out-File -FilePath $htmlPath -Encoding UTF8
        Write-Status "HTML report: $htmlPath" -Type Success
    }
    catch {
        Write-Status "Failed to generate HTML report: $_" -Type Error
    }
    
    # PDF Report (if requested and PSWriteHTML available)
    if ($GeneratePDF) {
        try {
            if (Get-Module -ListAvailable -Name PSWriteHTML) {
                Import-Module PSWriteHTML -ErrorAction Stop
                $pdfPath = Join-Path $OutputPath "$reportPrefix.pdf"
                
                # Generate modern industrial-style PDF
                $pdfHtml = New-IndustrialPDFReport -Results $Results
                $pdfHtml | Out-File -FilePath $pdfPath.Replace('.pdf', '_temp.html') -Encoding UTF8
                
                # Note: Actual PDF conversion requires wkhtmltopdf or similar tool
                Write-Status "Industrial-style HTML generated for PDF conversion: $($pdfPath.Replace('.pdf', '_temp.html'))" -Type Success
                Write-Status "To convert to PDF, use: wkhtmltopdf --enable-local-file-access $($pdfPath.Replace('.pdf', '_temp.html')) $pdfPath" -Type Info
            }
            else {
                Write-Status "PSWriteHTML module not found. Run Setup-Prerequisites.ps1 to install" -Type Warning
            }
        }
        catch {
            Write-Status "PDF generation not available: $_" -Type Warning
        }
    }
    
    return $htmlPath
}

function New-HTMLReport {
    param($Results)
    
    $html = @"
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Azure Storage Assessment Report</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #0078d4;
            border-bottom: 3px solid #0078d4;
            padding-bottom: 10px;
        }
        h2 {
            color: #333;
            margin-top: 30px;
        }
        .header {
            background: linear-gradient(135deg, #0078d4 0%, #00bcf2 100%);
            color: white;
            padding: 20px;
            margin: -30px -30px 30px -30px;
        }
        .summary-box {
            display: flex;
            justify-content: space-around;
            margin: 20px 0;
            flex-wrap: wrap;
        }
        .summary-item {
            background-color: #f8f8f8;
            padding: 20px;
            border-radius: 5px;
            min-width: 200px;
            margin: 10px;
            text-align: center;
        }
        .summary-value {
            font-size: 32px;
            font-weight: bold;
            color: #0078d4;
        }
        .summary-label {
            color: #666;
            margin-top: 5px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #0078d4;
            color: white;
        }
        tr:hover {
            background-color: #f5f5f5;
        }
        .severity-critical {
            background-color: #d13438;
            color: white;
            padding: 4px 8px;
            border-radius: 3px;
            font-weight: bold;
        }
        .severity-high {
            background-color: #ff8c00;
            color: white;
            padding: 4px 8px;
            border-radius: 3px;
            font-weight: bold;
        }
        .severity-medium {
            background-color: #ffb900;
            color: black;
            padding: 4px 8px;
            border-radius: 3px;
            font-weight: bold;
        }
        .severity-low {
            background-color: #00b7c3;
            color: white;
            padding: 4px 8px;
            border-radius: 3px;
            font-weight: bold;
        }
        .severity-info {
            background-color: #8a8886;
            color: white;
            padding: 4px 8px;
            border-radius: 3px;
            font-weight: bold;
        }
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
            font-size: 12px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Azure Storage Account Assessment Report</h1>
            <p>Assessment ID: $($Results.Metadata.AssessmentId)</p>
            <p>Generated: $($Results.Metadata.Timestamp)</p>
            <p>Subscription: $($Results.Metadata.Subscription.Name)</p>
        </div>
        
        <h2>Executive Summary</h2>
        <div class="summary-box">
            <div class="summary-item">
                <div class="summary-value">$($Results.Summary.TotalAccounts)</div>
                <div class="summary-label">Storage Accounts</div>
            </div>
            <div class="summary-item">
                <div class="summary-value">$($Results.Summary.TotalFindings)</div>
                <div class="summary-label">Total Findings</div>
            </div>
            <div class="summary-item">
                <div class="summary-value">$($Results.Summary.CriticalFindings)</div>
                <div class="summary-label">Critical</div>
            </div>
            <div class="summary-item">
                <div class="summary-value">$($Results.Summary.HighFindings)</div>
                <div class="summary-label">High</div>
            </div>
            <div class="summary-item">
                <div class="summary-value">$($Results.Summary.MediumFindings)</div>
                <div class="summary-label">Medium</div>
            </div>
        </div>
        
        <h2>Storage Accounts</h2>
        <table>
            <thead>
                <tr>
                    <th>Storage Account</th>
                    <th>Location</th>
                    <th>SKU</th>
                    <th>Score</th>
                    <th>Findings</th>
                </tr>
            </thead>
            <tbody>
"@
    
    foreach ($account in $Results.StorageAccounts) {
        $scoreColor = if ($account.Score -ge 80) { 'green' } elseif ($account.Score -ge 60) { 'orange' } else { 'red' }
        $html += @"
                <tr>
                    <td><strong>$($account.StorageAccount)</strong></td>
                    <td>$($account.Location)</td>
                    <td>$($account.Sku)</td>
                    <td style="color: $scoreColor; font-weight: bold;">$($account.Score)/100</td>
                    <td>$($account.Summary.Total) ($($account.Summary.Critical)C / $($account.Summary.High)H / $($account.Summary.Medium)M / $($account.Summary.Low)L)</td>
                </tr>
"@
    }
    
    $html += @"
            </tbody>
        </table>
        
        <h2>Detailed Findings</h2>
        <table>
            <thead>
                <tr>
                    <th>Storage Account</th>
                    <th>Severity</th>
                    <th>Category</th>
                    <th>Finding</th>
                    <th>Recommendation</th>
                </tr>
            </thead>
            <tbody>
"@
    
    foreach ($account in $Results.StorageAccounts) {
        foreach ($finding in $account.Findings) {
            $html += @"
                <tr>
                    <td>$($account.StorageAccount)</td>
                    <td><span class="severity-$($finding.Severity.ToLower())">$($finding.Severity)</span></td>
                    <td>$($finding.Category)</td>
                    <td>$($finding.Finding)</td>
                    <td>$($finding.Recommendation)</td>
                </tr>
"@
        }
    }
    
    $html += @"
            </tbody>
        </table>
        
        <div class="footer">
            <p>Generated by Azure Storage Best Practices Analyzer v$($Results.Metadata.Version)</p>
            <p>Repository: <a href="$($Results.Metadata.Repository)">$($Results.Metadata.Repository)</a></p>
        </div>
    </div>
</body>
</html>
"@
    
    return $html
}

function New-IndustrialPDFReport {
    param($Results)
    
    # Calculate overall health metrics
    $totalAccounts = $Results.Summary.TotalAccounts
    $avgScore = if ($totalAccounts -gt 0) { 
        [math]::Round(($Results.StorageAccounts | Measure-Object -Property Score -Average).Average, 0) 
    } else { 0 }
    $criticalRate = if ($totalAccounts -gt 0) { 
        [math]::Round(($Results.Summary.CriticalFindings / $totalAccounts), 1) 
    } else { 0 }
    
    $html = @"
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Azure Storage Security Assessment | Industrial Report</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;500;700&family=Inter:wght@300;400;600;700;900&display=swap');
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #e8eef5 100%);
            color: #2c3e50;
            line-height: 1.6;
            padding: 0;
        }
        
        /* Cover Page */
        .cover-page {
            height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            position: relative;
            page-break-after: always;
            border-bottom: 4px solid #667eea;
        }
        
        .cover-grid {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-image: 
                repeating-linear-gradient(0deg, rgba(255, 255, 255, 0.05) 0px, transparent 1px, transparent 40px),
                repeating-linear-gradient(90deg, rgba(255, 255, 255, 0.05) 0px, transparent 1px, transparent 40px);
            pointer-events: none;
        }
        
        .cover-content {
            z-index: 10;
            text-align: center;
            max-width: 900px;
            padding: 60px;
        }
        
        .cover-badge {
            display: inline-block;
            background: rgba(255, 255, 255, 0.2);
            border: 2px solid rgba(255, 255, 255, 0.6);
            color: #ffffff;
            padding: 8px 24px;
            border-radius: 4px;
            font-family: 'Roboto Mono', monospace;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 3px;
            text-transform: uppercase;
            margin-bottom: 40px;
        }
        
        .cover-title {
            font-size: 72px;
            font-weight: 900;
            line-height: 1.1;
            margin-bottom: 20px;
            color: #ffffff;
            text-shadow: 2px 2px 20px rgba(0, 0, 0, 0.2);
            text-transform: uppercase;
            letter-spacing: -2px;
        }
        
        .cover-subtitle {
            font-size: 24px;
            color: rgba(255, 255, 255, 0.95);
            font-family: 'Roboto Mono', monospace;
            font-weight: 500;
            margin-bottom: 60px;
            letter-spacing: 2px;
        }
        
        .cover-meta {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 30px;
            margin-top: 80px;
        }
        
        .cover-meta-item {
            background: rgba(255, 255, 255, 0.15);
            border: 1px solid rgba(255, 255, 255, 0.3);
            padding: 20px;
            border-radius: 8px;
            backdrop-filter: blur(10px);
        }
        
        .cover-meta-label {
            font-size: 11px;
            color: rgba(255, 255, 255, 0.8);
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 8px;
            font-weight: 600;
        }
        
        .cover-meta-value {
            font-size: 18px;
            color: #ffffff;
            font-family: 'Roboto Mono', monospace;
            font-weight: 700;
        }
        
        /* Main Container */
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: #ffffff;
            padding: 60px;
        }
        
        /* Header Section */
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-left: 6px solid #5a67d8;
            padding: 40px;
            margin-bottom: 60px;
            position: relative;
            border-radius: 8px;
        }
        
        .header::after {
            content: '';
            position: absolute;
            top: 0;
            right: 0;
            width: 200px;
            height: 100%;
            background: linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.1) 100%);
        }
        
        .header h1 {
            font-size: 36px;
            font-weight: 900;
            color: #ffffff;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: -1px;
        }
        
        .header-subtitle {
            font-size: 14px;
            color: rgba(255, 255, 255, 0.85);
            font-family: 'Roboto Mono', monospace;
            letter-spacing: 1px;
        }
        
        /* KPI Dashboard */
        .kpi-dashboard {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 60px;
        }
        
        .kpi-card {
            background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
            border: 1px solid #e3e8ef;
            border-left: 4px solid #667eea;
            padding: 30px;
            border-radius: 8px;
            transition: all 0.3s ease;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        }
        
        .kpi-card.critical {
            border-left-color: #e85d75;
        }
        
        .kpi-card.high {
            border-left-color: #f09a61;
        }
        
        .kpi-card.medium {
            border-left-color: #f7c548;
        }
        
        .kpi-label {
            font-size: 11px;
            color: #6c757d;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 12px;
            font-weight: 600;
        }
        
        .kpi-value {
            font-size: 48px;
            font-weight: 900;
            font-family: 'Roboto Mono', monospace;
            color: #2c3e50;
            line-height: 1;
        }
        
        .kpi-value.critical { color: #e85d75; }
        .kpi-value.high { color: #f09a61; }
        .kpi-value.medium { color: #f7c548; }
        .kpi-value.success { color: #667eea; }
        
        .kpi-change {
            font-size: 12px;
            color: #6c757d;
            margin-top: 8px;
            font-family: 'Roboto Mono', monospace;
        }
        
        /* Section Headers */
        .section-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-left: 4px solid #5a67d8;
            padding: 20px 30px;
            margin: 40px 0 20px 0;
            border-radius: 6px;
            box-shadow: 0 2px 8px rgba(102, 126, 234, 0.15);
        }
        
        .section-header h2 {
            font-size: 20px;
            font-weight: 700;
            color: #ffffff;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin: 0;
        }
        
        /* Account Cards */
        .account-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 30px;
            margin-bottom: 40px;
        }
        
        .account-card {
            background: #ffffff;
            border: 1px solid #e3e8ef;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
        }
        
        .account-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px 30px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.2);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .account-name {
            font-size: 18px;
            font-weight: 700;
            color: #ffffff;
            font-family: 'Roboto Mono', monospace;
        }
        
        .account-score {
            font-size: 36px;
            font-weight: 900;
            font-family: 'Roboto Mono', monospace;
        }
        
        .account-score.good { color: #ffffff; }
        .account-score.warn { color: #fff3cd; }
        .account-score.critical { color: #ffcdd2; }
        
        .account-body {
            padding: 30px;
            background: #ffffff;
        }
        
        .account-meta {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .account-meta-item {
            font-size: 12px;
            color: #6c757d;
        }
        
        .account-meta-item strong {
            color: #2c3e50;
            font-family: 'Roboto Mono', monospace;
        }
        
        .finding-summary {
            display: flex;
            gap: 15px;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #e9ecef;
        }
        
        .finding-badge {
            background: #f8f9fa;
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 700;
            font-family: 'Roboto Mono', monospace;
            border: 2px solid;
        }
        
        .finding-badge.critical {
            border-color: #e85d75;
            color: #e85d75;
            background: #fef5f7;
        }
        
        .finding-badge.high {
            border-color: #f09a61;
            color: #f09a61;
            background: #fef8f4;
        }
        
        .finding-badge.medium {
            border-color: #f7c548;
            color: #f7c548;
            background: #fffcf0;
        }
        
        .finding-badge.low {
            border-color: #6c9bd1;
            color: #6c9bd1;
            background: #f4f8fc;
        }
        
        /* Findings Table */
        .findings-table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            margin: 20px 0;
            background: #ffffff;
            border: 1px solid #e3e8ef;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        }
        
        .findings-table thead tr {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        
        .findings-table th {
            padding: 16px 20px;
            text-align: left;
            font-size: 11px;
            font-weight: 700;
            color: #ffffff;
            text-transform: uppercase;
            letter-spacing: 2px;
            border-bottom: none;
        }
        
        .findings-table td {
            padding: 16px 20px;
            font-size: 13px;
            color: #2c3e50;
            border-bottom: 1px solid #e9ecef;
        }
        
        .findings-table tbody tr:hover {
            background: #f8f9fa;
        }
        
        .findings-table tbody tr:last-child td {
            border-bottom: none;
        }
        
        .severity-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 5px;
            font-size: 10px;
            font-weight: 700;
            font-family: 'Roboto Mono', monospace;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .severity-badge.critical {
            background: #fef5f7;
            color: #e85d75;
            border: 2px solid #e85d75;
        }
        
        .severity-badge.high {
            background: #fef8f4;
            color: #f09a61;
            border: 2px solid #f09a61;
        }
        
        .severity-badge.medium {
            background: #fffcf0;
            color: #f7c548;
            border: 2px solid #f7c548;
        }
        
        .severity-badge.low {
            background: #f4f8fc;
            color: #6c9bd1;
            border: 2px solid #6c9bd1;
        }
        
        .severity-badge.info {
            background: #f8f9fa;
            color: #6c757d;
            border: 2px solid #adb5bd;
        }
        
        /* Footer */
        .footer {
            margin-top: 80px;
            padding-top: 40px;
            border-top: 1px solid #e3e8ef;
            text-align: center;
            color: #6c757d;
            font-size: 11px;
            font-family: 'Roboto Mono', monospace;
        }
        
        .footer-link {
            color: #667eea;
            text-decoration: none;
        }
        
        /* Print Styles */
        @media print {
            body {
                background: #ffffff;
            }
            .cover-page {
                page-break-after: always;
            }
            .section-header {
                page-break-after: avoid;
            }
            .account-card {
                page-break-inside: avoid;
            }
        }
    </style>
</head>
<body>
    <!-- Cover Page -->
    <div class="cover-page">
        <div class="cover-grid"></div>
        <div class="cover-content">
            <div class="cover-badge">Security Assessment Report</div>
            <h1 class="cover-title">Azure Storage<br>Analysis</h1>
            <p class="cover-subtitle">ENTERPRISE SECURITY & COMPLIANCE AUDIT</p>
            
            <div class="cover-meta">
                <div class="cover-meta-item">
                    <div class="cover-meta-label">Assessment ID</div>
                    <div class="cover-meta-value">$($Results.Metadata.AssessmentId)</div>
                </div>
                <div class="cover-meta-item">
                    <div class="cover-meta-label">Generated</div>
                    <div class="cover-meta-value">$($Results.Metadata.Timestamp)</div>
                </div>
                <div class="cover-meta-item">
                    <div class="cover-meta-label">Subscription</div>
                    <div class="cover-meta-value">$($Results.Metadata.Subscription.Name)</div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Main Report -->
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>Executive Summary</h1>
            <p class="header-subtitle">Assessment ID: $($Results.Metadata.AssessmentId) | Version $($Results.Metadata.Version)</p>
        </div>
        
        <!-- KPI Dashboard -->
        <div class="kpi-dashboard">
            <div class="kpi-card">
                <div class="kpi-label">Storage Accounts</div>
                <div class="kpi-value success">$($Results.Summary.TotalAccounts)</div>
                <div class="kpi-change">ANALYZED</div>
            </div>
            <div class="kpi-card critical">
                <div class="kpi-label">Critical Issues</div>
                <div class="kpi-value critical">$($Results.Summary.CriticalFindings)</div>
                <div class="kpi-change">IMMEDIATE ACTION</div>
            </div>
            <div class="kpi-card high">
                <div class="kpi-label">High Priority</div>
                <div class="kpi-value high">$($Results.Summary.HighFindings)</div>
                <div class="kpi-change">REQUIRES ATTENTION</div>
            </div>
            <div class="kpi-card medium">
                <div class="kpi-label">Total Findings</div>
                <div class="kpi-value">$($Results.Summary.TotalFindings)</div>
                <div class="kpi-change">ACROSS ALL ACCOUNTS</div>
            </div>
        </div>
        
        <!-- Storage Accounts Section -->
        <div class="section-header">
            <h2>Storage Account Assessment</h2>
        </div>
        
        <div class="account-grid">
"@
    
    foreach ($account in $Results.StorageAccounts) {
        $scoreClass = if ($account.Score -ge 80) { 'good' } elseif ($account.Score -ge 60) { 'warn' } else { 'critical' }
        $html += @"
            <div class="account-card">
                <div class="account-header">
                    <div class="account-name">$($account.StorageAccount)</div>
                    <div class="account-score $scoreClass">$($account.Score)</div>
                </div>
                <div class="account-body">
                    <div class="account-meta">
                        <div class="account-meta-item">
                            <strong>LOCATION:</strong> $($account.Location)
                        </div>
                        <div class="account-meta-item">
                            <strong>SKU:</strong> $($account.Sku)
                        </div>
                        <div class="account-meta-item">
                            <strong>KIND:</strong> $($account.Kind)
                        </div>
                        <div class="account-meta-item">
                            <strong>RESOURCE GROUP:</strong> $($account.ResourceGroup)
                        </div>
                    </div>
                    <div class="finding-summary">
"@
        if ($account.Summary.Critical -gt 0) {
            $html += @"
                        <div class="finding-badge critical">$($account.Summary.Critical) CRITICAL</div>
"@
        }
        if ($account.Summary.High -gt 0) {
            $html += @"
                        <div class="finding-badge high">$($account.Summary.High) HIGH</div>
"@
        }
        if ($account.Summary.Medium -gt 0) {
            $html += @"
                        <div class="finding-badge medium">$($account.Summary.Medium) MEDIUM</div>
"@
        }
        if ($account.Summary.Low -gt 0) {
            $html += @"
                        <div class="finding-badge low">$($account.Summary.Low) LOW</div>
"@
        }
        $html += @"
                    </div>
                </div>
            </div>
"@
    }
    
    $html += @"
        </div>
        
        <!-- Detailed Findings Section -->
        <div class="section-header">
            <h2>Detailed Security Findings</h2>
        </div>
        
        <table class="findings-table">
            <thead>
                <tr>
                    <th>Account</th>
                    <th>Severity</th>
                    <th>Category</th>
                    <th>Finding</th>
                    <th>Recommendation</th>
                </tr>
            </thead>
            <tbody>
"@
    
    foreach ($account in $Results.StorageAccounts) {
        foreach ($finding in $account.Findings) {
            $html += @"
                <tr>
                    <td style="font-family: 'Roboto Mono', monospace; font-weight: 600;">$($account.StorageAccount)</td>
                    <td><span class="severity-badge $($finding.Severity.ToLower())">$($finding.Severity)</span></td>
                    <td style="color: #00ff88; font-weight: 600;">$($finding.Category)</td>
                    <td>$($finding.Finding)</td>
                    <td style="color: #b0b0b0;">$($finding.Recommendation)</td>
                </tr>
"@
        }
    }
    
    $html += @"
            </tbody>
        </table>
        
        <!-- Footer -->
        <div class="footer">
            <p>Generated by <strong>Azure Storage Best Practices Analyzer</strong> v$($Results.Metadata.Version)</p>
            <p>Repository: <a href="$($Results.Metadata.Repository)" class="footer-link">$($Results.Metadata.Repository)</a></p>
            <p style="margin-top: 20px; color: #606060;">This report contains confidential security assessment data. Handle with care.</p>
        </div>
    </div>
</body>
</html>
"@
    
    return $html
}

#endregion

#region Main Execution

try {
    # Display header
    Write-AssessmentHeader
    
    # Initialize Azure connection
    $context = Initialize-AzureConnection
    
    # Load configuration
    Write-Section "Configuration" -Color 'Cyan'
    $config = Get-AssessmentConfig
    Write-Status "Configuration loaded" -Type Success
    
    if ($Quick) {
        Write-Status "Quick mode enabled - reduced assessment depth" -Type Info
    }
    
    # Discover storage accounts
    $storageAccounts = Get-TargetStorageAccounts
    
    if ($storageAccounts.Count -eq 0) {
        Write-Status "No storage accounts to assess. Exiting." -Type Warning
        exit 0
    }
    
    # Run assessments
    Write-Section "Running Assessments" -Color 'Cyan'
    $Script:AssessmentResults.Summary.TotalAccounts = $storageAccounts.Count
    
    $assessmentCounter = 0
    foreach ($account in $storageAccounts) {
        $assessmentCounter++
        
        $accountResult = Invoke-StorageAccountAssessment -StorageAccount $account -Config $config
        $Script:AssessmentResults.StorageAccounts += $accountResult
        
        # Update summary
        $Script:AssessmentResults.Summary.TotalFindings += $accountResult.Summary.Total
        $Script:AssessmentResults.Summary.CriticalFindings += $accountResult.Summary.Critical
        $Script:AssessmentResults.Summary.HighFindings += $accountResult.Summary.High
        $Script:AssessmentResults.Summary.MediumFindings += $accountResult.Summary.Medium
        $Script:AssessmentResults.Summary.LowFindings += $accountResult.Summary.Low
        $Script:AssessmentResults.Summary.InfoFindings += $accountResult.Summary.Info
    }
    
    # Generate reports
    $reportPath = Export-AssessmentReport -Results $Script:AssessmentResults -OutputPath $OutputPath
    
    # Display final summary
    $duration = (Get-Date) - $Script:StartTime
    
    Write-Host "`n╔══════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║                   Assessment Complete                           ║" -ForegroundColor Green
    Write-Host "╚══════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Green
    
    Write-Host "Duration:          " -NoNewline -ForegroundColor Gray
    Write-Host "$($duration.ToString('mm\:ss'))" -ForegroundColor White
    
    Write-Host "Accounts Assessed: " -NoNewline -ForegroundColor Gray
    Write-Host "$($Script:AssessmentResults.Summary.TotalAccounts)" -ForegroundColor White
    
    Write-Host "Total Findings:    " -NoNewline -ForegroundColor Gray
    Write-Host "$($Script:AssessmentResults.Summary.TotalFindings)" -ForegroundColor White
    
    if ($Script:AssessmentResults.Summary.CriticalFindings -gt 0) {
        Write-Host "  Critical:        " -NoNewline -ForegroundColor Gray
        Write-Host "$($Script:AssessmentResults.Summary.CriticalFindings)" -ForegroundColor Red
    }
    
    if ($Script:AssessmentResults.Summary.HighFindings -gt 0) {
        Write-Host "  High:            " -NoNewline -ForegroundColor Gray
        Write-Host "$($Script:AssessmentResults.Summary.HighFindings)" -ForegroundColor DarkRed
    }
    
    if ($Script:AssessmentResults.Summary.MediumFindings -gt 0) {
        Write-Host "  Medium:          " -NoNewline -ForegroundColor Gray
        Write-Host "$($Script:AssessmentResults.Summary.MediumFindings)" -ForegroundColor Yellow
    }
    
    Write-Host "`nReports Location:  " -NoNewline -ForegroundColor Gray
    Write-Host "$OutputPath" -ForegroundColor White
    Write-Host "`nOpen HTML Report:  " -NoNewline -ForegroundColor Gray
    Write-Host $reportPath -ForegroundColor Cyan
    
    Write-Host "`n"
    
    # Exit code based on findings
    if ($Script:AssessmentResults.Summary.CriticalFindings -gt 0) {
        exit 2
    }
    elseif ($Script:AssessmentResults.Summary.HighFindings -gt 0) {
        exit 1
    }
    else {
        exit 0
    }
}
catch {
    Write-Host "`n╔══════════════════════════════════════════════════════════════════╗" -ForegroundColor Red
    Write-Host "║                    Assessment Failed                            ║" -ForegroundColor Red
    Write-Host "╚══════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Red
    
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host "`nStack Trace:" -ForegroundColor Yellow
    Write-Host $_.ScriptStackTrace -ForegroundColor Gray
    
    exit 99
}

#endregion
