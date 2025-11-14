# Testing Checklist

Use this checklist to validate the Azure Storage Best Practices Analyzer before deploying to production.

---

## Prerequisites Testing

### Test 1: PowerShell Version Check
```powershell
$PSVersionTable.PSVersion
# Expected: 7.0 or higher
```

- [ ] PowerShell 7.0+ confirmed

### Test 2: Module Installation
```powershell
.\Setup-Prerequisites.ps1
```

**Verify Output:**
- [ ] PowerShell version check passes
- [ ] Az.Accounts module installed/verified
- [ ] Az.Storage module installed/verified
- [ ] Az.Resources module installed/verified
- [ ] Az.Monitor module installed/verified
- [ ] Az.Security module installed/verified
- [ ] PSWriteHTML module installed/verified (for PDF)
- [ ] Reports directory created
- [ ] All modules verified successfully
- [ ] Green success messages displayed

### Test 3: Force Reinstall
```powershell
.\Setup-Prerequisites.ps1 -Force
```

- [ ] Modules reinstalled successfully
- [ ] No errors displayed

---

## Azure Connection Testing

### Test 4: Manual Azure Login
```powershell
Connect-AzAccount
Get-AzContext
```

- [ ] Successfully authenticated
- [ ] Correct subscription displayed
- [ ] Tenant ID visible

### Test 5: Subscription Context
```powershell
Get-AzContext | Select-Object Account, Subscription, Tenant
```

- [ ] Account email correct
- [ ] Subscription name correct
- [ ] Tenant ID correct

---

## Basic Assessment Testing

### Test 6: Help Documentation
```powershell
Get-Help .\Invoke-StorageAssessment.ps1 -Full
```

- [ ] Synopsis displayed
- [ ] Parameters documented
- [ ] Examples shown

### Test 7: Default Assessment (All Storage Accounts)
```powershell
.\Invoke-StorageAssessment.ps1
```

**Verify Output:**
- [ ] Assessment header displayed with box characters
- [ ] Azure connection section shows subscription info
- [ ] Storage account discovery section lists accounts
- [ ] Assessment progress shown for each account
- [ ] Security checks executed
- [ ] Resiliency checks executed
- [ ] Operational checks executed
- [ ] Lifecycle checks executed
- [ ] Score displayed per account (0-100)
- [ ] Finding counts shown (Critical/High/Medium)
- [ ] Final summary displayed with totals
- [ ] Reports location shown
- [ ] HTML report path displayed

**Check Generated Files:**
- [ ] `.\reports\StorageAssessment_*.html` exists
- [ ] `.\reports\StorageAssessment_*.json` exists
- [ ] `.\reports\StorageAssessment_*.csv` exists
- [ ] Files have reasonable sizes (not empty)

### Test 8: HTML Report Validation
```powershell
# Open the HTML report
$htmlReport = Get-ChildItem .\reports\*.html | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Invoke-Item $htmlReport.FullName
```

**Verify in Browser:**
- [ ] Report title visible: "Azure Storage Account Assessment Report"
- [ ] Assessment ID and timestamp shown
- [ ] Subscription name displayed
- [ ] Executive summary boxes show counts
- [ ] Storage accounts table populated
- [ ] Scores visible with color coding
- [ ] Detailed findings table shows all issues
- [ ] Severity badges color-coded correctly
- [ ] Footer shows version and repository link
- [ ] Professional styling applied
- [ ] No broken links or images

### Test 9: JSON Report Structure
```powershell
$jsonReport = Get-ChildItem .\reports\*.json | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$data = Get-Content $jsonReport.FullName | ConvertFrom-Json
$data.Metadata
$data.Summary
$data.StorageAccounts | Select-Object StorageAccount, Score
```

- [ ] Metadata section contains AssessmentId, Timestamp, Version
- [ ] Summary section has TotalAccounts, TotalFindings counts
- [ ] StorageAccounts array populated
- [ ] Each account has Score and Findings

### Test 10: CSV Report Structure
```powershell
$csvReport = Get-ChildItem .\reports\*.csv | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Import-Csv $csvReport.FullName | Format-Table
```

- [ ] CSV has columns: StorageAccount, Category, Severity, Type, Finding, Recommendation, Remediation
- [ ] Multiple rows present
- [ ] Data properly formatted

---

## Parameter Testing

### Test 11: Specific Storage Account
```powershell
# Replace with an actual storage account name
.\Invoke-StorageAssessment.ps1 -StorageAccountName "yourstorageaccount"
```

