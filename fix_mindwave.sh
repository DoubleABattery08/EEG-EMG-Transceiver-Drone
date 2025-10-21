#!/bin/bash
# Fix MindWave Connection Issues

echo "======================================"
echo "MindWave Connection Fix Script"
echo "======================================"
echo ""

# CHANGE THIS TO YOUR MINDWAVE MAC ADDRESS!
MINDWAVE_MAC="74:E5:43:XX:XX:XX"

echo "1. Stopping any processes using the serial port..."
sudo killall python3 2>/dev/null
sleep 2

echo ""
echo "2. Checking if anything is using /dev/rfcomm0..."
if sudo lsof /dev/rfcomm0 2>/dev/null; then
    echo "   ⚠ Process found using /dev/rfcomm0, killing it..."
    sudo lsof -t /dev/rfcomm0 | xargs -r sudo kill -9
    sleep 1
else
    echo "   ✓ No processes using /dev/rfcomm0"
fi

echo ""
echo "3. Releasing existing rfcomm binding..."
sudo rfcomm release /dev/rfcomm0 2>/dev/null
sleep 1

echo ""
echo "4. Restarting Bluetooth service..."
sudo systemctl restart bluetooth
sleep 3

echo ""
echo "5. Checking if MindWave is powered on..."
if bluetoothctl info $MINDWAVE_MAC 2>/dev/null | grep -q "Connected: yes"; then
    echo "   ✓ MindWave is connected via Bluetooth"
else
    echo "   ⚠ MindWave may not be connected"
    echo "   Make sure headset is powered ON (LED blinking)"
fi

echo ""
echo "6. Binding MindWave to /dev/rfcomm0..."
sudo rfcomm bind /dev/rfcomm0 $MINDWAVE_MAC 1

if [ $? -eq 0 ]; then
    echo "   ✓ Bound successfully"
else
    echo "   ✗ Binding failed"
    echo "   Check that MAC address is correct: $MINDWAVE_MAC"
    exit 1
fi

echo ""
echo "7. Setting permissions..."
sudo chmod 666 /dev/rfcomm0

echo ""
echo "8. Verifying /dev/rfcomm0 exists..."
if [ -e /dev/rfcomm0 ]; then
    echo "   ✓ /dev/rfcomm0 exists"
    ls -l /dev/rfcomm0
else
    echo "   ✗ /dev/rfcomm0 does not exist"
    exit 1
fi

echo ""
echo "======================================"
echo "MindWave should be ready!"
echo ""
echo "Test it with:"
echo "  python3 eeg_interface.py"
echo ""
echo "Then run:"
echo "  python3 main.py"
echo "======================================"
