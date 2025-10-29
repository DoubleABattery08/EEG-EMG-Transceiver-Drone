#!/usr/bin/env python3
"""
EEG-Controlled Tello Drone System
Main control script for integrating MindWave EEG headset with DJI Tello drone
using cylindrical coordinates (r, theta, z) derived from alpha wave activity.
"""

import time
import logging
import signal
import sys
from threading import Event, Thread
from eeg_interface import MindWaveInterface
from tello_controller import TelloController
from coordinate_mapper import CylindricalCoordinateMapper
from config import Config
from web_server import EEGWebServer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('eeg_drone_control.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Global shutdown event
shutdown_event = Event()


def signal_handler(sig, frame):
    """Handle graceful shutdown on CTRL+C"""
    logger.info("Shutdown signal received. Cleaning up...")
    shutdown_event.set()


class EEGDroneController:
    """Main controller integrating EEG input with Tello drone control"""

    def __init__(self, config):
        self.config = config
        self.eeg = None
        self.drone = None
        self.mapper = None
        self.web_server = None
        self.web_thread = None
        self.is_running = False

    def initialize(self):
        """Initialize all components"""
        try:
            logger.info("Initializing EEG-Drone Control System...")

            # Initialize coordinate mapper
            logger.info("Initializing coordinate mapper...")
            self.mapper = CylindricalCoordinateMapper(self.config)

            # Initialize EEG headset with error handling
            logger.info("Initializing MindWave EEG headset...")
            try:
                self.eeg = MindWaveInterface(
                    port=self.config.EEG_PORT,
                    baudrate=self.config.EEG_BAUDRATE
                )
                logger.info("EEG headset interface created successfully")
            except Exception as e:
                logger.error(f"Failed to create EEG interface: {e}")
                logger.error("Make sure MindWave is powered on and in pairing mode")
                return False

            # Start web server if enabled
            if self.config.ENABLE_WEB_SERVER:
                try:
                    logger.info("Starting web visualization server...")
                    self.web_server = EEGWebServer(self.eeg, self.config)
                    self.web_thread = Thread(target=self.web_server.start, daemon=True)
                    self.web_thread.start()
                    logger.info(f"Web dashboard available at http://{self.config.WEB_HOST}:{self.config.WEB_PORT}")
                    logger.info(f"Access from other devices: http://<raspberry-pi-ip>:{self.config.WEB_PORT}")
                except Exception as e:
                    logger.warning(f"Failed to start web server: {e}")
                    logger.warning("Continuing without web server...")
                    self.web_server = None
                    self.web_thread = None

            # Initialize Tello drone
            logger.info("Initializing Tello drone...")
            try:
                self.drone = TelloController(
                    host=self.config.TELLO_IP,
                    port=self.config.TELLO_PORT
                )
                logger.info("Tello controller created successfully")
            except Exception as e:
                logger.error(f"Failed to create Tello controller: {e}")
                return False

            # Connect to drone with retry logic
            logger.info("Connecting to Tello drone...")
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    if self.drone.connect():
                        logger.info("Successfully connected to Tello drone")
                        break
                    else:
                        logger.warning(f"Connection attempt {attempt + 1} failed")
                        if attempt < max_retries - 1:
                            logger.info("Retrying in 2 seconds...")
                            time.sleep(2)
                        else:
                            raise Exception("Failed to connect to Tello drone after all retries")
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"Failed to connect to Tello drone: {e}")
                        logger.error("Make sure Tello is powered on and Pi is connected to Tello WiFi")
                        return False
                    else:
                        logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                        time.sleep(2)

            # Get battery level with error handling
            try:
                battery = self.drone.get_battery()
                logger.info(f"Drone battery level: {battery}%")

                if battery < self.config.MIN_BATTERY_LEVEL:
                    logger.warning(f"Battery level too low: {battery}% (minimum: {self.config.MIN_BATTERY_LEVEL}%)")
                    logger.warning("Please charge the drone before flying")
                    return False
            except Exception as e:
                logger.warning(f"Could not get battery level: {e}")
                logger.warning("Continuing without battery check...")

            logger.info("All systems initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return False

    def start(self):
        """Start the control loop"""
        if not self.initialize():
            logger.error("Failed to initialize system")
            return

        self.is_running = True
        logger.info("Starting EEG-Drone control loop...")
        logger.info("Press CTRL+C to stop and land the drone")

        try:
            # Takeoff
            if self.config.AUTO_TAKEOFF:
                logger.info("Taking off...")
                self.drone.takeoff()
                time.sleep(3)

            control_loop_count = 0
            last_command_time = time.time()

            while self.is_running and not shutdown_event.is_set():
                try:
                    # Read EEG data
                    eeg_data = self.eeg.read_data()

                    if eeg_data and 'alpha' in eeg_data:
                        alpha_power = eeg_data['alpha']
                        attention = eeg_data.get('attention', 0)
                        meditation = eeg_data.get('meditation', 0)
                        signal_quality = eeg_data.get('signal_quality', 200)

                        # Check signal quality
                        if signal_quality > self.config.MAX_POOR_SIGNAL:
                            if control_loop_count % 20 == 0:  # Log every 20 iterations when signal is poor
                                logger.warning(f"Poor EEG signal quality: {signal_quality} (max good: {self.config.MAX_POOR_SIGNAL})")
                                logger.warning("Check headset contact and positioning")
                            # Skip control commands when signal is poor
                            time.sleep(self.config.LOOP_DELAY)
                            continue

                        # Log EEG metrics
                        if control_loop_count % 10 == 0:  # Log every 10 iterations
                            logger.info(f"Signal: {signal_quality}, Alpha: {alpha_power}, Attention: {attention}, Meditation: {meditation}")

                        # Map alpha waves to cylindrical coordinates
                        r, theta, z = self.mapper.map_alpha_to_coordinates(
                            alpha_power, attention, meditation
                        )

                        # Convert cylindrical to drone velocity commands
                        vx, vy, vz, yaw = self.mapper.cylindrical_to_velocity(r, theta, z)

                        # Validate command values
                        vx = max(-100, min(100, vx))
                        vy = max(-100, min(100, vy))
                        vz = max(-100, min(100, vz))
                        yaw = max(-100, min(100, yaw))

                        # Send command to drone (with rate limiting)
                        current_time = time.time()
                        if current_time - last_command_time >= self.config.COMMAND_INTERVAL:
                            try:
                                self.drone.send_rc_control(vx, vy, vz, yaw)
                                last_command_time = current_time
                            except Exception as e:
                                logger.error(f"Failed to send drone command: {e}")
                                # Continue trying to send commands

                        control_loop_count += 1
                    else:
                        # No valid EEG data
                        if control_loop_count % 50 == 0:  # Log every 50 iterations when no data
                            logger.warning("No valid EEG data received - check headset connection")

                except Exception as e:
                    logger.error(f"Error in control loop: {e}")
                    # Continue the loop even if there's an error

                # Small delay to prevent overwhelming the system
                time.sleep(self.config.LOOP_DELAY)

        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        except Exception as e:
            logger.error(f"Error in control loop: {e}")
        finally:
            self.stop()

    def stop(self):
        """Stop the system and land the drone"""
        self.is_running = False
        logger.info("Stopping EEG-Drone control system...")

        # Stop web server first
        if self.web_server:
            try:
                logger.info("Stopping web server...")
                self.web_server.stop()
                if self.web_thread and self.web_thread.is_alive():
                    self.web_thread.join(timeout=5)
                logger.info("Web server stopped")
            except Exception as e:
                logger.error(f"Error stopping web server: {e}")

        # Land drone safely
        if self.drone:
            try:
                logger.info("Landing drone...")
                self.drone.land()
                time.sleep(3)
                logger.info("Drone landed successfully")
            except Exception as e:
                logger.error(f"Error during drone landing: {e}")
                logger.warning("Drone may not have landed safely - check manually")

            try:
                logger.info("Disconnecting from drone...")
                self.drone.disconnect()
                logger.info("Drone disconnected")
            except Exception as e:
                logger.error(f"Error disconnecting from drone: {e}")

        # Disconnect EEG
        if self.eeg:
            try:
                logger.info("Disconnecting EEG headset...")
                self.eeg.disconnect()
                logger.info("EEG headset disconnected")
            except Exception as e:
                logger.error(f"Error disconnecting EEG: {e}")

        logger.info("System shutdown complete")


def check_dependencies():
    """Check if all required dependencies are available"""
    missing_deps = []
    
    try:
        import serial
    except ImportError:
        missing_deps.append("pyserial")
    
    try:
        import numpy
    except ImportError:
        missing_deps.append("numpy")
    
    try:
        import socket
    except ImportError:
        missing_deps.append("socket (built-in)")
    
    if missing_deps:
        logger.error(f"Missing dependencies: {', '.join(missing_deps)}")
        logger.error("Install with: pip3 install " + " ".join(missing_deps))
        return False
    
    return True


def main():
    """Main entry point"""
    # Setup signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Check dependencies
    if not check_dependencies():
        logger.error("Missing required dependencies. Please install them and try again.")
        return

    # Load configuration
    config = Config()
    logger.info("Configuration loaded successfully")

    # Create and start controller
    try:
        controller = EEGDroneController(config)
        controller.start()
    except Exception as e:
        logger.error(f"Failed to start controller: {e}")
        logger.error("Check your connections and try again")


if __name__ == "__main__":
    main()
