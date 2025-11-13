# Architecture & Design

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLI Entry Point                               │
│                      (assess_storage.py)                             │
│                                                                       │
│  ┌────────────┐  ┌─────────────┐  ┌──────────────┐                 │
│  │ Arg Parser │  │ Config Mgr  │  │ Auth Handler │                 │
│  └────────────┘  └─────────────┘  └──────────────┘                 │
└───────────────────────────┬───────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   Assessment Orchestrator                            │
│                   (StorageAssessment)                                │
│                                                                       │
│  Coordinates: Data Collection → Analysis → Reporting                │
└─────┬────────────────────────┬──────────────────────┬───────────────┘
      │                        │                      │
      ▼                        ▼                      ▼
┌────────────┐        ┌─────────────┐        ┌─────────────┐
│ COLLECTORS │        │  ANALYZERS  │        │  REPORTERS  │
└────────────┘        └─────────────┘        └─────────────┘
      │                        │                      │
      │                        │                      │
┌─────▼──────────────────────────────────────────────────────────────┐
│                        Data Flow Pipeline                            │
└──────────────────────────────────────────────────────────────────────┘

COLLECTORS (Data Collection)
├── StorageAccountCollector
│   ├── Get subscriptions
│   ├── List storage accounts
│   ├── Get blob service properties
│   └── Collect metadata
│
├── BlobContainerCollector  
│   ├── List containers
│   ├── Analyze blobs
│   ├── Calculate access tiers
│   └── Detect stale data
│
└── MetricsCollector
    ├── Query Azure Monitor
    ├── Collect metrics (transactions, ingress, egress)
    └── Calculate statistics

ANALYZERS (Analysis & Insights)
├── CostAnalyzer
│   ├── Estimate storage costs
│   ├── Calculate tier optimization savings
│   ├── Generate cost recommendations
│   └── Calculate ROI
│
├── SecurityAnalyzer
│   ├── Check public access
│   ├── Validate encryption (at rest & in transit)
│   ├── Audit network rules
│   ├── Review authentication methods
│   ├── Check data protection features
│   └── Calculate security score
│
└── GovernanceAnalyzer
    ├── Validate tagging compliance
    ├── Check naming conventions
    ├── Verify lifecycle policies
    ├── Detect orphaned resources
    └── Audit diagnostics

REPORTERS (Output Generation)
├── JSONReporter
│   └── Complete data export
│
├── CSVReporter
│   ├── Storage accounts summary
│   ├── Findings export
│   └── Cost optimization recommendations
│
└── MarkdownReporter
    └── Executive summary

UTILITIES
├── Authentication (Azure credential management)
├── Configuration (YAML config loader)
└── Helpers (formatting, parsing, logging)
```

## Data Flow

```
1. INITIALIZATION
   ├─ Load configuration (config.yaml)
   ├─ Authenticate with Azure (DefaultAzureCredential)
   └─ Initialize collectors, analyzers, reporters

2. DATA COLLECTION
   ├─ Get accessible subscriptions
   ├─ For each subscription:
   │  ├─ List storage accounts (filtered by config)
   │  └─ For each storage account:
   │     ├─ Get blob service properties
   │     ├─ List containers
   │     ├─ For each container:
   │     │  ├─ List blobs (with sampling)
   │     │  ├─ Calculate size & tier distribution
   │     │  └─ Identify stale data
   │     └─ Query Azure Monitor metrics
   └─ Aggregate all data

3. ANALYSIS
   ├─ Cost Analysis:
   │  ├─ Calculate current costs by tier
   │  ├─ Identify optimization opportunities
   │  └─ Estimate potential savings
   │
   ├─ Security Analysis:
   │  ├─ Run security checks
   │  ├─ Generate findings
   │  └─ Calculate security score
   │
   └─ Governance Analysis:
      ├─ Validate compliance
      ├─ Check policies
      └─ Detect orphans

4. REPORTING
   ├─ Generate summary statistics
   ├─ Prioritize recommendations
   ├─ Create reports:
   │  ├─ JSON (complete data)
   │  ├─ CSV (tabular data)
   │  └─ Markdown (summary)
   └─ Save to output directory

5. COMPLETION
   └─ Display summary & exit
```

## Key Design Decisions

### 1. **Modular Architecture**
- Separation of concerns: Collectors, Analyzers, Reporters
- Easy to extend with new features
- Independent testing of components

### 2. **Configuration-Driven**
- YAML configuration for flexibility
- Command-line overrides for convenience
- Sensible defaults for quick start

### 3. **Azure SDK Best Practices**
- Use DefaultAzureCredential for multiple auth methods
- Proper error handling and retries
- Rate limiting to avoid throttling

### 4. **Performance Optimization**
- Parallel processing of storage accounts
- Sampling for large containers
- Quick mode option
- Configurable limits

### 5. **Output Flexibility**
- Multiple report formats (JSON, CSV, Markdown)
- Sanitization option for public sharing
- Timestamped files

### 6. **Security & Privacy**
- Read-only operations (no modifications)
- No blob content access
- Credential management via Azure SDK
- Optional output sanitization

## Extension Points

### Adding New Collectors
```python
from src.collectors.base import BaseCollector

class CustomCollector(BaseCollector):
    def collect(self, storage_account, config):
        # Your collection logic
        return data
```

### Adding New Analyzers
```python
from src.analyzers.base import BaseAnalyzer

class CustomAnalyzer(BaseAnalyzer):
    def analyze(self, data, config):
        # Your analysis logic
        return findings
```

### Adding New Reporters
```python
from src.reporters.base import BaseReporter

class CustomReporter(BaseReporter):
    def generate(self, assessment_data, filename):
        # Your reporting logic
        return output_path
```

## Performance Considerations

### Large Environments
- Use parallel processing (`execution.parallel.enabled: true`)
- Increase worker count (`execution.parallel.max_workers: 10`)
- Enable sampling (`stale_data.sample_size: 10000`)
- Set container limits (`stale_data.max_container_size: 1000000`)

### Quick Assessments
- Enable quick mode (`execution.quick_mode: true`)
- Disable metrics collection (`metrics.enabled: false`)
- Reduce sample size
- Filter subscriptions/resource groups

### Rate Limiting
- Azure imposes API rate limits
- Tool implements configurable rate limiting
- Automatic retry with exponential backoff

## Security Model

### Permissions Required
- **Minimum:** Reader (subscription/resource group level)
- **Recommended:** Reader + Storage Blob Data Reader
- **Enhanced:** Add Monitoring Reader for metrics

### What Data is Accessed
✅ Storage account metadata
✅ Container metadata  
✅ Blob metadata (name, size, tier, last modified)
✅ Azure Monitor metrics
❌ Blob content (never accessed)
❌ Access keys (not stored or logged)

### Authentication Methods Supported
1. Azure CLI (`az login`)
2. Managed Identity (when running in Azure)
3. Service Principal (environment variables)
4. Visual Studio Code
5. Azure PowerShell

## Future Enhancements

1. **Data Lake Gen2 Support**
2. **Actual Cost Integration** (Azure Cost Management API)
3. **Historical Trending**
4. **Power BI Template**
5. **CI/CD Integration Examples**
6. **Webhook Notifications**
7. **Custom Check Framework**
8. **Multi-Cloud Support**
