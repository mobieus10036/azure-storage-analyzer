# Quick Start Guide

## Prerequisites

1. **Python 3.9+** installed
2. **Azure CLI** installed and authenticated
3. **Azure permissions**: Minimum Reader + Storage Blob Data Reader

## Installation

```bash
# Clone repository
git clone https://github.com/your-org/az-storage-assessment.git
cd az-storage-assessment

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Authentication

```bash
# Login to Azure
az login

# Set default subscription (optional)
az account set --subscription "Your Subscription Name"
```

## Basic Usage

```bash
# Run assessment with default configuration
python assess_storage.py

# Assess specific subscription(s)
python assess_storage.py --subscription "sub-id-1"

# Custom output directory
python assess_storage.py --output-dir ./my-reports

# Quick mode (faster, less detailed)
python assess_storage.py --quick

# Verbose logging
python assess_storage.py --verbose
```

## Configuration

Edit `config.yaml` to customize:
- Stale data thresholds
- Security checks
- Cost analysis parameters
- Output formats

## Output Files

After running, find reports in `./reports/`:
- `storage_assessment_TIMESTAMP.json` - Complete data
- `storage_accounts_TIMESTAMP.csv` - Account summary
- `findings_TIMESTAMP.csv` - Security/governance findings
- `summary_TIMESTAMP.md` - Human-readable summary

## Common Scenarios

### 1. Assess Production Environment

```bash
python assess_storage.py \
  --subscription "prod-sub-id" \
  --output-dir ./prod-assessment
```

### 2. Quick Cost Check

```yaml
# Edit config.yaml
execution:
  quick_mode: true

cost_analysis:
  enabled: true
  calculate_savings: true
```

```bash
python assess_storage.py
```

### 3. Security Audit

```yaml
# Edit config.yaml
security:
  check_public_access: true
  check_encryption: true
  check_network_rules: true
  check_https_only: true
```

```bash
python assess_storage.py --verbose
```

## Troubleshooting

### Authentication Errors

```bash
# Re-login to Azure
az login

# Check current account
az account show
```

### Permission Errors

Ensure you have:
- `Reader` role on subscriptions/resource groups
- `Storage Blob Data Reader` for blob analysis

### No Storage Accounts Found

Check:
- Subscription IDs in config
- Resource group filters
- Tag filters

## Next Steps

- Review the generated Markdown summary
- Analyze CSV files in Excel/Power BI
- Act on high-severity findings
- Schedule regular assessments

## Support

- 📖 Full documentation: [README.md](README.md)
- 🐛 Report issues: [GitHub Issues](https://github.com/your-org/az-storage-assessment/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/your-org/az-storage-assessment/discussions)
