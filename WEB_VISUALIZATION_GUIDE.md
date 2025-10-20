# Web Visualization Guide - Real-time EEG Dashboard

Your system now includes a **real-time web dashboard** that broadcasts EEG brain wave data to any device on your local network!

---

## 🌐 What's New?

### Real-time Web Dashboard Features:

✅ **Live Brain Wave Graphs**
- Delta (δ) - Deep sleep waves (0.5-3 Hz)
- Theta (θ) - Drowsiness/meditation (4-7 Hz)
- Alpha (α) - Relaxed awareness (8-12 Hz)
- Beta (β) - Active thinking (13-30 Hz)
- Gamma (γ) - High-level processing (30+ Hz)

✅ **Cognitive Metrics**
- Attention level (0-100)
- Meditation level (0-100)
- Signal quality monitoring

✅ **Multi-Device Access**
- View on any phone, tablet, or computer
- Access from anywhere on the same WiFi network
- Beautiful, responsive design

✅ **Real-time Updates**
- 10 updates per second by default
- Smooth animated graphs
- No page refresh needed

---

## 🚀 Quick Start

### Step 1: Install New Dependencies

```bash
pip3 install flask flask-socketio flask-cors python-socketio
```

### Step 2: Enable Web Server (Already Enabled by Default)

In `config.py`, web server is enabled:
```python
ENABLE_WEB_SERVER = True
WEB_HOST = '0.0.0.0'  # Listen on all network interfaces
WEB_PORT = 5000
```

### Step 3: Run the System

**Option A: Full system (with drone)**
```bash
python3 main.py
```

**Option B: EEG visualization only (no drone)**
```bash
python3 web_server.py
```

### Step 4: Access the Dashboard

When the system starts, you'll see:
```
Starting web visualization server...
Web dashboard available at http://0.0.0.0:5000
Access from other devices: http://<raspberry-pi-ip>:5000
```

**On the Raspberry Pi:**
- Open browser → `http://localhost:5000`

**From another device (phone, tablet, laptop):**
1. Connect to the same WiFi network as the Raspberry Pi
2. Find Pi's IP address (see below)
3. Open browser → `http://192.168.1.XXX:5000`

---

## 📱 How to Find Your Raspberry Pi's IP Address

### Method 1: On the Raspberry Pi

```bash
hostname -I
# Output: 192.168.1.123 (example)
```

### Method 2: From Router

- Log into your router admin page
- Look for connected devices
- Find "raspberrypi" or "drone"

### Method 3: Network Scan (from Windows)

```bash
# If you have nmap installed
nmap -sn 192.168.1.0/24 | grep -B 2 "Raspberry"
```

---

## 🎨 Using the Dashboard

### Dashboard Layout:

**1. Connection Status** (top-right)
- Green = Connected to EEG server
- Red = Disconnected

**2. Status Bar** (top section)
- **Signal Quality**: 0 = perfect, 200 = no contact
  - Green (0-50) = Good signal
  - Yellow (50-100) = Fair signal
  - Red (100-200) = Poor/no signal
- **Attention**: Focus level (0-100)
- **Meditation**: Relaxation level (0-100)

**3. Metric Cards** (middle section)
- Real-time values for all brain wave bands
- Large, easy-to-read numbers
- Updates 10x per second

**4. Live Graphs** (bottom section)
- **Brain Wave Bands**: All major waves on one chart
- **Alpha Detail**: Low & high alpha separation
- **Beta Detail**: Low & high beta separation
- **Attention & Meditation**: Cognitive metrics over time

### What to Watch For:

**🧘 Relaxation/Meditation:**
- High alpha waves (eyes closed, relaxed)
- High meditation score

**🎯 Focus/Concentration:**
- High beta waves (active thinking)
- High attention score

**😴 Drowsiness:**
- High theta waves
- Low attention score

**⚡ High Activity:**
- High gamma waves
- Mixed beta/gamma

---

## 🔧 Configuration Options

### In `config.py`:

```python
# Enable/disable web server
ENABLE_WEB_SERVER = True  # Set False to disable

# Network settings
WEB_HOST = '0.0.0.0'  # 0.0.0.0 = all interfaces, localhost = local only
WEB_PORT = 5000  # Change if port 5000 is in use

# Update rate
WEB_UPDATE_RATE = 10  # Updates per second (1-30)
```

### Common Scenarios:

**1. Faster Updates (smoother graphs)**
```python
WEB_UPDATE_RATE = 20  # 20 updates/second
```

**2. Different Port**
```python
WEB_PORT = 8080  # Use port 8080 instead
```

**3. Local Only (no network access)**
```python
WEB_HOST = 'localhost'  # Only accessible from Raspberry Pi
```

**4. Disable Web Server**
```python
ENABLE_WEB_SERVER = False
```

---

## 🌐 Network Access Examples

### Scenario 1: Raspberry Pi + Phone

1. **Pi:** Connected to home WiFi (192.168.1.100)
2. **Phone:** Connected to same WiFi
3. **Access:** Open phone browser → `http://192.168.1.100:5000`

### Scenario 2: Multiple Viewers

- **Laptop:** `http://192.168.1.100:5000`
- **Tablet:** `http://192.168.1.100:5000`
- **Desktop:** `http://192.168.1.100:5000`

All devices see the same real-time data simultaneously!

### Scenario 3: Raspberry Pi Standalone (No Drone)

Just want to visualize EEG without flying?

```bash
# Run web server only (no drone control)
python3 web_server.py
```

---

## 🔍 Troubleshooting

### Issue: Can't access dashboard from other devices

**Solution 1: Check firewall**
```bash
# On Raspberry Pi, allow port 5000
sudo ufw allow 5000
# Or disable firewall temporarily for testing
sudo ufw disable
```

