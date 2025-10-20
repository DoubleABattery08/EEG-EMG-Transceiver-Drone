# DETAILED SETUP GUIDE - Windows

## Part 1: Connect MindWave Mobile 2 (Bluetooth)

### Step 1: Pair the Headset

1. Turn on your MindWave Mobile 2 headset (LED should blink blue)

2. On Windows:
   - Click Start → Settings → Bluetooth & devices
   - Click "Add device" → Bluetooth
   - Wait for "MindWave Mobile" to appear
   - Click on it to pair
   - Wait for "Connected" status

### Step 2: Find the COM Port

1. Press `Win + X` → Device Manager
2. Expand "Ports (COM & LPT)"
3. Look for "Standard Serial over Bluetooth link (COMX)" where X is a number
4. **Write down this COM port number** (e.g., COM3, COM4, COM5, etc.)

### Step 3: Update Configuration

1. Open `config.py` in a text editor
2. Find the line near the bottom that says:
   ```python
   if platform.system() == 'Windows':
       Config.EEG_PORT = 'COM3'
   ```
3. Change 'COM3' to YOUR COM port number from Step 2
4. Save the file

---

## Part 2: Test MindWave Connection

### Step 1: Put on the Headset Properly

- Sensor arm should touch the middle of your forehead
- Ear clip on your earlobe
- Should feel snug but comfortable

### Step 2: Run Test Script

Open Command Prompt (cmd) or PowerShell in the project folder and run:

```bash
python eeg_interface.py
```

### What You Should See:

```
Signal: 0-50 | Alpha: XXXXXX | Attention: XX | Meditation: XX
```

**Good Signal**: Number 0-50 (0 is perfect)
**Poor Signal**: Number 100-200 (adjust headset position)

### Troubleshooting:

**If you see "Failed to connect":**
- Check Bluetooth is paired
- Verify COM port in config.py matches Device Manager
- Try unplugging/replugging Bluetooth or restarting

**If Signal Quality is always 200:**
- Clean the sensor with rubbing alcohol
- Moisten sensor slightly with water
- Ensure good contact with forehead

Press `Ctrl+C` to stop the test.

---

## Part 3: Connect to Tello Drone

### Step 1: Prepare the Drone

1. **Charge the battery** - Must be >20% (ideally >50% for testing)
2. **Insert battery** into Tello
3. **Power on** - Press power button once, then press and hold
4. Wait for **yellow LED** to blink slowly (ready for connection)

### Step 2: Connect to Tello WiFi

1. On your computer:
   - Click WiFi icon in system tray
   - Look for network named **TELLO-XXXXXX** (6 random characters)
   - Click to connect (no password needed)
   - Wait for "Connected"

2. **Verify connection:**
   - Open Command Prompt
   - Type: `ping 192.168.10.1`
   - You should see replies (0% packet loss)

**IMPORTANT**: When connected to Tello WiFi, you won't have internet access.

### Step 3: Test Tello Connection

In Command Prompt, run:

```bash
python tello_controller.py
```

### What You Should See:

```
Tello connected successfully
Battery: XX%
Speed: 10 cm/s
Testing RC control for 5 seconds...
Test complete
```

### Troubleshooting:

**If "Connection failed":**
- Verify you're connected to Tello WiFi
- Try power cycling the drone
- Check Windows Firewall isn't blocking Python
- Make sure no other program is using the Tello

Press `Ctrl+C` if needed to stop.

---

## Part 4: First Calibration Run

Before flying, let's see your EEG baseline values.

### Step 1: Run Calibration

```bash
python coordinate_mapper.py
```

This will show you test mappings. Note the values to understand the system.

### Step 2: Adjust Sensitivity (Optional)

Edit `config.py` and adjust these values based on your comfort:

```python
# Start with VERY smooth, slow control
SMOOTHING_FACTOR = 0.9  # 0.9 = very smooth, 0.3 = very responsive

# Increase deadzones to prevent drift
R_DEADZONE = 20       # Forward/backward deadzone
THETA_DEADZONE = 30   # Rotation deadzone
Z_DEADZONE = 20       # Up/down deadzone

# For first flight, disable auto-takeoff
AUTO_TAKEOFF = False
```

---

## Part 5: FIRST FLIGHT (Outdoor/Large Room)

### Safety Checklist:

- [ ] MindWave headset on and signal quality < 50
- [ ] Tello battery > 50%
- [ ] Connected to Tello WiFi
- [ ] Flying in open area (no people, pets, obstacles)
- [ ] At least 3m x 3m clear space
- [ ] You're ready to press Ctrl+C for emergency land

