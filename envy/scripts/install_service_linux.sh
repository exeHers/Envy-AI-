#!/bin/bash
# Install Envy as a systemd service
# MIT License

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "========================================="
echo "Installing Envy as systemd service"
echo "========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run as root (use sudo)"
    exit 1
fi

# Get actual user (not root)
ACTUAL_USER="${SUDO_USER:-$USER}"

echo "Installing for user: $ACTUAL_USER"
echo "Install directory: $PROJECT_ROOT"

# Create service file
SERVICE_FILE="/etc/systemd/system/envy.service"
cp "$SCRIPT_DIR/envy.service" "$SERVICE_FILE"

# Replace placeholders
sed -i "s|%USER%|$ACTUAL_USER|g" "$SERVICE_FILE"
sed -i "s|%INSTALL_DIR%|$PROJECT_ROOT|g" "$SERVICE_FILE"

echo "✓ Service file created: $SERVICE_FILE"

# Reload systemd
systemctl daemon-reload
echo "✓ Systemd reloaded"

# Enable service
systemctl enable envy.service
echo "✓ Service enabled"

echo ""
echo "========================================="
echo "✅ Service installed successfully!"
echo "========================================="
echo ""
echo "Control Envy with:"
echo "  Start:   sudo systemctl start envy"
echo "  Stop:    sudo systemctl stop envy"
echo "  Status:  sudo systemctl status envy"
echo "  Logs:    sudo journalctl -u envy -f"
echo ""
