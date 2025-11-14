# Quick Start Guide

Get started with Azure Storage Best Practices Analyzer in 2 steps!

## Step 1: Install Prerequisites

Run the prerequisite installer to ensure all required PowerShell modules are installed:

```powershell
.\Setup-Prerequisites.ps1
```

This will:
- ✅ Verify PowerShell 7+ is installed
- ✅ Install Azure PowerShell modules (Az.Storage, Az.Accounts, etc.)
- ✅ Install PSWriteHTML for PDF generation
- ✅ Verify internet connectivity and permissions
- ✅ Create reports directory

**Run this ONCE before your first assessment.**

## Step 2: Run Assessment

### Basic Assessment (All Storage Accounts)

```powershell
.\Invoke-StorageAssessment.ps1
```

This will:
- Connect to your Azure subscription
- Discover all storage accounts
- Assess security, resiliency, operational, and lifecycle best practices
- Generate HTML, JSON, and CSV reports
- Display rich terminal output with colored findings

### Advanced Usage

#### Assess Specific Storage Account

```powershell
.\Invoke-StorageAssessment.ps1 -StorageAccountName "mystorageaccount"
```

#### Assess Specific Resource Group

```powershell
.\Invoke-StorageAssessment.ps1 -ResourceGroupName "myresourcegroup"
```

#### Generate PDF Report

```powershell
.\Invoke-StorageAssessment.ps1 -GeneratePDF
```

#### Quick Mode (Faster Assessment)

```powershell
.\Invoke-StorageAssessment.ps1 -Quick
```

#### Target Specific Subscription

```powershell
.\Invoke-StorageAssessment.ps1 -SubscriptionId "12345678-1234-1234-1234-123456789abc"
```

#### Custom Output Directory

```powershell
.\Invoke-StorageAssessment.ps1 -OutputPath "C:\AzureAssessments"
```

#### Verbose Logging

```powershell
.\Invoke-StorageAssessment.ps1 -Verbose
```

## What You'll Get

### Terminal Output
- 🎨 **Rich colored output** with severity indicators
- 📊 **Progress bars** for multi-account assessments
- ✓ **Real-time status** updates
- 📈 **Score per storage account** (0-100)
- 📋 **Summary statistics** (Critical/High/Medium findings)

### Generated Reports
Located in `.\reports\` directory:

1. **HTML Report** (`StorageAssessment_YYYYMMDD_HHMMSS.html`)
   - Executive summary dashboard
   - Detailed findings table
   - Clickable navigation
   - Professional styling

2. **JSON Report** (`StorageAssessment_YYYYMMDD_HHMMSS.json`)
   - Complete assessment data
   - Machine-readable format
   - Integration-ready

3. **CSV Report** (`StorageAssessment_YYYYMMDD_HHMMSS.csv`)
   - All findings in tabular format
   - Excel-compatible
   - Easy filtering and sorting

4. **PDF Report** (if `-GeneratePDF` specified)
   - Print-ready format
   - Executive presentation

## Understanding Results

### Scoring System
- **100**: Perfect - No issues found
- **80-99**: Good - Minor improvements possible
- **60-79**: Fair - Some significant issues
- **40-59**: Poor - Multiple critical issues
- **0-39**: Critical - Immediate action required

### Finding Severity
- **Critical** 🔴 - Immediate security/compliance risk
- **High** 🟠 - Significant issue requiring attention
- **Medium** 🟡 - Important improvement opportunity
- **Low** 🔵 - Minor recommendation
- **Info** ⚪ - Informational guidance

## Example Output

```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║      Azure Storage Best Practices Analyzer                      ║
║      Enterprise Security, Governance & Resiliency Assessment     ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────┐
│ Azure Connection                                             │
└─────────────────────────────────────────────────────────────┘
✓ Connected to Azure
  Account:      user@company.com
  Subscription: Production Subscription
  Tenant:       12345678-1234-1234-1234-123456789abc

┌─────────────────────────────────────────────────────────────┐
│ Storage Account Discovery                                    │
└─────────────────────────────────────────────────────────────┘
✓ Found 3 storage account(s) to assess
  • mystorageacct01 [eastus] {Standard_GRS}
  • mystorageacct02 [westus2] {Premium_LRS}
  • stlogs [centralus] {Standard_LRS}

┌─────────────────────────────────────────────────────────────┐
│ Running Assessments                                          │
└─────────────────────────────────────────────────────────────┘

  Assessing: mystorageacct01
    • Security posture...
    • Resiliency & DR...
    • Operational practices...
    • Lifecycle management...
    Score: 75/100
    Findings: 5 total
      [1 Critical] [2 High] [2 Medium]

╔══════════════════════════════════════════════════════════════════╗
║                   Assessment Complete                           ║
╚══════════════════════════════════════════════════════════════════╝

Duration:          02:34
Accounts Assessed: 3
Total Findings:    12
  Critical:        2
  High:            4
  Medium:          6

Reports Location:  .\reports
Open HTML Report:  .\reports\StorageAssessment_20251114_105844.html
```

## Customization

### Configuration File

Edit `config.json` to customize assessment rules:

```json
{
  "Security": {
    "MinimumTLSVersion": "TLS1_2",
    "CheckPublicAccess": true,
    "CheckPrivateEndpoints": true
  },
  "Resiliency": {
    "MinimumReplicationForProduction": "ZRS",
    "CheckSoftDelete": true
  },
  "Operational": {
    "RequiredTags": ["Environment", "Owner", "CostCenter"]
  }
}
```

## Troubleshooting

### "Not connected to Azure"
Run: `Connect-AzAccount`

### "Module not found"
Run: `.\Setup-Prerequisites.ps1 -Force`

### "Access denied"
Ensure you have Reader permissions on storage accounts

### "No storage accounts found"
Verify subscription context: `Get-AzContext`

## CI/CD Integration

### Azure DevOps Pipeline

```yaml
steps:
- task: AzurePowerShell@5
  inputs:
    azureSubscription: 'MyAzureConnection'
    scriptType: 'FilePath'
    scriptPath: 'Invoke-StorageAssessment.ps1'
    azurePowerShellVersion: 'LatestVersion'
```

### GitHub Actions

```yaml
- name: Run Storage Assessment
  uses: azure/powershell@v1
  with:
    inlineScript: |
      ./Invoke-StorageAssessment.ps1 -OutputPath ./assessment-results
    azPSVersion: 'latest'
```

## Next Steps

1. Review the generated HTML report
2. Address Critical and High severity findings
3. Implement Azure Policy for continuous compliance
4. Schedule regular assessments (weekly/monthly)
5. Track score improvements over time

## Support

- 📖 Full Documentation: [README.md](README.md)
- 🐛 Issues: [GitHub Issues](https://github.com/mobieus10036/azure-storage-analyzer/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/mobieus10036/azure-storage-analyzer/discussions)

---

**Ready to improve your Azure Storage security posture? Run your first assessment now!**

```powershell
.\Setup-Prerequisites.ps1
.\Invoke-StorageAssessment.ps1 -GeneratePDF
```
