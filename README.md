# Azure Storage Assessment Toolkit

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![GitHub](https://img.shields.io/github/stars/mobieus10036/azure-storage-analyzer?style=social)](https://github.com/mobieus10036/azure-storage-analyzer)

A comprehensive, production-ready toolkit for assessing Azure Storage Accounts with a focus on **cost optimization**, **security best practices**, and **governance compliance**.

> **⚡ Quick Start**: Run your first assessment in 9 seconds with `python assess_storage.py --quick --pdf-only`

## 🎯 Overview

The Azure Storage Assessment Toolkit helps you:

- **📊 Discover** all Storage Accounts across subscriptions
- **💰 Identify Cost Savings** by detecting stale data, inefficient access tiers, and orphaned resources
- **🔒 Enhance Security** with configuration checks for encryption, network access, and authentication
- **📈 Optimize Performance** by analyzing access patterns and tier recommendations
- **📝 Generate Reports** in multiple formats (CSV, JSON, Markdown)

## ✨ Features

### Discovery & Inventory
- List all storage accounts across selected subscriptions
- Enumerate containers, file shares, queues, and tables
- Track resource tags and metadata

### Cost Optimization
- Identify **stale blobs** (not accessed in 90+ days)
- Detect **over-tiered data** (hot tier with cold access patterns)
- Find **orphaned resources** (empty containers, unused storage accounts)
- Calculate potential savings from tier optimization
- Analyze lifecycle management policies

### Security & Governance
- Check encryption at rest and in transit (HTTPS-only)
- Validate public access configurations
- Review network rules (firewall, virtual network, private endpoints)
- Audit authentication methods (keys vs. Azure AD)
- Verify soft delete and versioning status
- Check for Microsoft Defender for Storage enablement

### Compliance Checks
- Validate against Azure Well-Architected Framework
- Check for required tags
- Verify backup and disaster recovery configurations
- Review access logging and monitoring setup

## 🚀 Quick Start

### First-Time Users (Recommended)

**Want to assess your storage in under 10 seconds?**

```bash
# Install dependencies
pip install -r requirements.txt

# Run quick assessment with auto-detection (generates PDF report)
python assess_storage.py --quick --pdf-only
```

That's it! The toolkit will:
- ✅ Auto-discover all storage accounts across subscriptions
- ✅ Auto-detect FSLogix/AVD workloads for accurate cost estimation
- ✅ Generate a PDF executive summary in `./reports/`

**Example output:**
```
Auto-detected FSLogix/AVD workload from share: avdfslxuserprofiles
Auto-detected workload profile: heavy
Estimated monthly cost: $421.44
✓ PDF summary: reports/summary_2025-11-13_09-47-55.pdf
```

### Common Scenarios

**Monthly FinOps Cost Review:**
```bash
python assess_storage.py --config examples/scenarios/finops-review.yaml
```
- Fast assessment (quick mode enabled)
- Focus on cost optimization opportunities
- Generates CSV for Excel analysis + PDF for executives

**Security Audit:**
```bash
python assess_storage.py --config examples/scenarios/security-audit.yaml
```
- Comprehensive security checks
- Network isolation and access control review
- Generates JSON for SIEM integration

**FSLogix/AVD Optimization:**
```bash
python assess_storage.py --config examples/scenarios/fslogix-optimization.yaml
```
- File share performance analysis
- High-transaction workload cost estimation ($0.48/GB)
- Network and access tier recommendations

**Custom Configuration:**
```bash
# Use your own config file
python assess_storage.py --config my-config.yaml

# Or specify subscription and output directory
python assess_storage.py --subscription "Mobieus Labs - Prod" --output-dir ./reports/prod
```

### Prerequisites

- Python 3.9 or higher
- Azure CLI (authenticated) or Azure credentials
- Appropriate Azure permissions (Reader + Storage Blob Data Reader minimum)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/az-storage-assessment.git
cd az-storage-assessment

# Install dependencies
pip install -r requirements.txt
```

### Authentication

The toolkit uses Azure DefaultAzureCredential, which supports multiple authentication methods:

```bash
# Option 1: Azure CLI (recommended for interactive use)
az login

# Option 2: Environment variables
export AZURE_SUBSCRIPTION_ID="your-subscription-id"
export AZURE_TENANT_ID="your-tenant-id"
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-client-secret"
```

### Basic Usage

```bash
# Full assessment (all features, all report formats)
python assess_storage.py

# Quick assessment (9 seconds - skips detailed metrics)
python assess_storage.py --quick

# Run on specific subscription(s)
python assess_storage.py --subscription "sub-id-1" --subscription "sub-id-2"

# Run with custom output directory
python assess_storage.py --output-dir ./reports

# Enable verbose logging
python assess_storage.py --verbose
```

### Advanced Usage

```bash
# Generate PDF report only
python assess_storage.py --pdf-only

# Quick PDF report (fastest option)
python assess_storage.py --quick --pdf-only

# Interactive account selection
python assess_storage.py --interactive

# Quick mode with interactive selection
python assess_storage.py --quick --interactive

# Test specific workload profile
python assess_storage.py --workload heavy

# Use scenario configuration
python assess_storage.py --config scenarios/fslogix.yaml

# Combine options for custom workflow
python assess_storage.py --quick --subscription "Prod Sub" --output-dir ./monthly-review
```

### Configuration

Customize assessment behavior via `config.yaml`:

```yaml
# Stale data thresholds
stale_days: 90

# Cost analysis
include_cost_estimates: true

# Security checks
check_public_access: true
check_encryption: true
check_network_rules: true

# Output formats
output_formats:
  - json
  - csv
  - markdown
```

## 📊 Sample Output

### Summary Report (Markdown)

```
# Azure Storage Assessment Report
Generated: 2025-11-13 10:30:00 UTC

## Executive Summary
- Total Storage Accounts: 42
- Total Capacity: 15.3 TB
- Estimated Monthly Cost: $1,247.50
- Potential Monthly Savings: $312.80 (25%)

## Key Findings
🔴 **Critical**: 5 storage accounts allow public blob access
🟡 **Warning**: 12 accounts have blobs in Hot tier with no access in 90+ days
🟢 **Info**: 38 accounts have soft delete enabled

## Top Recommendations
1. Move 2.3 TB of stale data from Hot to Cool tier → Save $89/month
2. Enable soft delete on 4 storage accounts
3. Restrict public access on 5 storage accounts
4. Configure lifecycle management for 8 accounts
```

### Detailed CSV Export

```csv
SubscriptionId,ResourceGroup,StorageAccountName,Location,SKU,Capacity(GB),TotalBlobs,StaleBlobs,PublicAccess,SoftDelete,EstimatedMonthlyCost,PotentialSavings
sub-123,rg-prod,stproddata01,eastus,Standard_LRS,5120,45000,12000,Disabled,Enabled,412.50,89.30
...
```

## 📁 Project Structure

```
az-storage-assessment/
├── assess_storage.py          # Main CLI entry point
├── config.yaml                # Configuration file
├── requirements.txt           # Python dependencies
├── src/
│   ├── collectors/            # Data collection modules
│   │   ├── storage_accounts.py
│   │   ├── blob_containers.py
│   │   └── metrics_collector.py
│   ├── analyzers/             # Analysis modules
│   │   ├── cost_analyzer.py
│   │   ├── security_analyzer.py
│   │   └── stale_data_analyzer.py
│   ├── reporters/             # Report generation
│   │   ├── json_reporter.py
│   │   ├── csv_reporter.py
│   │   └── markdown_reporter.py
│   └── utils/                 # Utilities
│       ├── auth.py
│       ├── config.py
│       └── helpers.py
├── tests/                     # Unit tests
├── examples/                  # Sample reports and configs
└── docs/                      # Additional documentation
```

## 💰 Cost Estimation Notes

### Important Limitations

**Azure Files Transaction Costs**: Cost estimates for Azure File Shares include both storage and estimated transaction costs. However, actual costs can vary significantly based on your workload:

- **Light usage** (basic file storage): ~$0.10/GB/month
- **Moderate usage** (typical file shares): ~$0.20/GB/month  
- **Heavy usage** (FSLogix, AVD profiles): ~$0.48/GB/month

**Why the variation?** Azure Files charges separately for:
1. **Data storage**: ~$0.075/GB/month
2. **Transactions**: Read, write, list operations (can be 2-10x storage costs)

### Configuring Workload Profiles

Set your workload profile in `config.yaml` for more accurate estimates:

```yaml
cost_analysis:
  workload_profile: "heavy"  # Options: light, moderate, heavy
```

| Profile | Use Case | Est. Cost/GB/Month | Transaction Level |
|---------|----------|-------------------|-------------------|
| **light** | Basic file storage, infrequent access | ~$0.10 | Low read/write |
| **moderate** | Typical department shares, regular access | ~$0.20 | Normal activity |
| **heavy** | FSLogix, AVD profiles, continuous I/O | ~$0.48 | Very high transactions |

**Use "heavy" if you have:**
- FSLogix profile containers
- Azure Virtual Desktop (AVD) user profiles
- Continuous sync or backup operations
- High-transaction database files

**Actual costs**: Always compare estimates with your Azure Cost Management data. For high-transaction workloads, consider Azure Files Premium which includes transactions in the storage price.

## 🛡️ Security & Privacy

This toolkit:
- **Does NOT** access or read blob content
- **Does NOT** modify any Azure resources
- **Only requires READ permissions**
- Uses Azure-managed credentials (no secrets stored)
- Outputs can be sanitized before sharing

## 🤝 Contributing

Contributions welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Run linting
black src/ tests/
pylint src/
```

## 📋 Roadmap

- [ ] Azure Data Lake Storage Gen2 support
- [ ] Integration with Azure Cost Management API
- [ ] Power BI report template
- [ ] Azure DevOps pipeline examples
- [ ] GitHub Actions workflow
- [ ] Support for Azure Government and China clouds

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Azure SDK for Python](https://github.com/Azure/azure-sdk-for-python)
- Inspired by Azure Well-Architected Framework
- Community contributions and feedback

## 📞 Support

- 🐛 [Report bugs](https://github.com/your-org/az-storage-assessment/issues)
- 💡 [Request features](https://github.com/your-org/az-storage-assessment/issues)
- 💬 [Discussions](https://github.com/your-org/az-storage-assessment/discussions)

---

**Note**: This is a community tool and is not officially supported by Microsoft. Always test in non-production environments first.
