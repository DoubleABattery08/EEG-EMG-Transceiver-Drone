#!/usr/bin/env python3
"""
EEG Monitor for Windows
Real-time EEG data monitoring while drone flies on Pi
"""

import serial
import struct
import time
import logging
from threading import Thread, Lock
import json
import requests

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WindowsEEGMonitor:
    """EEG monitor for Windows to track MindWave data while drone flies on Pi"""
    
    # ThinkGear packet constants
    SYNC = 0xAA
    EXCODE = 0x55
    
    # Data codes
    CODE_POOR_SIGNAL = 0x02
    CODE_ATTENTION = 0x04
    CODE_MEDITATION = 0x05
    CODE_RAW_VALUE = 0x80
    CODE_ASIC_EEG_POWER = 0x83
    
    def __init__(self, port='COM3', baudrate=57600):
        """Initialize Windows EEG monitor"""
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.is_connected = False
        self.is_reading = False
        self.read_thread = None
        self.data_lock = Lock()
        
        # Latest EEG data
        self.latest_data = {
            'signal_quality': 200,
            'attention': 0,
            'meditation': 0,
            'alpha': 0,
            'timestamp': time.time()
        }
    
    def connect(self):
        """Connect to MindWave via COM port"""
        try:
            logger.info(f"Connecting to MindWave on {self.port} at {self.baudrate} baud...")
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=1)
            self.is_connected = True
            logger.info("MindWave connected successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MindWave: {e}")
            return False
    
    def start_monitoring(self):
        """Start monitoring EEG data"""
        if not self.connect():
            return False
        
        self.is_reading = True
        self.read_thread = Thread(target=self._read_loop, daemon=True)
        self.read_thread.start()
        
        logger.info("Starting EEG monitoring...")
        logger.info("Press Ctrl+C to stop")
        
        try:
            while self.is_reading:
                self._display_data()
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        finally:
            self.stop()
        
        return True
    
    def _read_loop(self):
        """Background thread for reading data"""
        while self.is_reading and self.is_connected:
            try:
                packet = self._read_packet()
                if packet:
                    self._parse_packet(packet)
            except Exception as e:
                logger.error(f"Error reading packet: {e}")
                time.sleep(0.1)
    
    def _read_packet(self):
        """Read a single ThinkGear packet"""
        if not self.serial_conn or not self.serial_conn.is_open:
            return None
        
        try:
            # Wait for sync bytes
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
            payload_sum = sum(payload) & 0xFF
            if ((~payload_sum) & 0xFF) != checksum:
                return None
            
            return payload
            
        except Exception as e:
            logger.error(f"Error reading packet: {e}")
            return None
    
    def _parse_packet(self, payload):
        """Parse ThinkGear payload"""
        i = 0
        try:
            while i < len(payload):
                # Skip extended code bytes
                while i < len(payload) and payload[i] == self.EXCODE:
                    i += 1
                
                if i >= len(payload):
                    break
                
                code = payload[i]
                i += 1
                
                if code == self.CODE_POOR_SIGNAL:
                    if i < len(payload):
                        signal_quality = payload[i]
                        with self.data_lock:
                            self.latest_data['signal_quality'] = signal_quality
                        i += 1
                
                elif code == self.CODE_ATTENTION:
                    if i < len(payload):
                        attention = payload[i]
                        with self.data_lock:
                            self.latest_data['attention'] = attention
                        i += 1
                
                elif code == self.CODE_MEDITATION:
                    if i < len(payload):
                        meditation = payload[i]
                        with self.data_lock:
                            self.latest_data['meditation'] = meditation
                        i += 1
                
                elif code == self.CODE_ASIC_EEG_POWER:
                    if i + 24 <= len(payload):
                        bands = []
                        for j in range(8):
                            offset = i + (j * 3)
                            value = (payload[offset] << 16) | (payload[offset+1] << 8) | payload[offset+2]
                            bands.append(value)
                        
                        with self.data_lock:
                            self.latest_data['alpha'] = (bands[2] + bands[3]) // 2
                        
                        i += 24
                    else:
                        break
                
                else:
                    # Skip unknown codes
                    if code >= 0x80:
                        if i < len(payload):
                            vlength = payload[i]
                            i += 1
                            if i + vlength <= len(payload):
                                i += vlength
                            else:
                                break
                    else:
                        i += 1
        
        except Exception as e:
            logger.error(f"Error parsing packet: {e}")
    
    def _display_data(self):
        """Display current EEG data"""
        with self.data_lock:
            data = self.latest_data.copy()
        
        signal = data['signal_quality']
        alpha = data['alpha']
        attention = data['attention']
        meditation = data['meditation']
        
        # Color coding for signal quality
        if signal < 50:
            signal_status = "GOOD"
        elif signal < 100:
            signal_status = "FAIR"
        else:
            signal_status = "POOR"
        
        print(f"\rSignal: {signal:3d} ({signal_status}) | Alpha: {alpha:6d} | Attention: {attention:3d} | Meditation: {meditation:3d}", end="", flush=True)
    
    def get_latest_data(self):
        """Get latest EEG data"""
        with self.data_lock:
            return self.latest_data.copy()
    
    def stop(self):
        """Stop monitoring"""
        self.is_reading = False
        if self.read_thread:
            self.read_thread.join(timeout=2)
        
        if self.serial_conn:
            self.serial_conn.close()
            logger.info("MindWave disconnected")
        
        self.is_connected = False

def main():
    """Main function"""
    print("Windows EEG Monitor")
    print("=" * 50)
    print("This will monitor EEG data while the drone flies on the Pi")
    print("Make sure MindWave is paired with Windows")
    print()
    
    # Try common COM ports
    com_ports = ['COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8']
    
    for port in com_ports:
        print(f"Trying {port}...")
        monitor = WindowsEEGMonitor(port=port)
        if monitor.connect():
            monitor.serial_conn.close()
            print(f"Found MindWave on {port}")
            break
    else:
        print("ERROR: Could not find MindWave on any COM port")
        print("Please check Device Manager for the correct COM port")
        return
    
    # Start monitoring
    monitor = WindowsEEGMonitor(port=port)
    monitor.start_monitoring()

if __name__ == "__main__":
    main()
