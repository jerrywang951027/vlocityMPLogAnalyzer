#!/bin/bash
# Performance Log Analyzer - Quick Start Script

echo "====================================="
echo "Performance Log Analyzer"
echo "====================================="
echo ""

# Use Python 3.13 explicitly
PYTHON_BIN="/usr/local/bin/python3"

# Verify Python version
echo "Using Python: $($PYTHON_BIN --version)"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    $PYTHON_BIN -m venv venv
    echo "Virtual environment created."
    echo ""
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import pandas" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    echo "Dependencies installed."
    echo ""
fi

# Run the application
echo "Starting Performance Log Analyzer..."
echo ""
cd source
python main.py

