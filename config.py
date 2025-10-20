#!/usr/bin/env python3
"""
Configuration file for EEG-Drone Control System
Adjust these parameters to tune the system behavior
"""


class Config:
    """Configuration parameters for the EEG-controlled Tello drone system"""

    # ========== EEG Headset Configuration ==========
    # MindWave Mobile 2 Bluetooth connection
    # For Linux: typically '/dev/rfcomm0' (use rfcomm bind)
    # For Windows: typically 'COM3', 'COM4', etc.
    EEG_PORT = '/dev/rfcomm0'
    EEG_BAUDRATE = 57600  # Standard for MindWave

    # ========== Tello Drone Configuration ==========
    # Default Tello WiFi settings
    TELLO_IP = '192.168.10.1'
    TELLO_PORT = 8889
    TELLO_STATE_PORT = 8890
    TELLO_VIDEO_PORT = 11111

    # Safety settings
    MIN_BATTERY_LEVEL = 20  # Don't fly if battery below this percentage
    AUTO_TAKEOFF = False  # Set to True to automatically takeoff on start

    # ========== Web Visualization Server ==========
    # Enable web dashboard for real-time EEG visualization
    ENABLE_WEB_SERVER = True  # Set to False to disable web server
    WEB_HOST = '0.0.0.0'  # Listen on all network interfaces
    WEB_PORT = 5000  # Web server port
    WEB_UPDATE_RATE = 10  # Data updates per second (Hz)

    # ========== Alpha Wave Mapping Configuration ==========
    # Alpha power ranges (adjust based on your headset readings)
    # These values are typical for MindWave Mobile 2
    ALPHA_MIN = 0  # Minimum alpha power
    ALPHA_MAX = 1000000  # Maximum alpha power (adjust after testing)

    # ========== Cylindrical Coordinate Ranges ==========
    # r (radius) - controls forward/backward movement
    R_MIN = 0  # Minimum radius
    R_MAX = 100  # Maximum radius
    R_DEADZONE = 15  # Deadzone around center to prevent drift

    # theta (angle) - controls rotation/yaw
    THETA_MIN = -180  # Minimum angle (degrees)
    THETA_MAX = 180  # Maximum angle (degrees)
    THETA_DEADZONE = 20  # Deadzone around center (degrees)

    # z (height) - controls up/down movement
    Z_MIN = 0  # Minimum height
    Z_MAX = 100  # Maximum height
    Z_DEADZONE = 15  # Deadzone around center

    # ========== Velocity Mapping ==========
    # These control how aggressive the drone movements are
    # Velocity range for Tello is -100 to 100
    VELOCITY_SCALE = 1.0  # Global velocity scaling (0.0 to 1.0)

    # ========== Signal Processing ==========
    # Smoothing factor for EEG data (0-1)
    # Higher = more smoothing (slower response, less jitter)
    # Lower = less smoothing (faster response, more jitter)
    SMOOTHING_FACTOR = 0.7

    # ========== Control Loop Settings ==========
    # How often to send commands to the drone (seconds)
    COMMAND_INTERVAL = 0.05  # 20 Hz (Tello can handle up to 20 commands/sec)

    # Main loop delay (seconds)
    LOOP_DELAY = 0.05  # 20 Hz

    # ========== Signal Quality ==========
    # Minimum signal quality threshold (0 = best, 200 = no contact)
    MAX_POOR_SIGNAL = 50  # Warn if signal quality above this

    # ========== Logging ==========
    LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_FILE = 'eeg_drone_control.log'

    # ========== Advanced Mapping Options ==========
    # Control mode: how EEG metrics map to coordinates
    # Mode 1: Alpha -> r, Attention -> theta, Meditation -> z (default)
    # Mode 2: Alpha -> z, Attention -> r, Meditation -> theta
    # Mode 3: Custom mapping (modify coordinate_mapper.py)
    CONTROL_MODE = 1

    # Enable/disable specific degrees of freedom
    ENABLE_R_CONTROL = True  # Forward/backward
    ENABLE_THETA_CONTROL = True  # Rotation
    ENABLE_Z_CONTROL = True  # Up/down

    # ========== Safety Limits ==========
    # Maximum flight height (cm)
    MAX_HEIGHT = 300  # 3 meters

    # Maximum horizontal distance from takeoff point (cm)
    MAX_HORIZONTAL_DISTANCE = 500  # 5 meters

    # Auto-land if signal quality is poor for this many seconds
    AUTO_LAND_ON_POOR_SIGNAL_TIMEOUT = 10

    # ========== Calibration Settings ==========
    # Calibration mode: run for a few seconds to determine user's baseline
    ENABLE_CALIBRATION = False
    CALIBRATION_DURATION = 30  # seconds

    def __init__(self):
        """Initialize configuration with any runtime adjustments"""
        pass

    def __repr__(self):
        """String representation of configuration"""
        config_str = "EEG-Drone Control Configuration:\n"
        config_str += f"  EEG Port: {self.EEG_PORT}\n"
        config_str += f"  Tello IP: {self.TELLO_IP}\n"
        config_str += f"  Web Server: {'Enabled' if self.ENABLE_WEB_SERVER else 'Disabled'}\n"
        if self.ENABLE_WEB_SERVER:
            config_str += f"  Web Port: {self.WEB_PORT}\n"
        config_str += f"  Control Mode: {self.CONTROL_MODE}\n"
        config_str += f"  Alpha Range: {self.ALPHA_MIN} - {self.ALPHA_MAX}\n"
        config_str += f"  Smoothing Factor: {self.SMOOTHING_FACTOR}\n"
        config_str += f"  Command Interval: {self.COMMAND_INTERVAL}s\n"
        return config_str


# Platform-specific configuration overrides
import platform

if platform.system() == 'Windows':
    # Windows typically uses COM ports for Bluetooth serial
    # You may need to adjust this to match your system
    Config.EEG_PORT = 'COM3'  # Change to your Bluetooth COM port

elif platform.system() == 'Darwin':  # macOS
    # macOS Bluetooth serial port
    Config.EEG_PORT = '/dev/tty.MindWaveMobile-SerialPo'

else:  # Linux
    # Linux typically uses /dev/rfcomm0
    # You need to pair and bind the device first:
    # sudo bluetoothctl
    # pair XX:XX:XX:XX:XX:XX
    # sudo rfcomm bind /dev/rfcomm0 XX:XX:XX:XX:XX:XX
    Config.EEG_PORT = '/dev/rfcomm0'


if __name__ == "__main__":
    # Display configuration
    config = Config()
    print(config)
    print(f"\nPlatform: {platform.system()}")
