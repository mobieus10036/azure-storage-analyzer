# Azure Storage Assessment Toolkit - Test Suite

## Running Tests

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_cost_analyzer.py

# Verbose output
pytest -v tests/
```

## Test Structure

```
tests/
├── __init__.py
├── test_collectors/
│   ├── test_storage_accounts.py
│   ├── test_blob_containers.py
│   └── test_metrics_collector.py
├── test_analyzers/
│   ├── test_cost_analyzer.py
│   ├── test_security_analyzer.py
│   └── test_governance_analyzer.py
├── test_reporters/
│   ├── test_json_reporter.py
│   ├── test_csv_reporter.py
│   └── test_markdown_reporter.py
└── test_utils/
    ├── test_auth.py
    ├── test_config.py
    └── test_helpers.py
```

## Writing Tests

### Example: Testing Cost Analyzer

```python
import pytest
from src.analyzers.cost_analyzer import CostAnalyzer

@pytest.fixture
def cost_analyzer():
    return CostAnalyzer(pricing_region='eastus')

@pytest.fixture
def sample_storage_account():
    return {
        'name': 'test-storage',
        'sku': 'Standard_LRS',
        'location': 'eastus'
    }

def test_estimate_storage_cost(cost_analyzer):
    # 100 GB in Hot tier, Standard_LRS
    size_bytes = 100 * 1024 * 1024 * 1024
    cost = cost_analyzer.estimate_storage_cost(
        size_bytes=size_bytes,
        access_tier='Hot',
        sku='Standard_LRS'
    )
    
    assert cost > 0
    assert isinstance(cost, float)
    # Rough validation based on pricing
    assert 1.5 < cost < 2.5

def test_calculate_tier_optimization(cost_analyzer):
    size_bytes = 1000 * 1024 * 1024 * 1024  # 1000 GB
    
    savings = cost_analyzer.calculate_tier_optimization_savings(
        current_tier='Hot',
        recommended_tier='Cool',
        size_bytes=size_bytes,
        sku='Standard_LRS'
    )
    
    assert savings['monthly_savings'] > 0
    assert savings['current_monthly_cost'] > savings['optimized_monthly_cost']
    assert savings['savings_percent'] > 0
```

### Mocking Azure SDK Calls

```python
from unittest.mock import Mock, patch
from src.collectors.storage_accounts import StorageAccountCollector

@patch('src.collectors.storage_accounts.StorageManagementClient')
@patch('src.collectors.storage_accounts.SubscriptionClient')
def test_get_storage_accounts(mock_sub_client, mock_storage_client):
    # Setup mocks
    credential = Mock()
    collector = StorageAccountCollector(credential)
    
    # Mock storage account response
    mock_account = Mock()
    mock_account.id = '/subscriptions/test-sub/resourceGroups/test-rg/providers/Microsoft.Storage/storageAccounts/teststorage'
    mock_account.name = 'teststorage'
    mock_account.location = 'eastus'
    mock_account.sku.name = 'Standard_LRS'
    
    mock_storage_client.return_value.storage_accounts.list.return_value = [mock_account]
    
    # Test
    accounts = collector.get_storage_accounts('test-sub-id')
    
    assert len(accounts) == 1
    assert accounts[0]['name'] == 'teststorage'
```

## Test Coverage Goals

- **Minimum:** 80% code coverage
- **Target:** 90% code coverage
- Focus on critical business logic and error handling

## Continuous Integration

Tests run automatically on:
- Pull requests
- Commits to main branch
- Nightly builds

### GitHub Actions Workflow

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run tests with coverage
      run: pytest --cov=src tests/
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```
