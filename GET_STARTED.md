# 🎯 GETTING STARTED - Azure Storage Assessment Toolkit

## ⚡ Quick 5-Minute Setup

### 1. Prerequisites Check
```powershell
# Check Python (need 3.9+)
python --version

# Check Azure CLI (recommended)
az --version

# If Azure CLI not installed, get it from:
# https://docs.microsoft.com/cli/azure/install-azure-cli
```

### 2. Automated Setup
```powershell
# Run the setup script (does everything for you)
.\setup.ps1
```

This script will:
- ✅ Verify Python version
- ✅ Create virtual environment
- ✅ Install all dependencies
- ✅ Check Azure CLI

### 3. Authenticate with Azure
```powershell
# Login to Azure
az login

# (Optional) Set default subscription
az account set --subscription "Your Subscription Name"
```

### 4. Run Your First Assessment
```powershell
# Activate virtual environment
.\venv\Scripts\activate

# Run assessment
python assess_storage.py
```

That's it! Reports will be in `./reports/`

---

## 📊 What You'll Get

After running the assessment, you'll find:

### In `./reports/` directory:
1. **JSON File** - Complete raw data for integration
2. **CSV Files** - Spreadsheet-ready data:
   - Storage accounts summary
   - Security/governance findings
   - Cost optimization recommendations
3. **Markdown Summary** - Human-readable executive report

### Sample Output:
```
Assessment Complete!
================================================================================
Assessed 15 storage accounts
Generated 4 report files

Total capacity: 3470.50 GB
Estimated monthly cost: $425.80
Potential monthly savings: $87.30
```

---

## 🎨 Customization Options

### Quick Mode (Faster, Less Detail)
```powershell
python assess_storage.py --quick
```

### Specific Subscription
```powershell
python assess_storage.py --subscription "your-sub-id"
```

### Custom Output Directory
```powershell
python assess_storage.py --output-dir ./my-reports
```

### Verbose Logging
```powershell
python assess_storage.py --verbose
```

### All Options
```powershell
python assess_storage.py --help
```

---

## ⚙️ Configuration

Edit `config.yaml` to customize:

```yaml
# How long before data is "stale"?
stale_data:
  threshold_days: 90

# What to analyze?
cost_analysis:
  enabled: true
  calculate_savings: true

security:
  check_public_access: true
  check_encryption: true

# What formats to output?
output:
  formats:
    - json
    - csv
    - markdown
```

See `examples/` folder for more config samples.

---

## 🔍 Understanding Your Reports

### 1. Markdown Summary (`summary_*.md`)
**Best for:** Quick overview for management

Contains:
- Executive summary with key metrics
- Security score
- Top recommendations with priorities
- Cost optimization opportunities

### 2. Storage Accounts CSV (`storage_accounts_*.csv`)
**Best for:** Spreadsheet analysis, sorting, filtering

Columns include:
- Account details (name, location, SKU)
- Size and blob counts
- Security configuration
- Cost estimates
- Potential savings

### 3. Findings CSV (`findings_*.csv`)
**Best for:** Tracking remediation work

Each row is a finding with:
- Severity (Critical, High, Medium, Low, Info)
- Type (security, cost, governance)
- Recommendation
- Remediation steps

### 4. JSON Export (`storage_assessment_*.json`)
**Best for:** Integration with other tools, custom analysis

Complete structured data including:
- All storage accounts
- All containers
- All findings
- All metrics
- Configuration used

---

## 🎯 Common Scenarios

### Scenario 1: "I want to find cost savings quickly"
```powershell
# Use quick mode, focus on cost
python assess_storage.py --quick
```
Then open the Markdown summary and look at the "Cost Analysis" section.

### Scenario 2: "I need a security audit for compliance"
```powershell
# Full assessment with verbose logging
python assess_storage.py --verbose
```
Then review the "findings_*.csv" file, filtering by severity.

### Scenario 3: "I want to assess multiple subscriptions"
```powershell
python assess_storage.py `
  --subscription "prod-sub-id" `
  --subscription "staging-sub-id" `
  --output-dir ./multi-sub-report
```

### Scenario 4: "I need production-grade detailed analysis"
```powershell
# Use production config
python assess_storage.py --config examples/config-production.yaml
```

---

## 🆘 Troubleshooting

### Error: "Python not found"
**Solution:** Install Python 3.9+ from https://www.python.org/

### Error: "Authentication failed"
**Solution:** Run `az login` to authenticate

### Error: "No storage accounts found"
**Causes:**
1. No storage accounts in subscription
2. Filter too restrictive in config
3. Insufficient permissions

**Solution:** Check `config.yaml` filters and your Azure role assignments

### Error: "Permission denied"
**Solution:** Ensure you have at least `Reader` + `Storage Blob Data Reader` roles

### Reports are empty
**Cause:** Quick mode skips some analysis

**Solution:** Run without `--quick` flag for full details

---

## 📚 Learn More

- **Architecture:** See `docs/ARCHITECTURE.md`
- **Testing:** See `docs/TESTING.md`  
- **Contributing:** See `CONTRIBUTING.md`
- **Examples:** See `examples/` folder

---

## ✅ Checklist for Your First Run

- [ ] Python 3.9+ installed
- [ ] Azure CLI installed (optional but recommended)
- [ ] Authenticated with Azure (`az login`)
- [ ] Dependencies installed (`.\setup.ps1`)
- [ ] Virtual environment activated
- [ ] `config.yaml` reviewed (optional)
- [ ] Run `python assess_storage.py`
- [ ] Check `./reports/` directory
- [ ] Review Markdown summary
- [ ] Open CSV in Excel/viewer
- [ ] Act on high-priority findings!

---

## 🚀 Advanced Usage

### Schedule Regular Assessments
```powershell
# Windows Task Scheduler
# Create a scheduled task to run weekly

# Task Action:
powershell.exe -File "C:\path\to\run_assessment.ps1"

# run_assessment.ps1 content:
cd C:\path\to\az-storage-assessment
.\venv\Scripts\activate
python assess_storage.py --output-dir ".\reports\$(Get-Date -Format 'yyyy-MM-dd')"
```

### Integrate with CI/CD
See `docs/ARCHITECTURE.md` for pipeline examples

### Export to Power BI
1. Run assessment to generate CSV
2. Import CSV files into Power BI
3. Create dashboards from the data

---

## 💡 Pro Tips

1. **First run in quick mode** to get familiar with outputs
2. **Run full assessment overnight** for large environments
3. **Compare reports over time** to track improvements
4. **Share Markdown summary** with management
5. **Use CSV for tracking** remediation work
6. **Automate regular runs** for continuous monitoring

---

## 🎉 You're Ready!

Everything is set up and ready to go. Run your first assessment:

```powershell
python assess_storage.py
```

Check the `./reports/` folder for your results!

---

**Need Help?**
- 📖 Read the full [README.md](README.md)
- 🐛 [Report an issue](https://github.com/your-org/az-storage-assessment/issues)
- 💬 [Start a discussion](https://github.com/your-org/az-storage-assessment/discussions)

**Happy Assessing! 🚀**
