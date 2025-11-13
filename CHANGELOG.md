# Changelog

All notable changes to the Azure Storage Assessment Toolkit will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-11-13

### Added
- Initial release of Azure Storage Assessment Toolkit
- Storage account discovery across subscriptions
- Blob container and blob analysis
- Stale data detection (90+ days no access)
- Cost optimization analysis and recommendations
- Security configuration assessment
  - Public access checks
  - Encryption validation (at rest and in transit)
  - Network rule analysis
  - Authentication method review
  - Data protection features (soft delete, versioning)
- Governance compliance checks
  - Tagging compliance
  - Naming convention validation
  - Lifecycle management policy checks
  - Orphaned resource detection
- Azure Monitor metrics collection
- Multiple report formats
  - JSON (complete data export)
  - CSV (storage accounts, findings, cost optimization)
  - Markdown (executive summary)
- Configurable assessment parameters via YAML
- Parallel processing support
- Quick mode for faster assessments
- CLI interface with multiple options

### Documentation
- Comprehensive README with features and usage
- Quick start guide
- Contributing guidelines
- Testing documentation
- Example configurations and sample outputs

### Known Limitations
- Requires minimum Azure Reader + Storage Blob Data Reader permissions
- Does not modify any Azure resources (read-only)
- Pricing estimates are approximations based on East US region
- Last access time tracking requires analytics logging to be enabled

## [Unreleased]

### Planned Features
- Azure Data Lake Storage Gen2 support
- Integration with Azure Cost Management API for actual costs
- Power BI report template
- Azure DevOps pipeline examples
- GitHub Actions workflow templates
- Support for Azure Government and China clouds
- Email notification support
- Webhook integration for findings
- Custom check framework
- Historical trending analysis
- Multi-language support

---

[1.0.0]: https://github.com/your-org/az-storage-assessment/releases/tag/v1.0.0
