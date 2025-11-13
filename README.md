# Azure Storage Assessment Toolkit

A Python tool for assessing Azure Storage Accounts. Built to help with cost optimization, security checks, and compliance reporting.

> **Note**: This is a learning project. I'm relatively new to Python development and relied heavily on GitHub Copilot, Azure documentation, and community examples to build this. Suggestions and improvements are welcome!

## What It Does

This toolkit analyzes your Azure Storage Accounts and generates reports that show:

- Cost estimates and potential savings
- Security configuration issues
- Compliance with basic Azure best practices
- Stale data that could be moved to cheaper storage tiers

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Login to Azure
az login

# Run a quick assessment
python assess_storage.py --quick --pdf-only
```

This will scan your storage accounts and create a PDF report in the `./reports/` folder.

## Basic Usage

```bash
# Full assessment (takes longer, more detailed)
python assess_storage.py

# Quick mode (faster, less detail)
python assess_storage.py --quick

# Choose which accounts to assess
python assess_storage.py --interactive

# Specific subscription only
python assess_storage.py --subscription "your-subscription-name"
```

## What You Need

- Python 3.9 or newer
- Azure CLI installed and logged in (`az login`)
- Read permissions on your Azure Storage Accounts

## Output

The tool generates several report formats:

- **PDF** - Summary report (good for sharing with management)
- **CSV** - Detailed data (good for Excel analysis)
- **JSON** - Raw data (good for further processing)
- **Markdown** - Text-based summary

## Important Note on Cost Estimates

The cost estimates are approximations. Actual costs depend on many factors:

- Your specific Azure region
- How much you access your data (transactions)
- Data transfer amounts
- Special features you're using

For Azure Files, transaction costs can vary a lot:
- Basic file storage: ~$0.10/GB/month
- Regular file shares: ~$0.20/GB/month
- FSLogix/AVD profiles: ~$0.48/GB/month (lots of transactions)

Always check your actual bills in Azure Cost Management.

## Configuration

You can customize the assessment in `config.yaml`:

```yaml
# How many days before data is considered "stale"
stale_days: 90

# Workload type (affects cost estimates)
cost_analysis:
  workload_profile: "moderate"  # Options: light, moderate, heavy
```

## Project Structure

```
az-storage-assessment/
├── assess_storage.py       # Main script
├── config.yaml            # Settings
├── requirements.txt       # Python packages needed
├── src/
│   ├── collectors/        # Gets data from Azure
│   ├── analyzers/         # Analyzes the data
│   ├── reporters/         # Creates reports
│   └── utils/             # Helper functions
└── reports/               # Where reports are saved
```

## Limitations

- Only reads data, doesn't make any changes to Azure
- Doesn't access actual blob contents (just metadata)
- Cost estimates are rough - not exact billing
- Currently only supports Azure public cloud
- Some features may not work with all storage account types

## How I Built This

I'm learning Python and Azure together. This project was built with significant help from:

- GitHub Copilot for code suggestions and debugging
- Azure SDK documentation
- Stack Overflow for troubleshooting
- Various Azure community examples

The code probably isn't perfect, but it works for my needs. If you see ways to improve it, please let me know!

## Contributing

Found a bug? Have a suggestion? Please open an issue!

If you want to contribute code:
1. Fork the repo
2. Make your changes
3. Test it with your Azure environment
4. Submit a pull request

I appreciate any help making this better.

## License

MIT License - feel free to use and modify this for your own needs.

## Acknowledgments

- Azure SDK for Python
- GitHub Copilot (seriously, this wouldn't exist without it)
- The Azure community for documentation and examples
- 💬 [Discussions](https://github.com/your-org/az-storage-assessment/discussions)

---

**Note**: This is a community tool and is not officially supported by Microsoft. Always test in non-production environments first.
