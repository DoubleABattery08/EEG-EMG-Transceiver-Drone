#!/bin/bash
# Simple MindWave reconnect - run with: bash reconnect_simple.sh

# Change this to YOUR MindWave MAC address!
MINDWAVE_MAC="74:E5:43:XX:XX:XX"

echo "Stopping Python..."
killall python3 2>/dev/null
sleep 2

echo "Releasing /dev/rfcomm0..."
rfcomm release /dev/rfcomm0 2>/dev/null
sleep 1

echo "Rebinding MindWave..."
rfcomm bind /dev/rfcomm0 $MINDWAVE_MAC 1

if [ -e /dev/rfcomm0 ]; then
    echo "Success! /dev/rfcomm0 is ready"
    ls -l /dev/rfcomm0
else
    echo "Failed. Try running as root:"
    echo "  su -"
    echo "  bash reconnect_simple.sh"
fi