### Step 1: Start the System

```bash
python main.py
```

### What You Should See:

```
Initializing EEG-Drone Control System...
Initializing coordinate mapper...
Initializing MindWave EEG headset...
MindWave connected successfully
Initializing Tello drone...
Connecting to Tello drone...
Drone battery level: XX%
All systems initialized successfully
Starting EEG-Drone control loop...
Press CTRL+C to stop and land the drone
```

### Step 2: Manual Takeoff (Since AUTO_TAKEOFF = False)

The system is now running but the drone won't takeoff automatically.

**Option A: Modify main.py to add manual takeoff command**

OR

**Option B: Enable AUTO_TAKEOFF in config.py:**
- Edit `config.py`
- Set `AUTO_TAKEOFF = True`
- Save and restart `python main.py`

### Step 3: Control the Drone with Your Brain

Once airborne:

**To Move Forward:**
- Close your eyes
- Relax
- High alpha waves = forward movement

**To Move Backward:**
- Open your eyes
- Stay alert
- Low alpha waves = backward movement

**To Rotate:**
- Focus hard (attention up) = rotate right
- Relax focus (attention down) = rotate left

**To Go Up:**
- Meditate/calm state = up

**To Go Down:**
- Alert state = down

### Step 4: Emergency Stop

Press **Ctrl+C** at any time to:
- Stop all movement
- Land the drone
- Disconnect safely

---

## Part 6: Tuning for Better Control

After your first flight, adjust these in `config.py`:

### If the drone is TOO sensitive:
```python
SMOOTHING_FACTOR = 0.95  # Increase (max 0.99)
R_DEADZONE = 25          # Increase deadzones
THETA_DEADZONE = 35
Z_DEADZONE = 25
```

### If the drone is TOO slow to respond:
```python
SMOOTHING_FACTOR = 0.6   # Decrease
R_DEADZONE = 10          # Decrease deadzones
THETA_DEADZONE = 15
Z_DEADZONE = 10
```

### If you need to adjust alpha wave range:

1. Run the system and watch the log file
2. Look at your typical alpha values
3. Edit `config.py`:
```python
ALPHA_MIN = 0
ALPHA_MAX = 500000  # Adjust based on your max observed values
```

---

## Common Issues and Solutions

### Issue: Drone drifts when I'm trying to hover
**Solution**: Increase all deadzone values

### Issue: Drone doesn't respond to my brain waves
**Solution**:
- Check signal quality < 50
- Decrease smoothing factor
- Check alpha values are changing in the log

### Issue: Drone moves too erratically
**Solution**: Increase SMOOTHING_FACTOR to 0.9 or higher

### Issue: "Failed to connect to Tello"
**Solution**:
- Verify WiFi connection to TELLO-XXXXXX
- Power cycle the drone
- Check firewall settings
- Try: `python -c "import socket; s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.sendto(b'command', ('192.168.10.1', 8889)); print(s.recvfrom(1024))"`

### Issue: "Failed to connect to MindWave"
**Solution**:
- Check Bluetooth pairing
- Verify COM port in config.py
- Try different COM port
- Re-pair the device

---

## Quick Command Reference

```bash
# Test EEG headset
python eeg_interface.py

# Test Tello drone
python tello_controller.py

# Test coordinate mapping
python coordinate_mapper.py

# Run full system
python main.py

# View configuration
python config.py

# Emergency stop
Ctrl+C
```

---

## Flight Log

Check `eeg_drone_control.log` after each flight to see:
- Alpha wave values
- Attention/Meditation levels
- Commands sent to drone
- Any errors or warnings

This helps you tune the system for better control.

---

## Next Steps for Advanced Use

1. **Record your baseline**: Sit with headset for 5 minutes, note average alpha values
2. **Custom calibration**: Set ALPHA_MIN/MAX based on your personal range
3. **Different control modes**: Try CONTROL_MODE = 2 in config.py
4. **Add gestures**: Modify coordinate_mapper.py to detect patterns
5. **Data visualization**: Uncomment matplotlib in requirements.txt and add plotting

---

## Safety Reminders

⚠️ **ALWAYS:**
- Fly in open areas
- Keep drone in sight
- Have Ctrl+C ready
- Check battery before flight
- Ensure good EEG signal quality
- Start with high smoothing (0.9)
- Test in safe environment first

🚫 **NEVER:**
- Fly near people or animals
- Fly indoors on first attempt
- Fly with poor signal quality
- Fly with low battery
- Fly in windy conditions
- Leave the system unattended
