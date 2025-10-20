# Raspberry Pi Setup Guide - MindWave Mobile 2

Complete guide for setting up MindWave Mobile 2 EEG headset on Raspberry Pi via Bluetooth.

---

## Part 1: Raspberry Pi Preparation

### Step 1: Update Your Raspberry Pi

```bash
sudo apt-get update
sudo apt-get upgrade -y
```

### Step 2: Install Bluetooth Tools

```bash
sudo apt-get install -y bluetooth bluez bluez-tools rfcomm
sudo apt-get install -y python3-pip python3-serial
```

### Step 3: Install Python Dependencies

```bash
cd ~/EEG-EMG-Transceiver-Drone-1
pip3 install -r requirements.txt
```

### Step 4: Enable Bluetooth Service

```bash
sudo systemctl start bluetooth
sudo systemctl enable bluetooth
sudo systemctl status bluetooth
```

You should see `active (running)` in green.

---

## Part 2: Pair MindWave Mobile 2 Headset

### Step 1: Turn On Your Headset

- Power on the MindWave Mobile 2
- LED should blink blue (pairing mode)

### Step 2: Scan for the Headset

```bash
sudo bluetoothctl
```

This opens the Bluetooth control interface. You'll see a `[bluetooth]#` prompt.

Now run these commands one by one:

```bash
power on
agent on
default-agent
scan on
```

### Step 3: Find Your Headset

Watch for output like:
```
[NEW] Device 74:E5:43:XX:XX:XX MindWave Mobile
```

**Write down the MAC address** (the part like `74:E5:43:XX:XX:XX`)

Once you see it, stop scanning:
```bash
scan off
```

### Step 4: Pair and Trust the Device

Replace `XX:XX:XX:XX:XX:XX` with your actual MAC address:

```bash
pair 74:E5:43:XX:XX:XX
```

Wait for "Pairing successful"

```bash
trust 74:E5:43:XX:XX:XX
```

You should see "Changing XX:XX:XX:XX:XX:XX trust succeeded"

```bash
exit
```

---

## Part 3: Create Serial Port Connection

### Method A: Manual Binding (Test First)

This creates the serial port temporarily (resets on reboot):

```bash
sudo rfcomm bind /dev/rfcomm0 74:E5:43:XX:XX:XX 1
```

Replace `74:E5:43:XX:XX:XX` with your MindWave's MAC address.

**Verify it worked:**
```bash
ls -l /dev/rfcomm0
```

You should see the device listed.

**Set permissions:**
```bash
sudo chmod 666 /dev/rfcomm0
```

### Method B: Automatic Binding (Permanent Setup)

To make the connection automatic on every boot:

1. **Edit the rfcomm configuration file:**

```bash
sudo nano /etc/bluetooth/rfcomm.conf
```

2. **Add this configuration** (replace MAC address with yours):

```
rfcomm0 {
    bind yes;
    device 74:E5:43:XX:XX:XX;
    channel 1;
    comment "MindWave Mobile 2";
}
```

3. **Save and exit:**
   - Press `Ctrl+X`
   - Press `Y`
   - Press `Enter`

4. **Enable rfcomm service:**

```bash
sudo systemctl enable rfcomm
sudo systemctl start rfcomm
```

5. **Set permissions permanently:**

Create a udev rule:
```bash
sudo nano /etc/udev/rules.d/99-rfcomm.rules
```

Add this line:
```
KERNEL=="rfcomm[0-9]*", MODE="0666"
```

Save and exit (`Ctrl+X`, `Y`, `Enter`)

Reload udev:
```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
```

---

## Part 4: Test MindWave Connection

### Step 1: Verify Serial Port

```bash
ls -l /dev/rfcomm0
```

Should show the device with `rw-rw-rw-` permissions.

### Step 2: Put On Headset

- Place sensor on forehead
- Clip ear reference on earlobe
- Make sure it has good contact

### Step 3: Run Test Script

```bash
cd ~/EEG-EMG-Transceiver-Drone-1
python3 eeg_interface.py
```

### What You Should See:

```
Connecting to MindWave on /dev/rfcomm0 at 57600 baud...
MindWave connected successfully
Starting MindWave read loop...
Reading EEG data (Press Ctrl+C to stop)...
Signal:   0 | Alpha:   245678 | Attention:  65 | Meditation:  42
```

**Signal Quality Guide:**
- **0-50**: Good signal (ready to use)
- **50-100**: Fair signal (adjust headset)
- **100-200**: Poor/no signal (no contact)

Press `Ctrl+C` to stop.

---

## Part 5: Troubleshooting

### Issue: "Permission denied" on /dev/rfcomm0

