#!/bin/bash
# MindWave Connection Helper Script
# Run this after every Raspberry Pi reboot to connect the headset

# IMPORTANT: Replace XX:XX:XX:XX:XX:XX with YOUR MindWave's MAC address!
MINDWAVE_MAC="74:E5:43:XX:XX:XX"

echo "========================================"
echo "MindWave Mobile 2 Connection Script"
echo "========================================"
echo ""

# Release any existing binding
echo "Releasing existing connection..."
sudo rfcomm release /dev/rfcomm0 2>/dev/null

# Bind to serial port
echo "Binding MindWave to /dev/rfcomm0..."
sudo rfcomm bind /dev/rfcomm0 $MINDWAVE_MAC 1

# Set permissions
echo "Setting permissions..."
sudo chmod 666 /dev/rfcomm0

# Check if successful
if [ -e /dev/rfcomm0 ]; then
    echo ""
    echo "✓ MindWave connected successfully!"
    echo ""
    ls -l /dev/rfcomm0
    echo ""
    echo "You can now run: python3 main.py"
else
    echo ""
    echo "✗ Failed to connect MindWave"
    echo "Check that the headset is powered on and paired"
    echo ""
    echo "To pair manually, run:"
    echo "  sudo bluetoothctl"
    echo "  scan on"
    echo "  pair $MINDWAVE_MAC"
    echo "  trust $MINDWAVE_MAC"
    exit 1
fi