- [ ] Only specified account assessed
- [ ] Findings specific to that account
- [ ] Reports generated successfully

### Test 12: Specific Resource Group
```powershell
# Replace with an actual resource group name
.\Invoke-StorageAssessment.ps1 -ResourceGroupName "yourresourcegroup"
```

- [ ] Only accounts in that resource group assessed
- [ ] Discovery section shows filtered accounts
- [ ] Reports generated successfully

### Test 13: Quick Mode
```powershell
.\Invoke-StorageAssessment.ps1 -Quick
```

- [ ] Assessment completes faster
- [ ] Lifecycle checks skipped (or reduced)
- [ ] Reports still generated

### Test 14: Custom Output Path
```powershell
.\Invoke-StorageAssessment.ps1 -OutputPath "C:\Temp\TestReports"
```

- [ ] Custom directory created automatically
- [ ] Reports written to custom location
- [ ] Success message shows correct path

### Test 15: Verbose Mode
```powershell
.\Invoke-StorageAssessment.ps1 -Verbose
```

- [ ] Additional diagnostic messages displayed
- [ ] Verbose output shows internal operations
- [ ] Assessment completes successfully

### Test 16: Specific Subscription
```powershell
# Replace with your subscription ID
.\Invoke-StorageAssessment.ps1 -SubscriptionId "12345678-1234-1234-1234-123456789abc"
```

- [ ] Context switched to specified subscription
- [ ] Accounts from that subscription assessed
- [ ] Reports generated successfully

---

## Finding Detection Testing

### Test 17: Public Access Detection
**Setup:** Create test storage account with public blob access enabled
```powershell
# Manual: Enable "Allow Blob public access" in portal
.\Invoke-StorageAssessment.ps1 -StorageAccountName "teststorage"
```

- [ ] High severity finding: "Public blob access is enabled"
- [ ] Recommendation provided
- [ ] Remediation steps shown

### Test 18: HTTPS-Only Detection
**Setup:** Storage account without HTTPS-only enforcement
```powershell
# Manual: Disable "Secure transfer required" in portal
.\Invoke-StorageAssessment.ps1 -StorageAccountName "teststorage"
```

- [ ] Critical severity finding: "HTTPS-only traffic is not enforced"
- [ ] Recommendation provided

### Test 19: Network Rules Detection
**Setup:** Storage account with default action "Allow"
```powershell
.\Invoke-StorageAssessment.ps1 -StorageAccountName "teststorage"
```

- [ ] Critical severity finding: "Storage account allows access from all networks"
- [ ] Network restriction recommendation provided

### Test 20: Replication Level Detection
**Setup:** Production storage account with LRS replication
```powershell
# Manual: Tag storage account with Environment=Production
# Manual: Set replication to Standard_LRS
.\Invoke-StorageAssessment.ps1 -StorageAccountName "teststorage"
```

- [ ] High severity finding: "Production storage using Standard_LRS"
- [ ] Recommendation to upgrade replication

### Test 21: Naming Convention Detection
**Setup:** Storage account with non-standard name
```powershell
.\Invoke-StorageAssessment.ps1 -StorageAccountName "MyStorage123"
```

- [ ] Low severity finding: "Storage account name does not match naming convention"
- [ ] Pattern recommendation provided

### Test 22: Missing Tags Detection
**Setup:** Storage account without required tags
```powershell
# Manual: Remove Environment, Owner, DataClassification tags
.\Invoke-StorageAssessment.ps1 -StorageAccountName "teststorage"
```

- [ ] Medium severity finding: "Missing required tags"
- [ ] List of missing tags shown

### Test 23: Legacy Account Type Detection
**Setup:** Storage account with Kind = "Storage" (classic)
```powershell
.\Invoke-StorageAssessment.ps1 -StorageAccountName "legacystorage"
```

- [ ] High severity finding: "Classic storage account type detected"
- [ ] Upgrade recommendation provided

---

## Configuration Testing

### Test 24: Custom Configuration
```powershell
# Edit config.json
# Change MinimumTLSVersion to TLS1_3
# Add custom RequiredTags
.\Invoke-StorageAssessment.ps1
```

- [ ] Custom settings applied
- [ ] TLS findings reflect new minimum
- [ ] Custom tag validation enforced

### Test 25: Missing Configuration File
```powershell
# Temporarily rename config.json
Rename-Item config.json config.json.bak
.\Invoke-StorageAssessment.ps1
```

- [ ] Warning message about using defaults
- [ ] Assessment continues with default config
- [ ] Reports generated successfully