**Solution:**
```bash
sudo chmod 666 /dev/rfcomm0
# OR add your user to dialout group:
sudo usermod -a -G dialout $USER
# Then logout and login again
```

### Issue: "Failed to connect" or "No such file or directory"

**Solution 1 - Check if device is bound:**
```bash
ls /dev/rfcomm*
```

If nothing shows up:
```bash
sudo rfcomm bind /dev/rfcomm0 74:E5:43:XX:XX:XX 1
```

**Solution 2 - Check Bluetooth service:**
```bash
sudo systemctl status bluetooth
```

Should be `active (running)`. If not:
```bash
sudo systemctl start bluetooth
```

**Solution 3 - Reconnect manually:**
```bash
sudo bluetoothctl
connect 74:E5:43:XX:XX:XX
exit
sudo rfcomm bind /dev/rfcomm0 74:E5:43:XX:XX:XX 1
```

### Issue: Signal quality always 200 (no contact)

**Solutions:**
1. Clean the sensor arm with rubbing alcohol
2. Moisten the sensor slightly with water or saline
3. Ensure firm contact with center of forehead
4. Make sure ear clip is on earlobe
5. Check headset battery (replace if low)
6. Try repositioning the headset

### Issue: rfcomm bind fails with "Address already in use"

**Solution:**
```bash
# Release the binding first
sudo rfcomm release /dev/rfcomm0
# Then bind again
sudo rfcomm bind /dev/rfcomm0 74:E5:43:XX:XX:XX 1
```

### Issue: Headset won't pair

**Solutions:**

1. **Reset Bluetooth:**
```bash
sudo systemctl restart bluetooth
```

2. **Remove old pairing:**
```bash
sudo bluetoothctl
remove 74:E5:43:XX:XX:XX
scan on
# Wait for device to appear
pair 74:E5:43:XX:XX:XX
trust 74:E5:43:XX:XX:XX
exit
```

3. **Reset MindWave headset:**
   - Turn off headset
   - Wait 10 seconds
   - Turn on again
   - Should blink blue in pairing mode

### Issue: Python can't find serial module

**Solution:**
```bash
pip3 install pyserial --user
# OR system-wide:
sudo pip3 install pyserial
```

---

## Part 6: Auto-Connect on Boot (Optional)

To automatically connect the headset when Raspberry Pi boots:

### Create systemd service:

```bash
sudo nano /etc/systemd/system/mindwave-connect.service
```

**Add this content** (replace MAC address):

```ini
[Unit]
Description=MindWave Mobile 2 Bluetooth Connection
After=bluetooth.service
Requires=bluetooth.service

[Service]
Type=oneshot
ExecStartPre=/bin/sleep 5
ExecStart=/usr/bin/rfcomm bind /dev/rfcomm0 74:E5:43:XX:XX:XX 1
ExecStartPost=/bin/chmod 666 /dev/rfcomm0
RemainAfterExit=yes
ExecStop=/usr/bin/rfcomm release /dev/rfcomm0

[Install]
WantedBy=multi-user.target
```

**Enable and start:**

```bash
sudo systemctl enable mindwave-connect.service
sudo systemctl start mindwave-connect.service
```

**Check status:**
```bash
sudo systemctl status mindwave-connect.service
```

---

## Part 7: Connect to Tello Drone (WiFi)

### Important: WiFi Adapter Setup

Your Raspberry Pi needs **TWO WiFi connections**:
1. **Built-in WiFi**: Connect to Tello drone
2. **USB WiFi adapter** (optional): For internet/SSH access

**OR** use Ethernet for internet and built-in WiFi for Tello.

### Step 1: Connect to Tello WiFi

```bash
# List available networks
sudo iwlist wlan0 scan | grep TELLO

# Connect to Tello
sudo nmcli device wifi connect TELLO-XXXXXX
```

Replace `TELLO-XXXXXX` with your drone's actual WiFi name.

### Step 2: Verify Connection

```bash
ping -c 4 192.168.10.1
```

You should see 0% packet loss.

### Step 3: Test Tello

```bash
cd ~/EEG-EMG-Transceiver-Drone-1
python3 tello_controller.py
```

Should show battery level and "Tello connected successfully"

---

## Part 8: Run Complete System

### Pre-flight Checklist:

- [ ] MindWave headset paired and bound to /dev/rfcomm0
- [ ] Signal quality < 50 when wearing headset
- [ ] Tello battery > 50%
- [ ] Connected to Tello WiFi
- [ ] In open area (3m x 3m minimum)

### Run the system:

```bash
cd ~/EEG-EMG-Transceiver-Drone-1
python3 main.py
```

**Emergency stop:** Press `Ctrl+C`

