#!/bin/bash
# Double Top Scanner - Linux/Mac Setup Script
# This script sets up the Python environment and installs all dependencies

echo "================================================================================"
echo "DOUBLE TOP SCANNER - SETUP (Linux/Mac)"
echo "================================================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    echo "  - Ubuntu/Debian: sudo apt-get install python3 python3-pip python3-venv"
    echo "  - macOS: brew install python3"
    exit 1
fi

echo "[1/5] Python detected:"
python3 --version
echo ""

# Create virtual environment
echo "[2/5] Creating virtual environment..."
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

# Activate virtual environment and install dependencies
echo "[3/5] Installing dependencies..."
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi
echo "Dependencies installed successfully"
echo ""

# Copy configuration template if settings.yaml doesn't exist
echo "[4/5] Setting up configuration..."
if [ -f "config/settings.yaml" ]; then
    echo "Configuration file already exists, skipping"
else
    if [ -f "config/settings.yaml.template" ]; then
        cp config/settings.yaml.template config/settings.yaml
        echo "Configuration template copied to config/settings.yaml"
        echo "IMPORTANT: Edit config/settings.yaml with your settings before running"
    else
        echo "WARNING: Configuration template not found"
    fi
fi
echo ""

# Create output directories
echo "[5/5] Creating output directories..."
mkdir -p output/logs
echo "Output directories created"
echo ""

echo "================================================================================"
echo "SETUP COMPLETE!"
echo "================================================================================"
echo ""
echo "Next steps:"
echo "  1. Edit config/settings.yaml with your settings"
echo "  2. For Gmail notifications:"
echo "     - Enable 2-Step Verification"
echo "     - Generate App Password at: https://myaccount.google.com/apppasswords"
echo "     - Add credentials to config/settings.yaml"
echo "  3. Activate virtual environment:"
echo "     source venv/bin/activate"
echo "  4. Run the scanner:"
echo "     - Full scan:     python run_scanner.py"
echo "     - Test mode:     python run_scanner.py --test"
echo "     - Single symbol: python run_scanner.py --symbol AAPL"
echo "  5. Run tests:      python -m pytest tests/ -v"
echo ""
echo "For help, see README.md"
echo "================================================================================"
