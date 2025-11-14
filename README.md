# Azure Storage Best Practices Analyzer

A comprehensive **PowerShell-based** assessment tool for evaluating Azure Storage Accounts against enterprise security, governance, resiliency, and operational best practices.

**Built for Azure Cloud Architects and Platform Engineers**

🔗 **Repository:** [github.com/mobieus10036/azure-storage-analyzer](https://github.com/mobieus10036/azure-storage-analyzer)

## Why PowerShell?

This tool is built 100% in PowerShell because:
- ✅ **Native Azure Integration** - Direct access to Azure PowerShell modules
- ✅ **Zero Dependencies** - No Python, pip, or virtual environments needed
- ✅ **Windows Native** - Already installed on Windows systems
- ✅ **Enterprise Ready** - Perfect for automation and CI/CD pipelines
- ✅ **Cross-Platform** - Works on Windows, Linux, and macOS with PowerShell 7+

## Features

### 1. Security Posture Assessment
- Public access configurations and exposure risks
- Private endpoint enforcement and network isolation
- TLS version compliance
- Shared Key Access vs Azure AD authentication
- Local user access, SAS tokens, and stored access policies
- Firewall rules and virtual network configurations
- Encryption settings (Microsoft-managed vs customer-managed keys)
- Soft delete, versioning, and immutable blob policies
- Defender for Storage configuration and threat detection
- Secure transfer enforcement
- Access logging and monitoring posture

### 2. Resiliency, DR & Data Protection
- Replication configuration analysis (LRS, ZRS, GRS, RA-GRS, GZRS)
- RPO/RTO alignment assessment
- Backup posture for all storage services
- Snapshot schedules and retention policies
- Cross-region restore readiness
- Geo-failover configuration validation

### 3. Operational & Configuration Best Practices
- Storage Account naming standards
- Resource group organization
- Tagging hygiene (environment, owner, data classification)
- Diagnostic settings completeness
- Managed identity usage patterns
- Network security patterns
- Principle of least privilege validation
- Legacy configuration identification

### 4. Data Lifecycle & Hygiene
- Lifecycle management policy validation
- Stale snapshot detection
- Data retention compliance
- Blob organization patterns
- Ungoverned data growth indicators

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Login to Azure (requires appropriate RBAC permissions)
az login

# Run a comprehensive assessment
python assess_storage.py

# Generate PDF report only (faster)
python assess_storage.py --pdf-only
```

This will scan your storage accounts and create detailed reports in the `./reports/` folder.

## Basic Usage

```bash
# Full assessment with all analyzers
python assess_storage.py

# Interactive mode - select specific accounts
python assess_storage.py --interactive

# Specific subscription only
python assess_storage.py --subscription "your-subscription-name"

# Focus on specific resource groups
python assess_storage.py --resource-group "rg-production"
```

## Required Permissions

The assessment requires the following Azure RBAC roles:

- **Reader** on Storage Accounts (minimum)
- **Storage Blob Data Reader** (for blob analysis)
- **Monitoring Reader** (for metrics and diagnostics)

Recommended for comprehensive assessment:
- **Reader** at subscription level
- **Security Reader** (for Defender for Storage insights)

## Output Reports

The tool generates multiple report formats:

- **PDF** - Executive-level assessment with prioritized recommendations
- **Markdown** - Detailed findings organized by category
- **CSV** - Granular data for filtering and analysis
- **JSON** - Complete assessment data for automation

### Report Structure

Each report includes:

1. **Executive Summary** - Key risks, strengths, and highest-priority remediations
2. **Storage Account Inventory** - Each account with summarized posture
3. **Detailed Findings** - Organized by category with risk ratings
4. **Recommended Remediations** - Clear, actionable, prioritized steps
5. **Policy & Governance Recommendations** - Tenant-wide enforcement guidance
6. **Hardening Checklist** - Engineer-ready implementation steps

## Configuration

Customize the assessment scope and depth in `config.yaml`:

```yaml
security:
  # Enable comprehensive security checks
  check_public_access: true
  check_private_endpoints: true
  check_defender_for_storage: true
  check_encryption: true
  check_network_rules: true

resiliency:
  # Validate DR and backup configurations
  check_replication: true
  check_backup_policies: true
  minimum_retention_days: 30
```

## Project Structure

```
az-storage-assessment/
├── assess_storage.py       # Main orchestration script
├── config.yaml            # Assessment configuration
├── requirements.txt       # Python dependencies
├── src/
│   ├── collectors/        # Azure data collection modules
│   ├── analyzers/         # Best practice analysis engines
│   ├── reporters/         # Report generation (PDF, CSV, JSON, Markdown)
│   └── utils/             # Helper functions and utilities
├── reports/               # Generated assessment reports
└── examples/              # Sample configurations and scenarios
```

## Assessment Categories

### Security Analysis
- Network exposure and public access risks
- Authentication method evaluation (Shared Key vs Azure AD)
- Encryption configuration (at-rest and in-transit)
- Private endpoint implementation
- Defender for Storage threat detection
- Access control and RBAC alignment
- Diagnostic logging completeness

### Resiliency & DR Analysis
- Replication strategy validation
- Geo-redundancy configuration
- Backup and snapshot policies
- Soft delete and versioning
- Immutable storage configurations
- Recovery time/point objectives assessment

### Operational Best Practices
- Naming conventions adherence
- Tagging standards compliance
- Resource organization patterns
- Managed identity usage
- Diagnostic settings configuration
- Legacy feature identification

### Data Lifecycle & Governance
- Lifecycle management policies
- Data retention compliance
- Stale data identification
- Blob versioning hygiene
- Snapshot management

## Example Scenarios

Pre-configured assessment profiles are available in `examples/scenarios/`:

- `security-audit.yaml` - Focus on security posture
- `fslogix-optimization.yaml` - AVD/FSLogix specific checks
- `finops-review.yaml` - Cost optimization focus (legacy)

## Risk Rating System

Findings are rated using a standardized severity scale:

- **Critical** - Immediate security risk or compliance violation
- **High** - Significant misconfiguration requiring prompt attention
- **Medium** - Best practice deviation with moderate impact
- **Low** - Minor optimization or hygiene improvement
- **Info** - Informational finding or recommendation

## Architecture Recommendations

The tool provides opinionated, architecture-quality guidance including:

- **Hardening strategies** for each storage account
- **Network isolation** patterns and enforcement
- **Zero trust** security model implementation
- **Tenant-wide governance** controls
- **Monitoring and auditability** frameworks
- **Compliance alignment** roadmaps

## Contributing

This is a professional-grade assessment tool. Contributions should maintain:

- Enterprise architecture quality standards
- Comprehensive error handling
- Detailed logging
- Clear documentation
- Azure best practices alignment

See `CONTRIBUTING.md` for guidelines.

## Support & Resources

- **Documentation**: See `docs/` folder for detailed guides
- **Azure Storage Best Practices**: https://learn.microsoft.com/azure/storage/
- **Azure Well-Architected Framework**: https://learn.microsoft.com/azure/well-architected/

## License

MIT License - See `LICENSE` file for details.

---

**Designed for Azure Cloud Architects and Platform Engineers**

This tool is built to provide deep, actionable insights for hardening Azure Storage infrastructure at enterprise scale.

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
