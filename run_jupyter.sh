#!/bin/bash
# Launcher script for Jupyter Notebook

echo "🚀 Starting Jupyter Notebook for Performance Log Analyzer"
echo "========================================================="
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Check if jupyter is installed
if ! command -v jupyter &> /dev/null; then
    echo "❌ Jupyter not found in virtual environment"
    echo "Installing Jupyter..."
    pip install jupyter ipywidgets
fi

echo ""
echo "✅ Environment ready!"
echo ""
echo "📝 Jupyter will open in your browser at http://localhost:8888"
echo ""
echo "💡 Quick Start:"
echo "   1. Create a new Python 3 notebook"
echo "   2. Copy code from 'jupyter_analysis.py' into cells"
echo "   3. Or read 'JUPYTER_QUICKSTART.md' for detailed guide"
echo ""
echo "🛑 To stop Jupyter: Press Ctrl+C twice in this terminal"
echo ""
echo "========================================================="
echo ""

# Launch Jupyter
jupyter notebook

# When jupyter exits, deactivate
deactivate

