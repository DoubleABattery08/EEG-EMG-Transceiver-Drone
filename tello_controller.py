#!/usr/bin/env python3
"""
DJI Tello Drone Controller
Handles WiFi communication and control commands for DJI Tello drone
"""

import socket
import threading
import time
import logging

logger = logging.getLogger(__name__)


class TelloController:
    """Controller for DJI Tello drone via WiFi UDP"""

    def __init__(self, host='192.168.10.1', port=8889, state_port=8890, video_port=11111):
        """
        Initialize Tello controller

        Args:
            host: Tello IP address (default: 192.168.10.1)
            port: Command port (default: 8889)
            state_port: State data port (default: 8890)
            video_port: Video stream port (default: 11111)
        """
        self.host = host
        self.port = port
        self.state_port = state_port
        self.video_port = video_port

        # UDP socket for commands
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('', 9000))  # Bind to local port for receiving responses

        # State socket
        self.state_socket = None
        self.state_thread = None
        self.state_running = False

        # Connection state
        self.is_connected = False
        self.response = None
        self.response_lock = threading.Lock()

        # Current state data
        self.state_data = {}
        self.state_lock = threading.Lock()

        # Response receiver thread
        self.receive_thread = None
        self.abort = False

    def connect(self):
        """Initialize connection to Tello with retry logic"""
        try:
            logger.info("Connecting to Tello...")

            # Try to close and recreate socket in case it's stuck
            try:
                if self.socket:
                    self.socket.close()
            except:
                pass

            # Recreate socket with SO_REUSEADDR to avoid "address already in use"
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(('', 9000))

            logger.info("Socket bound to port 9000")

            # Start response receiver thread
            self.abort = False
            self.receive_thread = threading.Thread(target=self._receive_response, daemon=True)
            self.receive_thread.start()

            # Give thread time to start
            time.sleep(0.5)

            # Try to send command mode multiple times
            for attempt in range(3):
                logger.info(f"Sending 'command' to Tello (attempt {attempt + 1}/3)...")
                response = self.send_command("command", timeout=5)

                if response and response.lower() == "ok":
                    self.is_connected = True
                    logger.info("Tello connected successfully")

                    # Start state receiver thread
                    self._start_state_receiver()

                    return True
                else:
                    logger.warning(f"Attempt {attempt + 1} failed, response: {response}")
                    if attempt < 2:
                        time.sleep(2)

            logger.error("Failed to enter command mode after 3 attempts")
            logger.error("Make sure:")
            logger.error("  1. Tello is powered on")
            logger.error("  2. Connected to Tello WiFi")
            logger.error("  3. Can ping 192.168.10.1")
            logger.error("  4. Firewall allows UDP port 8889")
            return False

        except Exception as e:
            logger.error(f"Connection failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def disconnect(self):
        """Disconnect from Tello"""
        logger.info("Disconnecting from Tello...")
        self.abort = True
        self.state_running = False

        # Send emergency stop to ensure motors are off
        try:
            if self.socket and self.is_connected:
                self.socket.sendto(b'emergency', (self.host, self.port))
                time.sleep(0.1)
        except:
            pass

        # Close sockets
        if self.socket:
            try:
                self.socket.close()
            except:
                pass

        if self.state_socket:
            try:
                self.state_socket.close()
            except:
                pass

        self.is_connected = False

        # Wait for threads to finish
        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join(timeout=2)

        if self.state_thread and self.state_thread.is_alive():
            self.state_thread.join(timeout=2)

    def _receive_response(self):
        """Background thread to receive command responses"""
        while not self.abort:
            try:
                self.socket.settimeout(1.0)
                response, _ = self.socket.recvfrom(1024)
                response_str = response.decode('utf-8').strip()

                with self.response_lock:
                    self.response = response_str

                logger.debug(f"Received: {response_str}")

            except socket.timeout:
                continue
            except Exception as e:
                if not self.abort:
                    logger.error(f"Error receiving response: {e}")
                break

    def _start_state_receiver(self):
        """Start thread to receive state data from Tello"""
        try:
            self.state_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.state_socket.bind(('', self.state_port))
            self.state_running = True

            self.state_thread = threading.Thread(target=self._receive_state, daemon=True)
            self.state_thread.start()

            logger.info("State receiver started")

        except Exception as e:
            logger.error(f"Failed to start state receiver: {e}")

    def _receive_state(self):
        """Background thread to receive state data"""
        while self.state_running:
            try:
                self.state_socket.settimeout(1.0)
                data, _ = self.state_socket.recvfrom(1024)
                state_str = data.decode('utf-8').strip()

                # Parse state data
                state_dict = {}
                for item in state_str.split(';'):
                    if ':' in item:
                        key, value = item.split(':', 1)
                        try:
                            state_dict[key] = float(value)
                        except ValueError:
                            state_dict[key] = value

                with self.state_lock:
                    self.state_data = state_dict

            except socket.timeout:
                continue
            except Exception as e:
                if self.state_running:
                    logger.error(f"Error receiving state: {e}")

    def send_command(self, command, timeout=5):
        """
        Send command to Tello and wait for response

        Args:
            command: Command string
            timeout: Timeout in seconds

        Returns:
            Response string or None
        """
        logger.debug(f"Sending command: {command}")

        # Clear previous response
        with self.response_lock:
            self.response = None

        # Send command
        self.socket.sendto(command.encode('utf-8'), (self.host, self.port))

        # Wait for response
        start_time = time.time()
        while time.time() - start_time < timeout:
            with self.response_lock:
                if self.response:
                    return self.response
            time.sleep(0.01)

        logger.warning(f"Command timeout: {command}")
        return None

    def takeoff(self):
        """Take off with retry logic"""
        logger.info("Taking off...")

        # Try up to 3 times
        for attempt in range(3):
            if attempt > 0:
                logger.warning(f"Takeoff attempt {attempt + 1}/3...")
                # Send command mode again to wake up drone
                self.send_command("command", timeout=3)
                time.sleep(1)

            response = self.send_command("takeoff", timeout=15)
            if response == "ok":
                return True

        logger.error("Takeoff failed after 3 attempts")
        return False

    def land(self):
        """Land"""
        logger.info("Landing...")
        response = self.send_command("land", timeout=10)
        return response == "ok"

    def emergency(self):
        """Emergency stop motors"""
        logger.warning("EMERGENCY STOP")
        response = self.send_command("emergency")
        return response == "ok"

    def send_rc_control(self, left_right, forward_backward, up_down, yaw):
        """
        Send RC control command (velocity control)

        Args:
            left_right: Left/right velocity (-100 to 100)
            forward_backward: Forward/backward velocity (-100 to 100)
            up_down: Up/down velocity (-100 to 100)
            yaw: Yaw velocity (-100 to 100)
        """
        # Clamp values to valid range
        lr = max(-100, min(100, int(left_right)))
        fb = max(-100, min(100, int(forward_backward)))
        ud = max(-100, min(100, int(up_down)))
        y = max(-100, min(100, int(yaw)))

        command = f"rc {lr} {fb} {ud} {y}"
        self.socket.sendto(command.encode('utf-8'), (self.host, self.port))

    def move(self, direction, distance):
        """
        Move in a direction

        Args:
            direction: 'up', 'down', 'left', 'right', 'forward', 'back'
            distance: Distance in cm (20-500)
        """
        distance = max(20, min(500, int(distance)))
        command = f"{direction} {distance}"
        response = self.send_command(command, timeout=10)
        return response == "ok"

    def rotate(self, degrees):
        """
        Rotate clockwise

        Args:
            degrees: Degrees to rotate (positive = clockwise, negative = counter-clockwise)
        """
        if degrees > 0:
            command = f"cw {int(degrees)}"
        else:
            command = f"ccw {int(abs(degrees))}"

        response = self.send_command(command, timeout=10)
        return response == "ok"

    def flip(self, direction):
        """
        Flip in direction

        Args:
            direction: 'l', 'r', 'f', 'b' (left, right, forward, back)
        """
        response = self.send_command(f"flip {direction}", timeout=10)
        return response == "ok"

    def get_battery(self):
        """Get battery percentage"""
        response = self.send_command("battery?")
        try:
            return int(response) if response else 0
        except ValueError:
            return 0

    def get_speed(self):
        """Get current speed setting (cm/s)"""
        response = self.send_command("speed?")
        try:
            return int(response) if response else 0
        except ValueError:
            return 0

    def set_speed(self, speed):
        """Set speed (10-100 cm/s)"""
        speed = max(10, min(100, int(speed)))
        response = self.send_command(f"speed {speed}")
        return response == "ok"

    def get_flight_time(self):
        """Get flight time in seconds"""
        response = self.send_command("time?")
        try:
            return int(response) if response else 0
        except ValueError:
            return 0

    def get_state(self):
        """Get current state data"""
        with self.state_lock:
            return self.state_data.copy()

    def get_height(self):
        """Get current height from state data"""
        state = self.get_state()
        return state.get('h', 0)  # Height in cm


if __name__ == "__main__":
    # Test the controller
    logging.basicConfig(level=logging.INFO)

    print("Tello Controller Test")
    print("Make sure you are connected to Tello WiFi")

    drone = TelloController()

    if drone.connect():
        print(f"Battery: {drone.get_battery()}%")
        print(f"Speed: {drone.get_speed()} cm/s")

        # Test RC control (hover in place)
        print("\nTesting RC control for 5 seconds...")
        for i in range(50):
            drone.send_rc_control(0, 0, 0, 0)
            time.sleep(0.1)

        print("\nTest complete")

    drone.disconnect()