```powershell
# Restore config.json
Rename-Item config.json.bak config.json
```

---

## Error Handling Testing

### Test 26: No Azure Connection
```powershell
# Disconnect from Azure first
Disconnect-AzAccount
.\Invoke-StorageAssessment.ps1
```

- [ ] Authentication prompt appears
- [ ] Assessment continues after login
- OR
- [ ] Clear error message displayed
- [ ] Script exits gracefully

### Test 27: Invalid Subscription ID
```powershell
.\Invoke-StorageAssessment.ps1 -SubscriptionId "invalid-guid"
```

- [ ] Error message displayed
- [ ] Script exits gracefully
- [ ] No reports generated (or empty)

### Test 28: Invalid Storage Account Name
```powershell
.\Invoke-StorageAssessment.ps1 -StorageAccountName "doesnotexist12345"
```

- [ ] Warning: "No storage accounts found"
- [ ] Script exits gracefully
- [ ] Exit code 0

### Test 29: Invalid Resource Group Name
```powershell
.\Invoke-StorageAssessment.ps1 -ResourceGroupName "doesnotexist"
```

- [ ] Error message or warning displayed
- [ ] Script exits gracefully

### Test 30: Insufficient Permissions
**Setup:** Login with account that has no storage account access
```powershell
.\Invoke-StorageAssessment.ps1
```

- [ ] Clear permission error displayed
- [ ] Guidance on required permissions
- [ ] Script exits gracefully

---

## Performance Testing

### Test 31: Single Storage Account (Baseline)
```powershell
Measure-Command {
    .\Invoke-StorageAssessment.ps1 -StorageAccountName "teststorage"
}
```

- [ ] Duration recorded: ________ seconds
- [ ] Assessment completes in reasonable time (< 1 minute for single account)

### Test 32: Multiple Storage Accounts
```powershell
Measure-Command {
    .\Invoke-StorageAssessment.ps1 -ResourceGroupName "yourgroup"
}
```

- [ ] Duration recorded: ________ seconds
- [ ] Progress visible for each account
- [ ] No timeouts or hangs

### Test 33: Quick Mode Performance
```powershell
Measure-Command {
    .\Invoke-StorageAssessment.ps1 -Quick
}
```

- [ ] Quick mode faster than normal mode
- [ ] Time difference: ________ seconds

---

## PDF Generation Testing

### Test 34: PDF Report Generation
```powershell
.\Invoke-StorageAssessment.ps1 -GeneratePDF
```

- [ ] PSWriteHTML module check performed
- [ ] PDF generation attempted
- OR
- [ ] Warning if PSWriteHTML not available
- [ ] Guidance provided to install

---

## Exit Code Testing

### Test 35: No Findings (Success)
**Setup:** Assess a well-configured storage account
```powershell
.\Invoke-StorageAssessment.ps1 -StorageAccountName "prodstorageacct"
$LASTEXITCODE
```

- [ ] Exit code = 0 (no critical/high findings)

### Test 36: High Findings (Warning)
**Setup:** Assess storage account with high severity issues
```powershell
.\Invoke-StorageAssessment.ps1 -StorageAccountName "teststorage"
$LASTEXITCODE
```

- [ ] Exit code = 1 (high findings present)

### Test 37: Critical Findings (Critical)
**Setup:** Assess storage account with critical severity issues
```powershell
.\Invoke-StorageAssessment.ps1 -StorageAccountName "unsecurestorage"
$LASTEXITCODE
```

- [ ] Exit code = 2 (critical findings present)

---

## UI/UX Testing

### Test 38: Terminal Output Formatting
```powershell
.\Invoke-StorageAssessment.ps1
```

**Verify Visual Elements:**
- [ ] Box-drawing characters render correctly (╔═╗║╚╝┌─┐│└┘)
- [ ] Unicode symbols display correctly (✓✗⚠▶•)
- [ ] Colors render correctly (Red, Yellow, Green, Cyan, Gray)
- [ ] No text wrapping issues
- [ ] Progress indicators work
- [ ] Section headers clearly visible
- [ ] Finding severity colors distinct

### Test 39: Terminal Width Compatibility
```powershell
# Resize terminal to narrow width
.\Invoke-StorageAssessment.ps1
```

- [ ] Output still readable at 80 characters wide
- [ ] No broken box characters
- [ ] Text wraps gracefully

---

## CI/CD Integration Testing