**Solution 2: Verify network**
```bash
# On Raspberry Pi
hostname -I  # Get IP address
ping <phone-ip>  # Test connectivity to other device
```

**Solution 3: Check web server is running**
```bash
# Should see web server startup message in logs
# Look for: "Starting web visualization server..."
```

### Issue: "Connection refused" error

**Check if port is in use:**
```bash
sudo netstat -tulpn | grep 5000
```

**Change port in config.py:**
```python
WEB_PORT = 8080  # Try different port
```

### Issue: Dashboard shows "Disconnected"

**Possible causes:**
1. EEG headset not connected
2. Web server crashed
3. Browser cache issue (try Ctrl+F5)

**Check logs:**
```bash
tail -f eeg_drone_control.log
```

### Issue: Graphs not updating

**Refresh the page:**
- Press `Ctrl+F5` (force reload)

**Check MindWave connection:**
```bash
# Signal quality should be < 50
# Alpha values should be changing
```

### Issue: Slow/laggy updates

**Reduce update rate:**
```python
# In config.py
WEB_UPDATE_RATE = 5  # Slower updates, less CPU
```

**Check CPU usage on Pi:**
```bash
top
# If Python is using >80% CPU, reduce update rate
```

---

## 📊 Understanding the Graphs

### Brain Wave Bands Explained:

**Delta (0.5-3 Hz)**
- Deep, dreamless sleep
- Healing and regeneration
- Usually very low when awake

**Theta (4-7 Hz)**
- Light sleep, drowsiness
- Deep meditation
- Creativity and intuition

**Alpha (8-12 Hz)**
- Relaxed, calm awareness
- Eyes closed, not sleeping
- **Used to control forward/backward drone movement**

**Beta (13-30 Hz)**
- Active thinking, concentration
- Alert, focused attention
- Problem solving

**Gamma (30+ Hz)**
- High-level information processing
- Peak focus
- Complex cognitive tasks

### eSense Metrics:

**Attention (0-100)**
- How focused you are
- **Controls drone rotation (theta)**
- Higher = better focus

**Meditation (0-100)**
- How calm/relaxed you are
- **Controls drone height (z)**
- Higher = deeper relaxation

---

## 🎬 Use Cases

### 1. Training & Calibration

Monitor your EEG patterns to understand your baseline:
- Watch alpha levels when relaxed
- See attention peaks when focusing
- Calibrate `ALPHA_MIN/MAX` in config

### 2. Multi-Person Demonstrations

Show EEG data to audience while flying:
- Wear headset and fly drone
- Audience watches dashboard on big screen
- See brain → drone control in real-time

### 3. Research & Data Collection

Monitor EEG during experiments:
- Leave dashboard open while testing
- Take screenshots of interesting patterns
- Log data for analysis

### 4. Biofeedback Training

Practice controlling brain states:
- Try to increase alpha (relax)
- Try to increase attention (focus)
- See immediate feedback on graphs

---

## 🔐 Security Notes

⚠️ **Important:**
- Web server is NOT password protected
- Anyone on your network can access it
- Don't expose to public internet

**For public demos:**
1. Use separate WiFi network
2. Only allow trusted devices
3. Consider adding authentication (advanced)

---

## 📱 Mobile-Friendly Design

The dashboard is fully responsive:
- ✅ Works on phones (portrait/landscape)
- ✅ Works on tablets
- ✅ Works on desktops
- ✅ Adapts to screen size automatically

---

## 🎯 Tips for Best Results

**1. Good Signal Quality**
- Keep signal < 50 for accurate data
- Clean headset sensor regularly
- Ensure good forehead contact

**2. Stable WiFi**
- Keep devices on same 2.4GHz or 5GHz band
- Reduce WiFi interference
- Pi should be close to router

**3. Browser Compatibility**
- Chrome/Edge: ✅ Excellent
- Firefox: ✅ Good
- Safari: ✅ Good
- Mobile browsers: ✅ Good

**4. Performance**
- Close other browser tabs
- Reduce update rate if laggy
- Use wired ethernet on Pi if possible

---

## 🚀 Advanced: Run Web Server Standalone

Want to visualize EEG without drone control?

### Create standalone script:

```bash
nano ~/eeg_visualizer.sh
```

Add:
```bash
#!/bin/bash
echo "Starting EEG Web Visualizer..."
python3 /home/pi/EEG-EMG-Transceiver-Drone-1/web_server.py
```

Make executable:
```bash
chmod +x ~/eeg_visualizer.sh
```

Run:
```bash
~/eeg_visualizer.sh
```

Now you have EEG visualization without needing the Tello drone!

---

## 📈 What's Being Displayed

Every 0.1 seconds (10 Hz), the dashboard receives:

```javascript
{
  "delta": 12345,
  "theta": 23456,
  "low_alpha": 34567,
  "high_alpha": 45678,
  "alpha": 40122,  // Average of low+high
  "low_beta": 56789,
  "high_beta": 67890,
  "low_gamma": 78901,
  "mid_gamma": 89012,
  "attention": 65,
  "meditation": 42,
  "signal_quality": 15,
  "raw_value": -123
}
```

All values update in real-time!

---

## 🎉 Ready to Visualize!

### Quick Start Commands:

```bash
# Full system (EEG + Drone + Web)
python3 main.py

# EEG visualization only
python3 web_server.py

# View config
python3 config.py

# Find Pi IP
hostname -I
```

### Access Dashboard:

- **On Pi:** http://localhost:5000
- **On network:** http://[PI-IP]:5000

Enjoy your real-time brain wave visualization! 🧠📊✨
