#!/usr/bin/env python3
"""
MindWave Mobile 2 EEG Headset Interface
Handles Bluetooth connection and data parsing from NeuroSky MindWave headset
"""

import serial
import struct
import logging
from threading import Thread, Lock
import time

logger = logging.getLogger(__name__)


class MindWaveInterface:
    """Interface for MindWave Mobile 2 EEG headset via Bluetooth"""

    # ThinkGear packet constants
    SYNC = 0xAA
    EXCODE = 0x55

    # Data codes
    CODE_POOR_SIGNAL = 0x02
    CODE_ATTENTION = 0x04
    CODE_MEDITATION = 0x05
    CODE_RAW_VALUE = 0x80
    CODE_ASIC_EEG_POWER = 0x83

    def __init__(self, port='/dev/rfcomm0', baudrate=57600):
        """
        Initialize MindWave interface

        Args:
            port: Serial port for Bluetooth connection (default: /dev/rfcomm0)
            baudrate: Baud rate (default: 57600 for MindWave)
        """
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.is_connected = False
        self.is_reading = False
        self.read_thread = None
        self.data_lock = Lock()

        # Latest EEG data
        self.latest_data = {
            'signal_quality': 200,  # 0 = good, 200 = no signal
            'attention': 0,
            'meditation': 0,
            'delta': 0,
            'theta': 0,
            'low_alpha': 0,
            'high_alpha': 0,
            'alpha': 0,  # Combined alpha
            'low_beta': 0,
            'high_beta': 0,
            'low_gamma': 0,
            'mid_gamma': 0,
            'raw_value': 0
        }

        # Auto-connect
        self.connect()

    def connect(self):
        """Establish connection to MindWave headset"""
        try:
            logger.info(f"Connecting to MindWave on {self.port} at {self.baudrate} baud...")
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1
            )
            self.is_connected = True
            logger.info("MindWave connected successfully")

            # Start reading thread
            self.is_reading = True
            self.read_thread = Thread(target=self._read_loop, daemon=True)
            self.read_thread.start()

            return True

        except serial.SerialException as e:
            logger.error(f"Failed to connect to MindWave: {e}")
            logger.info("Make sure the headset is paired and the serial port is correct")
            self.is_connected = False
            return False

    def disconnect(self):
        """Disconnect from MindWave headset"""
        self.is_reading = False
        if self.read_thread:
            self.read_thread.join(timeout=2)

        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            logger.info("MindWave disconnected")

        self.is_connected = False

    def _read_loop(self):
        """Background thread for reading data from MindWave"""
        logger.info("Starting MindWave read loop...")

        while self.is_reading and self.is_connected:
            try:
                packet = self._read_packet()
                if packet:
                    self._parse_packet(packet)
            except Exception as e:
                logger.error(f"Error in read loop: {e}")
                time.sleep(0.1)

    def _read_packet(self):
        """Read a single ThinkGear packet"""
        if not self.serial_conn or not self.serial_conn.is_open:
            return None

        try:
            # Wait for sync bytes (0xAA 0xAA)
            while True:
                byte = self.serial_conn.read(1)
                if not byte:
                    return None

                if ord(byte) == self.SYNC:
                    byte2 = self.serial_conn.read(1)
                    if byte2 and ord(byte2) == self.SYNC:
                        break

            # Read payload length
            plength_byte = self.serial_conn.read(1)
            if not plength_byte:
                return None

            plength = ord(plength_byte)

            # Payload length should be less than 170
            if plength > 169:
                return None

            # Read payload
            payload = self.serial_conn.read(plength)
            if len(payload) != plength:
                return None

            # Read checksum
            checksum_byte = self.serial_conn.read(1)
            if not checksum_byte:
                return None

            checksum = ord(checksum_byte)

            # Verify checksum
            payload_sum = sum(payload) & 0xFF
            if ((~payload_sum) & 0xFF) != checksum:
                logger.warning("Checksum failed")
                return None

            return payload

        except Exception as e:
            logger.error(f"Error reading packet: {e}")
            return None

    def _parse_packet(self, payload):
        """Parse ThinkGear payload and update latest data"""
        i = 0
        while i < len(payload):
            # Skip extended code bytes
            while payload[i] == self.EXCODE:
                i += 1

            code = payload[i]
            i += 1

            if code == self.CODE_POOR_SIGNAL:
                signal_quality = payload[i]
                with self.data_lock:
                    self.latest_data['signal_quality'] = signal_quality
                i += 1

            elif code == self.CODE_ATTENTION:
                attention = payload[i]
                with self.data_lock:
                    self.latest_data['attention'] = attention
                i += 1

            elif code == self.CODE_MEDITATION:
                meditation = payload[i]
                with self.data_lock:
                    self.latest_data['meditation'] = meditation
                i += 1

            elif code == self.CODE_RAW_VALUE:
                # Raw value is 2 bytes, big-endian signed 16-bit
                if i + 2 <= len(payload):
                    raw_value = struct.unpack('>h', bytes(payload[i:i+2]))[0]
                    with self.data_lock:
                        self.latest_data['raw_value'] = raw_value
                i += 2

            elif code == self.CODE_ASIC_EEG_POWER:
                # EEG band powers: 8 bands x 3 bytes each (24 bytes total)
                if i + 24 <= len(payload):
                    bands = []
                    for j in range(8):
                        offset = i + (j * 3)
                        # Each band is 3 bytes, big-endian
                        value = (payload[offset] << 16) | (payload[offset+1] << 8) | payload[offset+2]
                        bands.append(value)

                    with self.data_lock:
                        self.latest_data['delta'] = bands[0]
                        self.latest_data['theta'] = bands[1]
                        self.latest_data['low_alpha'] = bands[2]
                        self.latest_data['high_alpha'] = bands[3]
                        self.latest_data['alpha'] = (bands[2] + bands[3]) // 2
                        self.latest_data['low_beta'] = bands[4]
                        self.latest_data['high_beta'] = bands[5]
                        self.latest_data['low_gamma'] = bands[6]
                        self.latest_data['mid_gamma'] = bands[7]

                i += 24

            else:
                # Unknown code with length
                if code >= 0x80:
                    # Multi-byte value
                    if i < len(payload):
                        vlength = payload[i]
                        i += 1 + vlength
                else:
                    # Single-byte value
                    i += 1

    def read_data(self):
        """
        Get the latest EEG data

        Returns:
            dict: Latest EEG measurements
        """
        with self.data_lock:
            return self.latest_data.copy()

    def is_signal_good(self):
        """Check if signal quality is good (0 = best, 200 = no contact)"""
        with self.data_lock:
            return self.latest_data['signal_quality'] < 50

    def get_alpha_power(self):
        """Get current alpha wave power"""
        with self.data_lock:
            return self.latest_data['alpha']

    def get_attention(self):
        """Get current attention level (0-100)"""
        with self.data_lock:
            return self.latest_data['attention']

    def get_meditation(self):
        """Get current meditation level (0-100)"""
        with self.data_lock:
            return self.latest_data['meditation']


if __name__ == "__main__":
    # Test the interface
    logging.basicConfig(level=logging.INFO)

    print("MindWave Interface Test")
    print("Make sure your MindWave headset is paired and connected")
    print("Default port: /dev/rfcomm0 (Linux) or COM port (Windows)")

    # For Windows, you might need to change this to 'COM3' or similar
    # For Linux, typical is '/dev/rfcomm0'
    eeg = MindWaveInterface(port='/dev/rfcomm0')

    if eeg.is_connected:
        print("\nReading EEG data (Press Ctrl+C to stop)...")
        try:
            while True:
                data = eeg.read_data()
                print(f"\rSignal: {data['signal_quality']:3d} | "
                      f"Alpha: {data['alpha']:8d} | "
                      f"Attention: {data['attention']:3d} | "
                      f"Meditation: {data['meditation']:3d}", end='')
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nStopping...")

    eeg.disconnect()
