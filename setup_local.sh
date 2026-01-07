#!/bin/bash
# setup_local.sh
# Local development environment setup script

set -e

echo "================================"
echo "BFIH Backend Local Setup"
echo "================================"

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create virtual environment
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
source venv/bin/activate
echo "✓ Virtual environment activated"

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip
echo "✓ Pip upgraded"

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
echo "✓ Dependencies installed"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "⚠ .env file created - please fill in your OpenAI API key and other secrets"
fi

# Create data directories
echo "Creating data directories..."
mkdir -p data/analyses data/scenarios data/status logs
echo "✓ Data directories created"

# Initialize vector store (interactive)
read -p "Do you want to set up the vector store with your treatise? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python3 setup_vector_store_fixed.py
fi

echo ""
echo "================================"
echo "Setup Complete!"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your OpenAI API key"
echo "2. Run: python3 bfih_orchestrator.py (to test)"
echo "3. Run: uvicorn bfih_api_server:app --reload (to start API)"
echo ""
