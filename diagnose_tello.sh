#!/bin/bash
# Tello Connection Diagnostic Script

echo "======================================"
echo "Tello Connection Diagnostics"
echo "======================================"
echo ""

echo "1. Checking WiFi connection..."
WIFI_SSID=$(iwgetid -r)
echo "   Connected to: $WIFI_SSID"

if [[ $WIFI_SSID == TELLO* ]]; then
    echo "   ✓ Connected to Tello WiFi"
else
    echo "   ✗ NOT connected to Tello WiFi!"
    echo "   Run: sudo nmcli device wifi connect TELLO-XXXXXX"
    exit 1
fi

echo ""
echo "2. Testing ping to Tello..."
if ping -c 2 -W 2 192.168.10.1 > /dev/null 2>&1; then
    echo "   ✓ Can ping Tello (192.168.10.1)"
else
    echo "   ✗ Cannot ping Tello"
    echo "   Make sure Tello is powered on"
    exit 1
fi

echo ""
echo "3. Checking if port 8889 is open..."
if sudo netstat -tulpn | grep -q ":8889"; then
    echo "   ⚠ Port 8889 is already in use:"
    sudo netstat -tulpn | grep ":8889"
    echo "   Kill the process: sudo killall python3"
else
    echo "   ✓ Port 8889 is available"
fi

echo ""
echo "4. Checking firewall status..."
if sudo ufw status | grep -q "Status: active"; then
    echo "   ⚠ Firewall is active"
    if sudo ufw status | grep -q "8889.*ALLOW"; then
        echo "   ✓ Port 8889 is allowed"
    else
        echo "   ✗ Port 8889 is NOT allowed"
        echo "   Run: sudo ufw allow 8889/udp"
    fi
else
    echo "   ✓ Firewall is inactive"
fi

echo ""
echo "5. Testing raw UDP communication..."
echo "   Sending 'command' to Tello..."

# Send UDP packet and wait for response
RESPONSE=$(echo -n "command" | timeout 3 nc -u -w 1 192.168.10.1 8889 2>&1)

if [[ $RESPONSE == *"ok"* ]]; then
    echo "   ✓ Tello responded: $RESPONSE"
    echo ""
    echo "======================================"
    echo "All checks passed! Tello is ready."
    echo "You can run: python3 main.py"
    echo "======================================"
else
    echo "   ✗ Tello did not respond"
    echo "   Response: $RESPONSE"
    echo ""
    echo "======================================"
    echo "Troubleshooting steps:"
    echo "1. Power cycle Tello (off 5 sec, then on)"
    echo "2. Reconnect to Tello WiFi"
    echo "3. Wait 10 seconds after WiFi connects"
    echo "4. Disable firewall: sudo ufw disable"
    echo "5. Try again"
    echo "======================================"
fi
