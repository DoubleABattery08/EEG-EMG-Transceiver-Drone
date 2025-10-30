# EEG-Controlled Tello Drone System

Control a DJI Tello drone using brain waves (alpha activity) from a MindWave Mobile 2 EEG headset, mapped to cylindrical coordinates for 3D flight control.

## System Overview

This system integrates:
- **MindWave Mobile 2 EEG headset** (Bluetooth) for brain wave detection
- **DJI Tello drone** (WiFi) for flight control
- **Raspberry Pi** (or any Linux/Windows computer) as the control hub

### Cylindrical Coordinate Mapping

The system uses 3 degrees of freedom in cylindrical coordinates (r, θ, z):

- **r (radius)**: Controlled by **alpha wave power** → Forward/backward movement
- **θ (theta/angle)**: Controlled by **attention level** → Rotation/yaw
- **z (height)**: Controlled by **meditation level** → Up/down movement

## Hardware Setup

### 1. MindWave Mobile 2 Setup (Bluetooth)

**On Raspberry Pi/Linux:**
```bash
# Install Bluetooth tools
sudo apt-get install bluetooth bluez bluez-tools rfcomm

# Find your MindWave device
bluetoothctl
scan on
# Look for "MindWave Mobile" and note its MAC address (e.g., 74:E5:43:XX:XX:XX)

# Pair the device
pair 74:E5:43:XX:XX:XX
trust 74:E5:43:XX:XX:XX

# Bind to serial port
sudo rfcomm bind /dev/rfcomm0 74:E5:43:XX:XX:XX 1

# Make it permanent (optional)
echo "rfcomm0 {
    bind yes;
    device 74:E5:43:XX:XX:XX;
    channel 1;
}" | sudo tee -a /etc/bluetooth/rfcomm.conf
```

**On Windows:**
1. Pair MindWave via Bluetooth settings
2. Open Device Manager → Ports (COM & LPT)
3. Find "Standard Serial over Bluetooth link" and note the COM port (e.g., COM3)
4. Update `config.py` with the correct COM port

### 2. Tello Drone Setup (WiFi)

**Connect to Tello WiFi:**
1. Power on the Tello drone
2. Connect your Raspberry Pi/computer to the Tello's WiFi network
   - Network name: `TELLO-XXXXXX`
3. The drone's IP address is always `192.168.10.1`

**Note:** You cannot be connected to both Tello WiFi and another WiFi network simultaneously. If you need internet access, use a second WiFi adapter or Ethernet connection.

## Software Installation

### Prerequisites
```bash
# Python 3.7 or higher
python3 --version

# Install pip if needed
sudo apt-get install python3-pip
```

### Install Dependencies
```bash
# Navigate to project directory
cd EEG-EMG-Transceiver-Drone-3

# Install required packages
pip3 install -r requirements.txt
```

## Configuration

Edit `config.py` to adjust system parameters:

### Key Settings to Adjust:

```python
# EEG port (adjust for your system)
EEG_PORT = '/dev/rfcomm0'  # Linux
# EEG_PORT = 'COM3'        # Windows

# Alpha wave range (calibrate based on your readings)
ALPHA_MIN = 0
ALPHA_MAX = 1000000  # Adjust after testing

# Control sensitivity
SMOOTHING_FACTOR = 0.7  # Higher = smoother, slower response

# Safety settings
MIN_BATTERY_LEVEL = 20
AUTO_TAKEOFF = False
```

## Usage

### 1. Test Individual Components

**Test EEG Headset:**
```bash
python3 eeg_interface.py
```
Put on the headset and ensure you see signal quality < 50 and changing alpha values.

**Test Tello Connection:**
```bash
# Make sure you're connected to Tello WiFi first
python3 tello_controller.py
```

**Test Coordinate Mapper:**
```bash
python3 coordinate_mapper.py
```

### 2. Run the Main System

```bash
python3 main.py
```

### Control Flow:
1. System initializes EEG headset and Tello drone
2. Checks battery level (must be > 20%)
3. If `AUTO_TAKEOFF = True`, drone takes off automatically
4. EEG data continuously controls the drone:
   - **High alpha** → Move forward
   - **Low alpha** → Move backward
   - **High attention** → Rotate right
   - **Low attention** → Rotate left
   - **High meditation** → Move up
   - **Low meditation** → Move down
