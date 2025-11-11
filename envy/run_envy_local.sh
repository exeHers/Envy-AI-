#!/bin/bash
# Run Envy locally

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENVY_DIR="$SCRIPT_DIR"
VENV_DIR="$ENVY_DIR/venv"
PROFILE="${PROFILE:-balanced}"

# Parse arguments
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

# Activate virtual environment
if [ -d "$VENV_DIR" ]; then
    source "$VENV_DIR/bin/activate"
else
    echo "Virtual environment not found. Run install_envy.sh first."
    exit 1
fi

# Change to envy directory
cd "$ENVY_DIR"

# Run Envy
python3 envy.py --profile "$PROFILE" $NO_GUI
