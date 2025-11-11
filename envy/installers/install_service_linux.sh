#!/bin/bash
# Install Envy as a systemd service on Linux

set -e

echo "Installing Envy AI Assistant as systemd service..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (sudo)"
    exit 1
fi

# Get current user
if [ -n "$SUDO_USER" ]; then
    REAL_USER="$SUDO_USER"
else
    REAL_USER="$(whoami)"
fi

echo "Installing for user: $REAL_USER"

# Copy service file
cp envy.service /etc/systemd/system/envy@.service

# Reload systemd
systemctl daemon-reload

echo ""
echo "Service installed successfully!"
echo ""
echo "To enable and start the service:"
echo "  sudo systemctl enable envy@$REAL_USER"
echo "  sudo systemctl start envy@$REAL_USER"
echo ""
echo "To check status:"
echo "  sudo systemctl status envy@$REAL_USER"
echo ""
echo "To view logs:"
echo "  sudo journalctl -u envy@$REAL_USER -f"
echo ""