5. Press `Ctrl+C` to land and stop

## How to Control the Drone

### Understanding EEG Metrics:

1. **Alpha Waves**: Relaxed, calm state with eyes closed
   - Close your eyes and relax → More forward movement
   - Open your eyes and focus → Less forward movement

2. **Attention**: Focused mental state
   - Focus on a task → Higher attention → Rotate right
   - Relax your focus → Lower attention → Rotate left

3. **Meditation**: Calm, meditative state
   - Deep relaxation → Higher meditation → Move up
   - Alert state → Lower meditation → Move down

### Tips for Better Control:

- **Calibration**: Run the system for 30 seconds to understand your baseline values
- **Signal Quality**: Ensure the headset electrode is making good contact (signal quality < 50)
- **Practice**: Start with `SMOOTHING_FACTOR = 0.9` for very smooth, slow movements
- **Deadzones**: Adjust `R_DEADZONE`, `THETA_DEADZONE`, `Z_DEADZONE` to prevent drift

## Safety Features

- **Minimum battery check**: Won't fly if battery < 20%
- **Emergency stop**: Press `Ctrl+C` to land immediately
- **Auto-land**: Lands automatically on poor signal quality
- **Deadzones**: Prevent unintended drift
- **Velocity limits**: Maximum velocities clamped to safe ranges

## Troubleshooting

### EEG Headset Issues:

**Problem**: Cannot connect to MindWave
- Check Bluetooth pairing
- Verify correct port in `config.py`
- Check permissions: `sudo chmod 666 /dev/rfcomm0`
- Try re-binding: `sudo rfcomm bind /dev/rfcomm0 <MAC_ADDRESS>`

**Problem**: Poor signal quality
- Ensure electrode is touching your forehead
- Clean the electrode with rubbing alcohol
- Moisten the electrode slightly with water
- Adjust headset position

### Tello Drone Issues:

**Problem**: Cannot connect to Tello
- Verify WiFi connection to Tello network
- Check IP address is `192.168.10.1`
- Restart the drone
- Check firewall settings (allow UDP ports 8889, 8890)

**Problem**: Drone doesn't respond to commands
- Check battery level
- Verify `COMMAND_INTERVAL` is not too short
- Ensure you're in range (< 10 meters)
- Check for WiFi interference

### Control Issues:

**Problem**: Drone drifts or moves unexpectedly
- Increase deadzone values in `config.py`
- Increase `SMOOTHING_FACTOR`
- Calibrate `ALPHA_MIN` and `ALPHA_MAX` based on your readings

**Problem**: Drone doesn't move enough
- Decrease deadzone values
- Adjust velocity scaling
- Check alpha wave ranges are correct

## Project Structure

```
EEG-EMG-Transceiver-Drone-3/
├── main.py                    # Main control script
├── eeg_interface.py           # MindWave EEG headset interface
├── tello_controller.py        # Tello drone controller
├── coordinate_mapper.py       # Cylindrical coordinate mapper
├── config.py                  # Configuration parameters
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Advanced Customization

### Custom Coordinate Mapping:

Edit `coordinate_mapper.py` to implement custom mapping strategies:
- Different EEG metrics to coordinates
- Non-linear mappings
- Gesture detection from EEG patterns

### Alternative Control Modes:

Modify `config.py`:
```python
CONTROL_MODE = 2  # Alpha -> z, Attention -> r, Meditation -> theta
```

### Data Logging:

All EEG and drone data is logged to `eeg_drone_control.log`. Analyze this file to tune parameters.

## Safety Warning

⚠️ **IMPORTANT SAFETY NOTES:**
- Always fly in an open area away from people and obstacles
- Keep line of sight with the drone
- Be ready to use emergency stop (Ctrl+C)
- Start with low sensitivity settings
- Test in a safe environment first
- Follow local drone regulations
- Ensure proper headset contact for reliable control

## License

This project is for educational and research purposes.

## Credits

- DJI Tello SDK
- NeuroSky MindWave Mobile 2
- Python Serial library