---

## Quick Command Reference

### Bluetooth Commands:
```bash
# Check Bluetooth status
sudo systemctl status bluetooth

# Start Bluetooth
sudo systemctl start bluetooth

# Pair headset (interactive)
sudo bluetoothctl

# Bind serial port
sudo rfcomm bind /dev/rfcomm0 74:E5:43:XX:XX:XX 1

# Check serial port
ls -l /dev/rfcomm0

# Set permissions
sudo chmod 666 /dev/rfcomm0

# Release binding
sudo rfcomm release /dev/rfcomm0
```

### Testing Commands:
```bash
# Test MindWave
python3 eeg_interface.py

# Test Tello
python3 tello_controller.py

# Run full system
python3 main.py
```

### WiFi Commands:
```bash
# Scan for Tello
sudo iwlist wlan0 scan | grep TELLO

# Connect to Tello
sudo nmcli device wifi connect TELLO-XXXXXX

# Check connection
ping 192.168.10.1
```

---

## Script for Easy Setup

Create a helper script to connect everything:

```bash
nano ~/connect-mindwave.sh
```

**Add this content** (replace MAC address):

```bash
#!/bin/bash

echo "Connecting MindWave Mobile 2..."

# Release any existing binding
sudo rfcomm release /dev/rfcomm0 2>/dev/null

# Bind to serial port
sudo rfcomm bind /dev/rfcomm0 74:E5:43:XX:XX:XX 1

# Set permissions
sudo chmod 666 /dev/rfcomm0

# Check if successful
if [ -e /dev/rfcomm0 ]; then
    echo "✓ MindWave connected successfully at /dev/rfcomm0"
    ls -l /dev/rfcomm0
else
    echo "✗ Failed to connect MindWave"
    exit 1
fi
```

**Make executable:**
```bash
chmod +x ~/connect-mindwave.sh
```

**Use it:**
```bash
~/connect-mindwave.sh
```

---

## Startup Script

To run the drone system automatically on boot:

```bash
sudo nano /etc/systemd/system/eeg-drone.service
```

**Add:**

```ini
[Unit]
Description=EEG Drone Control System
After=network.target bluetooth.service mindwave-connect.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/EEG-EMG-Transceiver-Drone-1
ExecStart=/usr/bin/python3 /home/pi/EEG-EMG-Transceiver-Drone-1/main.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

**Note:** Only enable this after you've tested everything thoroughly!

---

## Performance Tips for Raspberry Pi

### 1. Use Raspberry Pi 4 or newer
- Recommended: Pi 4 (2GB+ RAM)
- Minimum: Pi 3B+

### 2. Optimize Python
```bash
# Install optimized numpy
sudo apt-get install python3-numpy

# Use Python 3.9 or newer
python3 --version
```

### 3. Reduce logging for better performance

In `config.py`:
```python
LOG_LEVEL = 'WARNING'  # Instead of 'INFO'
```

### 4. Increase swap (if using Pi 3)
```bash
sudo nano /etc/dphys-swapfile
# Change CONF_SWAPSIZE=100 to CONF_SWAPSIZE=512
sudo /etc/init.d/dphys-swapfile restart
```

---

## Common Raspberry Pi Issues

### Issue: Bluetooth not working after reboot

**Solution:**
```bash
sudo systemctl enable bluetooth
sudo systemctl start bluetooth
~/connect-mindwave.sh
```

### Issue: Can't SSH after connecting to Tello WiFi

**Solution:** Use a second WiFi adapter or Ethernet for SSH access, as Tello WiFi has no internet.

### Issue: Python script runs slow

**Solution:**
- Use Raspberry Pi 4
- Install numpy via apt instead of pip:
  ```bash
  sudo apt-get install python3-numpy
  ```

### Issue: /dev/rfcomm0 disappears after reboot

**Solution:** Use the systemd service or add to rc.local:
```bash
sudo nano /etc/rc.local
# Add before "exit 0":
rfcomm bind /dev/rfcomm0 74:E5:43:XX:XX:XX 1
chmod 666 /dev/rfcomm0
```

---

## Your MindWave MAC Address

**Remember to replace `74:E5:43:XX:XX:XX` with YOUR actual MAC address in all commands above!**

Find it using:
```bash
sudo bluetoothctl
scan on
# Look for "MindWave Mobile"
```

---

## Ready to Fly!

Once everything is working:

1. ✓ MindWave connected (`python3 eeg_interface.py` shows good signal)
2. ✓ Tello connected (`python3 tello_controller.py` shows battery)
3. ✓ In safe flying area

Run:
```bash
python3 main.py
```

**Emergency stop:** `Ctrl+C` anytime!
