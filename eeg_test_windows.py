import serial
import struct
import logging
import time
from threading import Thread, Lock

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class MindWaveWindowsInterface:
    def __init__(self, port='COM3', baudrate=57600):
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.is_connected = False
        self.is_reading = False
        self.read_thread = None
        self.data_lock = Lock()
        
        # Initialize data structure
        self.latest_data = {
            'signal_quality': 200,
            'attention': 0,
            'meditation': 0,
            'alpha': 0,
            'beta': 0,
            'theta': 0,
            'delta': 0
        }

    def connect(self):
        """Connect to MindWave via serial port"""
        try:
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=1)
            self.is_connected = True
            logger.info(f"Connected to MindWave on {self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MindWave: {e}")
            return False

    def disconnect(self):
        """Disconnect from MindWave"""
        self.is_connected = False
        if self.serial_conn:
            self.serial_conn.close()
            logger.info("MindWave disconnected")

    def _read_packet(self):
        """Read a packet from MindWave"""
        try:
            # Look for sync bytes (0xAA, 0xAA)
            while True:
                byte1 = self.serial_conn.read(1)
                if not byte1:
                    return None
                
                if byte1[0] == 0xAA:
                    byte2 = self.serial_conn.read(1)
                    if byte2 and byte2[0] == 0xAA:
                        # Found sync bytes, read the rest of the packet
                        payload_length = self.serial_conn.read(1)[0]
                        payload = self.serial_conn.read(payload_length)
                        checksum = self.serial_conn.read(1)[0]
                        
                        # Verify checksum
                        calculated_checksum = 0
                        for byte in payload:
                            calculated_checksum ^= byte
                        
                        if calculated_checksum == checksum:
                            return payload
                        else:
                            logger.warning("Checksum mismatch")
                            continue
        except Exception as e:
            logger.error(f"Error reading packet: {e}")
            return None

    def _parse_packet(self, payload):
        """Parse MindWave packet"""
        with self.data_lock:
            i = 0
            while i < len(payload):
                code = payload[i]
                
                if code == 0x02:  # Signal quality
                    if i + 1 < len(payload):
                        self.latest_data['signal_quality'] = payload[i + 1]
                        i += 2
                    else:
                        break
                        
                elif code == 0x04:  # Attention
                    if i + 1 < len(payload):
                        self.latest_data['attention'] = payload[i + 1]
                        i += 2
                    else:
                        break
                        
                elif code == 0x05:  # Meditation
                    if i + 1 < len(payload):
                        self.latest_data['meditation'] = payload[i + 1]
                        i += 2
                    else:
                        break
                        
                elif code == 0x80:  # Raw wave data
                    if i + 3 < len(payload):
                        # Skip raw wave data for now
                        i += 4
                    else:
                        break
                        
                elif code == 0x83:  # EEG power bands
                    if i + 25 < len(payload):
                        # Parse EEG power bands
                        delta = struct.unpack('<I', payload[i+1:i+5])[0]
                        theta = struct.unpack('<I', payload[i+5:i+9])[0]
                        low_alpha = struct.unpack('<I', payload[i+9:i+13])[0]
                        high_alpha = struct.unpack('<I', payload[i+13:i+17])[0]
                        low_beta = struct.unpack('<I', payload[i+17:i+21])[0]
                        high_beta = struct.unpack('<I', payload[i+21:i+25])[0]
                        
                        self.latest_data['alpha'] = low_alpha + high_alpha
                        self.latest_data['beta'] = low_beta + high_beta
                        self.latest_data['theta'] = theta
                        self.latest_data['delta'] = delta
                        
                        i += 25
                    else:
                        break
                else:
                    i += 1

    def start_reading(self):
        """Start reading data in background thread"""
        if not self.is_connected:
            return False
        
        self.is_reading = True
        self.read_thread = Thread(target=self._read_loop)
        self.read_thread.daemon = True
        self.read_thread.start()
        return True

    def _read_loop(self):
        """Background thread for reading data"""
        logger.info("Starting MindWave read loop...")
        
        while self.is_reading and self.is_connected:
            try:
                packet = self._read_packet()
                if packet:
                    self._parse_packet(packet)
                else:
                    time.sleep(0.01)
            except Exception as e:
                logger.error(f"Error in read loop: {e}")
                time.sleep(0.1)

    def get_latest_data(self):
        """Get latest EEG data"""
        with self.data_lock:
            return self.latest_data.copy()

    def stop_reading(self):
        """Stop reading data"""
        self.is_reading = False
        if self.read_thread:
            self.read_thread.join()

def main():
    print("Windows MindWave Test")
    print("====================")
    print("Testing MindWave connection on Windows...")
    
    # Try different COM ports
    com_ports = ['COM3', 'COM4', 'COM5', 'COM6']
    eeg_interface = None
    
    for port in com_ports:
        print(f"Trying {port}...")
        eeg_interface = MindWaveWindowsInterface(port=port)
        if eeg_interface.connect():
            print(f"SUCCESS: Connected to MindWave on {port}")
            break
        else:
            print(f"Failed to connect on {port}")
    
    if not eeg_interface or not eeg_interface.is_connected:
        print("ERROR: Could not connect to MindWave on any COM port")
        print("Make sure MindWave is paired and connected via Bluetooth")
        return
    
    # Start reading data
    if eeg_interface.start_reading():
        print("Starting EEG data reading...")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                data = eeg_interface.get_latest_data()
                signal_status = "GOOD" if data['signal_quality'] < 50 else "POOR"
                print(f"Signal: {data['signal_quality']:>3} ({signal_status:>4}) | "
                      f"Alpha: {data['alpha']:>6} | "
                      f"Attention: {data['attention']:>3} | "
                      f"Meditation: {data['meditation']:>3}", end='\r')
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nStopping EEG monitor...")
        finally:
            eeg_interface.stop_reading()
            eeg_interface.disconnect()
            print("Monitor stopped.")

if __name__ == "__main__":
    main()
