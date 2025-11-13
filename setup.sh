#!/bin/bash

# Azure Storage Assessment Toolkit - Setup Script

echo "================================================================================"
echo "Azure Storage Assessment Toolkit - Setup"
echo "================================================================================"
echo ""

# Check Python version
echo "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.9 or higher"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found: Python $PYTHON_VERSION"

# Check if version is 3.9+
MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 9 ]); then
    echo "ERROR: Python 3.9 or higher is required"
    echo "Current version: $PYTHON_VERSION"
    exit 1
fi

echo ""

# Check Azure CLI
echo "Checking Azure CLI..."
if ! command -v az &> /dev/null; then
    echo "WARNING: Azure CLI is not installed"
    echo "You can install it from: https://docs.microsoft.com/cli/azure/install-azure-cli"
    echo "Or use other authentication methods (service principal, managed identity)"
else
    echo "Azure CLI is installed"
fi

echo ""

# Create virtual environment
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists, skipping creation"
else
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment"
        exit 1
    fi
    echo "Virtual environment created successfully"
fi

echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

echo ""

# Upgrade pip
echo "Upgrading pip..."
python -m pip install --upgrade pip --quiet

echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt --quiet

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi

echo "Dependencies installed successfully"

echo ""

# Check if config.yaml exists
if [ ! -f "config.yaml" ]; then
    echo "NOTE: config.yaml not found, using default configuration"
fi

echo ""
echo "================================================================================"
echo "Setup Complete!"
echo "================================================================================"
echo ""
echo "Next steps:"
echo "1. Authenticate with Azure: az login"
echo "2. Activate virtual environment: source venv/bin/activate"
echo "3. Run assessment: python assess_storage.py"
echo "4. Check reports in ./reports directory"
echo ""
echo "For help: python assess_storage.py --help"
echo "Documentation: docs/QUICKSTART.md"
echo ""
