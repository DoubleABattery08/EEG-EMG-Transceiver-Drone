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
from threading import Event
from eeg_interface import MindWaveInterface
from tello_controller import TelloController
from coordinate_mapper import CylindricalCoordinateMapper
from config import Config

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
        self.is_running = False

    def initialize(self):
        """Initialize all components"""
        try:
            logger.info("Initializing EEG-Drone Control System...")

            # Initialize coordinate mapper
            logger.info("Initializing coordinate mapper...")
            self.mapper = CylindricalCoordinateMapper(self.config)

            # Initialize EEG headset
            logger.info("Initializing MindWave EEG headset...")
            self.eeg = MindWaveInterface(
                port=self.config.EEG_PORT,
                baudrate=self.config.EEG_BAUDRATE
            )

            # Initialize Tello drone
            logger.info("Initializing Tello drone...")
            self.drone = TelloController(
                host=self.config.TELLO_IP,
                port=self.config.TELLO_PORT
            )

            # Connect to drone
            logger.info("Connecting to Tello drone...")
            if not self.drone.connect():
                raise Exception("Failed to connect to Tello drone")

            # Get battery level
            battery = self.drone.get_battery()
            logger.info(f"Drone battery level: {battery}%")

            if battery < self.config.MIN_BATTERY_LEVEL:
                logger.warning(f"Battery level too low: {battery}%")
                return False

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
                # Read EEG data
                eeg_data = self.eeg.read_data()

                if eeg_data and 'alpha' in eeg_data:
                    alpha_power = eeg_data['alpha']
                    attention = eeg_data.get('attention', 0)
                    meditation = eeg_data.get('meditation', 0)

                    # Log EEG metrics
                    if control_loop_count % 10 == 0:  # Log every 10 iterations
                        logger.info(f"Alpha: {alpha_power}, Attention: {attention}, Meditation: {meditation}")

                    # Map alpha waves to cylindrical coordinates
                    r, theta, z = self.mapper.map_alpha_to_coordinates(
                        alpha_power, attention, meditation
                    )

                    # Convert cylindrical to drone velocity commands
                    vx, vy, vz, yaw = self.mapper.cylindrical_to_velocity(r, theta, z)

                    # Send command to drone (with rate limiting)
                    current_time = time.time()
                    if current_time - last_command_time >= self.config.COMMAND_INTERVAL:
                        self.drone.send_rc_control(vx, vy, vz, yaw)
                        last_command_time = current_time

                    control_loop_count += 1

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

        if self.drone:
            try:
                logger.info("Landing drone...")
                self.drone.land()
                time.sleep(3)
                self.drone.disconnect()
            except Exception as e:
                logger.error(f"Error during drone landing: {e}")

        if self.eeg:
            try:
                self.eeg.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting EEG: {e}")

        logger.info("System shutdown complete")


def main():
    """Main entry point"""
    # Setup signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Load configuration
    config = Config()

    # Create and start controller
    controller = EEGDroneController(config)
    controller.start()


if __name__ == "__main__":
    main()
