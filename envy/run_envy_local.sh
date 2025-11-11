#!/bin/bash
# Run Envy locally

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Parse arguments
PROFILE="balanced"
NO_GUI=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --profile)
            PROFILE="$2"
            shift 2
            ;;
        --no-gui)
            NO_GUI="--no-gui"
            shift
            ;;
        *)
            shift
            ;;
    esac
done

# Run Envy
python main.py --profile "$PROFILE" $NO_GUI
