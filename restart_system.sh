#!/bin/bash
# Restart System Helper Script
# Properly cleans up and restarts the EEG-Drone system

echo "========================================"
echo "EEG-Drone System Restart"
echo "========================================"
echo ""

# Kill any running Python processes
echo "1. Stopping any running processes..."
sudo killall python3 2>/dev/null
sleep 2

# Clean up MindWave connection
echo "2. Reconnecting MindWave..."
if [ -e /dev/rfcomm0 ]; then
    sudo rfcomm release /dev/rfcomm0 2>/dev/null
fi

# Re-bind MindWave (update MAC address if needed)
MINDWAVE_MAC="74:E5:43:XX:XX:XX"  # CHANGE THIS TO YOUR MAC!
sudo rfcomm bind /dev/rfcomm0 $MINDWAVE_MAC 1
sudo chmod 666 /dev/rfcomm0

if [ -e /dev/rfcomm0 ]; then
    echo "   ✓ MindWave reconnected"
else
    echo "   ✗ MindWave connection failed"
    echo "   Run: ~/connect_mindwave.sh"
fi

echo ""
echo "3. Waiting for Tello to reset (5 seconds)..."
sleep 5

echo ""
echo "========================================"
echo "System ready! You can now run:"
echo "  python3 main.py"
echo "========================================"
echo ""
echo "TIP: If Tello still times out, power cycle it:"
echo "  1. Hold power button to turn off"
echo "  2. Wait 5 seconds"
echo "  3. Power back on"
echo ""
