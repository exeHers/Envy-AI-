#!/bin/bash
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Running installer..."
    bash scripts/install_envy.sh --local-demo
fi

source venv/bin/activate
python main.py "$@"
