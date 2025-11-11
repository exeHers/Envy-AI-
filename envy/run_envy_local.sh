#!/bin/bash
# Quick start script for Envy
# MIT License

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Running installer..."
    ./install_envy.sh
fi

# Activate venv
source venv/bin/activate

# Parse arguments
PROFILE="balanced"
HEADLESS=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --profile)
            PROFILE="$2"
            shift 2
            ;;
        --no-gui)
            HEADLESS="--no-gui"
            shift
            ;;
        *)
            shift
            ;;
    esac
done

# Start Envy
echo "🤖 Starting Envy (profile: $PROFILE)..."
python main.py --profile "$PROFILE" $HEADLESS
