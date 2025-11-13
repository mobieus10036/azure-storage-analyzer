# Contributing to Azure Storage Assessment Toolkit

Thank you for your interest in contributing! This document provides guidelines and information for contributors.

## 🤝 How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/your-org/az-storage-assessment/issues)
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs. actual behavior
   - Environment details (Python version, OS, Azure SDK versions)
   - Error messages or logs (sanitized)

### Suggesting Features

1. Check [Discussions](https://github.com/your-org/az-storage-assessment/discussions) for similar ideas
2. Create a new discussion or issue describing:
   - Use case and problem it solves
   - Proposed solution
   - Alternative approaches considered
   - Impact on existing functionality

### Code Contributions

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes** following the coding standards below
4. **Add tests** for new functionality
5. **Run tests**: `pytest tests/`
6. **Update documentation** as needed
7. **Commit with clear messages**: `git commit -m "Add feature: description"`
8. **Push to your fork**: `git push origin feature/your-feature-name`
9. **Create a Pull Request**

## 📝 Coding Standards

### Python Style

- Follow [PEP 8](https://pep8.org/) style guide
- Use [Black](https://black.readthedocs.io/) for code formatting: `black src/ tests/`
- Maximum line length: 100 characters
- Use type hints where appropriate

### Code Quality

- Run pylint: `pylint src/`
- Maintain test coverage > 80%
- Write docstrings for all public functions/classes
- Use meaningful variable and function names

### Example Docstring

```python
def analyze_storage_account(account_id: str, config: dict) -> dict:
    """
    Analyze a storage account for cost optimization opportunities.
    
    Args:
        account_id: Azure resource ID of the storage account
        config: Configuration dictionary with analysis parameters
        
    Returns:
        Dictionary containing analysis results with keys:
        - 'findings': List of issues found
        - 'recommendations': List of recommended actions
        - 'estimated_savings': Potential monthly savings in USD
        
    Raises:
        ValueError: If account_id is invalid
        AuthenticationError: If Azure credentials are invalid
    """
    pass
```

## 🧪 Testing

### Running Tests

```bash
# All tests
pytest tests/

# With coverage
pytest --cov=src tests/

# Specific test file
pytest tests/test_cost_analyzer.py

# Verbose output
pytest -v tests/
```

### Writing Tests

- Place tests in `tests/` directory mirroring `src/` structure
- Name test files: `test_<module_name>.py`
- Name test functions: `test_<function_name>_<scenario>`
- Use fixtures for common setup
- Mock Azure API calls

### Example Test

```python
import pytest
from unittest.mock import Mock, patch
from src.analyzers.cost_analyzer import CostAnalyzer

@pytest.fixture
def mock_storage_account():
    return {
        'id': '/subscriptions/sub-123/resourceGroups/rg-test/providers/Microsoft.Storage/storageAccounts/sttest01',
        'name': 'sttest01',
        'sku': {'name': 'Standard_LRS'},
        'location': 'eastus'
    }

def test_calculate_savings_hot_to_cool(mock_storage_account):
    analyzer = CostAnalyzer()
    savings = analyzer.calculate_tier_savings(
        account=mock_storage_account,
        current_tier='Hot',
        recommended_tier='Cool',
        size_gb=1000
    )
    assert savings > 0
    assert 'monthly_savings' in savings
```

## 📚 Documentation

### Code Documentation

- Add docstrings to all public functions, classes, and modules
- Include type hints
- Document exceptions and edge cases

### README Updates

- Update README.md for new features
- Add examples for new CLI options
- Update feature list and roadmap

### Additional Documentation

- Add detailed guides in `docs/` folder
- Include diagrams for complex workflows
- Provide examples in `examples/` folder

## 🔒 Security

### Handling Sensitive Data

- **Never log or output**:
  - Storage account keys
  - SAS tokens
  - Connection strings
  - Personal data
- Use sanitization functions for outputs
- Test with sample/mock data

### Responsible Disclosure

If you discover a security vulnerability:
1. **Do NOT** create a public issue
2. Email security@your-org.com with details
3. Allow time for patch development
4. Coordinate disclosure timing

## 🌍 Community Guidelines

### Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- No harassment, discrimination, or inappropriate behavior

### Communication

- Use clear, professional language
- Respond to feedback graciously
- Ask questions when unclear
- Help others learn

## ✅ Pull Request Checklist

Before submitting a PR, ensure:

- [ ] Code follows style guidelines (black, pylint)
- [ ] All tests pass
- [ ] New tests added for new functionality
- [ ] Documentation updated
- [ ] Commit messages are clear
- [ ] No secrets or credentials in code
- [ ] PR description explains changes
- [ ] Related issue linked (if applicable)

## 🎯 Development Priorities

Current focus areas:
1. Core functionality (storage account analysis)
2. Cost optimization features
3. Security checks
4. Report quality
5. Performance optimization

## 📦 Release Process

1. Version bump in `setup.py`
2. Update CHANGELOG.md
3. Tag release: `git tag v1.0.0`
4. Create GitHub release
5. Publish to PyPI (maintainers only)

## 🙋 Getting Help

- 💬 [GitHub Discussions](https://github.com/your-org/az-storage-assessment/discussions) for questions
- 📖 Read existing documentation
- 🐛 Check existing issues
- 📧 Contact maintainers

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to the Azure Storage Assessment Toolkit! 🎉