### Test 40: Azure DevOps Simulation
```powershell
# Simulate pipeline execution
$ErrorActionPreference = 'Continue'
.\Invoke-StorageAssessment.ps1 -OutputPath ./pipeline-reports
$exitCode = $LASTEXITCODE

Write-Host "Exit Code: $exitCode"
Get-ChildItem ./pipeline-reports
```

- [ ] Assessment completes
- [ ] Exit code captured correctly
- [ ] Reports in specified directory
- [ ] No pipeline-breaking errors

### Test 41: GitHub Actions Simulation
```powershell
# Simulate GitHub Actions run
$env:GITHUB_WORKSPACE = $PWD
.\Invoke-StorageAssessment.ps1 -OutputPath "$env:GITHUB_WORKSPACE/reports"
```

- [ ] Environment variable respected
- [ ] Reports written to correct location
- [ ] No path errors

---

## Stress Testing

### Test 42: Large Subscription (Many Storage Accounts)
**Setup:** Subscription with 10+ storage accounts
```powershell
.\Invoke-StorageAssessment.ps1
```

- [ ] All accounts discovered
- [ ] Progress bars show correctly
- [ ] No memory issues
- [ ] Reports generated successfully
- [ ] Assessment completes without hanging

### Test 43: Rapid Consecutive Runs
```powershell
1..5 | ForEach-Object {
    Write-Host "Run $_"
    .\Invoke-StorageAssessment.ps1 -Quick
}
```

- [ ] All runs complete successfully
- [ ] No file locking issues
- [ ] Reports timestamp correctly
- [ ] No resource exhaustion

---

## Documentation Testing

### Test 44: README Accuracy
- [ ] README examples work as documented
- [ ] Feature list matches implementation
- [ ] Prerequisites clearly stated
- [ ] Repository URL correct

### Test 45: QUICKSTART Guide
- [ ] Step 1 (Prerequisites) works
- [ ] Step 2 (Assessment) works
- [ ] Example commands all valid
- [ ] Output samples match actual output

### Test 46: Code Comments
```powershell
Get-Content .\Invoke-StorageAssessment.ps1 | Select-String "^#" | Measure-Object
```

- [ ] Adequate comments throughout
- [ ] Functions documented with descriptions
- [ ] Parameters documented
- [ ] Examples provided in help

---

## Compatibility Testing

### Test 47: PowerShell 7.0
```powershell
pwsh -Version 7.0 -File .\Invoke-StorageAssessment.ps1 -Quick
```

- [ ] Script executes without errors
- [ ] All features work

### Test 48: PowerShell 7.4+ (Latest)
```powershell
pwsh -File .\Invoke-StorageAssessment.ps1 -Quick
```

- [ ] Script executes without errors
- [ ] All features work

### Test 49: Windows Terminal
```powershell
# Run in Windows Terminal
.\Invoke-StorageAssessment.ps1
```

- [ ] Colors render correctly
- [ ] Unicode characters display properly
- [ ] No encoding issues

### Test 50: VS Code Integrated Terminal
```powershell
# Run in VS Code terminal
.\Invoke-StorageAssessment.ps1
```

- [ ] Colors render correctly
- [ ] Unicode characters display properly
- [ ] No encoding issues

---

## Final Validation

### Test 51: Complete End-to-End Workflow
```powershell
# Fresh start
.\Setup-Prerequisites.ps1
.\Invoke-StorageAssessment.ps1 -GeneratePDF

# Open HTML report
$report = Get-ChildItem .\reports\*.html | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Invoke-Item $report.FullName
```

- [ ] Prerequisites install successfully
- [ ] Assessment completes without errors
- [ ] All report formats generated
- [ ] HTML report opens and displays correctly
- [ ] Findings actionable and clear
- [ ] Professional presentation suitable for stakeholders

---

## Testing Summary

**Total Tests:** 51  
**Passed:** _____  
**Failed:** _____  
**Skipped:** _____

**Tested By:** _______________  
**Date:** _______________  
**PowerShell Version:** _______________  
**Azure Subscription:** _______________

**Overall Assessment:**
- [ ] Ready for production use
- [ ] Requires fixes (document below)
- [ ] Requires additional testing

**Issues Found:**
```
Document any issues here:




```

**Recommendations:**
```
Document any recommendations here:




```

---

## Post-Testing Actions

- [ ] Address all failed tests
- [ ] Update documentation based on findings
- [ ] Commit tested version to GitHub
- [ ] Tag release version (e.g., v2.0.0)
- [ ] Update CHANGELOG.md
- [ ] Announce release

---

*Testing Checklist Version: 1.0*  
*For: Azure Storage Best Practices Analyzer v2.0.0*
