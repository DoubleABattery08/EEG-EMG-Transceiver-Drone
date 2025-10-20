#!/usr/bin/env python3
"""
Cylindrical Coordinate Mapper
Maps EEG alpha wave activity to 3D cylindrical coordinates (r, theta, z)
and converts them to drone velocity commands
"""

import math
import logging
import numpy as np

logger = logging.getLogger(__name__)


class CylindricalCoordinateMapper:
    """
    Maps alpha wave activity to cylindrical coordinates (r, theta, z)

    Cylindrical coordinates:
    - r (radius): radial distance from center axis (controls forward/backward movement)
    - theta (angle): angular position around center axis (controls rotation/yaw)
    - z (height): vertical position (controls up/down movement)

    The mapping uses three EEG metrics:
    - Alpha power: maps to radius (r) - higher alpha = more forward movement
    - Attention: maps to angle (theta) - controls rotation direction
    - Meditation: maps to height (z) - higher meditation = higher altitude
    """

    def __init__(self, config):
        """
        Initialize coordinate mapper

        Args:
            config: Configuration object with mapping parameters
        """
        self.config = config

        # Alpha power normalization (typical range: 0 to 1000000+)
        self.alpha_min = config.ALPHA_MIN
        self.alpha_max = config.ALPHA_MAX

        # Attention/Meditation range (0-100)
        self.attention_min = 0
        self.attention_max = 100
        self.meditation_min = 0
        self.meditation_max = 100

        # Cylindrical coordinate ranges
        self.r_min = config.R_MIN
        self.r_max = config.R_MAX
        self.theta_min = config.THETA_MIN  # degrees
        self.theta_max = config.THETA_MAX  # degrees
        self.z_min = config.Z_MIN
        self.z_max = config.Z_MAX

        # Velocity output ranges (-100 to 100 for Tello)
        self.velocity_min = -100
        self.velocity_max = 100

        # Smoothing filter (exponential moving average)
        self.alpha_smoothed = 0
        self.attention_smoothed = 0
        self.meditation_smoothed = 0
        self.smoothing_factor = config.SMOOTHING_FACTOR  # 0-1, higher = more smoothing

        # Dead zone thresholds (to prevent drift)
        self.r_deadzone = config.R_DEADZONE
        self.theta_deadzone = config.THETA_DEADZONE
        self.z_deadzone = config.Z_DEADZONE

        logger.info("Cylindrical coordinate mapper initialized")

    def normalize(self, value, min_val, max_val):
        """Normalize value to 0-1 range"""
        if max_val == min_val:
            return 0.5
        normalized = (value - min_val) / (max_val - min_val)
        return max(0, min(1, normalized))

    def map_to_range(self, normalized_value, out_min, out_max):
        """Map normalized value (0-1) to output range"""
        return out_min + normalized_value * (out_max - out_min)

    def smooth_value(self, new_value, smoothed_value):
        """Apply exponential moving average smoothing"""
        return (self.smoothing_factor * smoothed_value +
                (1 - self.smoothing_factor) * new_value)

    def apply_deadzone(self, value, center, deadzone):
        """Apply deadzone around center value"""
        if abs(value - center) < deadzone:
            return center
        return value

    def map_alpha_to_coordinates(self, alpha_power, attention, meditation):
        """
        Map EEG metrics to cylindrical coordinates

        Args:
            alpha_power: Alpha wave power (raw value)
            attention: Attention level (0-100)
            meditation: Meditation level (0-100)

        Returns:
            tuple: (r, theta, z) in cylindrical coordinates
        """
        # Apply smoothing
        self.alpha_smoothed = self.smooth_value(alpha_power, self.alpha_smoothed)
        self.attention_smoothed = self.smooth_value(attention, self.attention_smoothed)
        self.meditation_smoothed = self.smooth_value(meditation, self.meditation_smoothed)

        # Normalize inputs
        alpha_norm = self.normalize(self.alpha_smoothed, self.alpha_min, self.alpha_max)
        attention_norm = self.normalize(self.attention_smoothed,
                                       self.attention_min, self.attention_max)
        meditation_norm = self.normalize(self.meditation_smoothed,
                                        self.meditation_min, self.meditation_max)

        # Map to cylindrical coordinates
        # r (radius): controlled by alpha power
        r = self.map_to_range(alpha_norm, self.r_min, self.r_max)
        r = self.apply_deadzone(r, (self.r_min + self.r_max) / 2, self.r_deadzone)

        # theta (angle): controlled by attention
        # Center at 0 degrees, range from negative to positive
        theta = self.map_to_range(attention_norm, self.theta_min, self.theta_max)
        theta = self.apply_deadzone(theta, 0, self.theta_deadzone)

        # z (height): controlled by meditation
        z = self.map_to_range(meditation_norm, self.z_min, self.z_max)
        z = self.apply_deadzone(z, (self.z_min + self.z_max) / 2, self.z_deadzone)

        return r, theta, z

    def cylindrical_to_velocity(self, r, theta, z):
        """
        Convert cylindrical coordinates to drone velocity commands

        Args:
            r: Radius (0-100)
            theta: Angle in degrees (-180 to 180)
            z: Height (0-100)

        Returns:
            tuple: (vx, vy, vz, vyaw) velocity commands for drone
                   vx: left/right velocity (-100 to 100)
                   vy: forward/backward velocity (-100 to 100)
                   vz: up/down velocity (-100 to 100)
                   vyaw: yaw velocity (-100 to 100)
        """
        # Convert theta to radians
        theta_rad = math.radians(theta)

        # r controls forward/backward movement (vy)
        # Map r from (r_min, r_max) to velocity range
        r_center = (self.r_min + self.r_max) / 2
        r_normalized = (r - r_center) / (self.r_max - r_center)
        vy = int(r_normalized * self.velocity_max)

        # theta controls yaw rotation (vyaw)
        # Normalize theta to -1 to 1 range
        theta_normalized = theta / self.theta_max
        vyaw = int(theta_normalized * self.velocity_max)

        # z controls up/down movement (vz)
        # Map z from (z_min, z_max) to velocity range
        z_center = (self.z_min + self.z_max) / 2
        z_normalized = (z - z_center) / (self.z_max - z_center)
        vz = int(z_normalized * self.velocity_max)

        # vx (left/right) can be derived from r and theta for circular motion
        # For simplicity, we'll use theta component for lateral movement
        vx = int(math.sin(theta_rad) * abs(r_normalized) * self.velocity_max * 0.5)

        # Clamp all values to valid range
        vx = max(self.velocity_min, min(self.velocity_max, vx))
        vy = max(self.velocity_min, min(self.velocity_max, vy))
        vz = max(self.velocity_min, min(self.velocity_max, vz))
        vyaw = max(self.velocity_min, min(self.velocity_max, vyaw))

        logger.debug(f"Cylindrical ({r:.1f}, {theta:.1f}°, {z:.1f}) -> "
                    f"Velocity ({vx}, {vy}, {vz}, {vyaw})")

        return vx, vy, vz, vyaw

    def get_cartesian_from_cylindrical(self, r, theta, z):
        """
        Convert cylindrical to Cartesian coordinates for visualization

        Args:
            r: Radius
            theta: Angle in degrees
            z: Height

        Returns:
            tuple: (x, y, z) in Cartesian coordinates
        """
        theta_rad = math.radians(theta)
        x = r * math.cos(theta_rad)
        y = r * math.sin(theta_rad)
        return x, y, z

    def reset_smoothing(self):
        """Reset smoothing filters"""
        self.alpha_smoothed = 0
        self.attention_smoothed = 0
        self.meditation_smoothed = 0
        logger.info("Smoothing filters reset")


if __name__ == "__main__":
    # Test the mapper
    logging.basicConfig(level=logging.DEBUG)

    # Create a mock config
    class MockConfig:
        ALPHA_MIN = 0
        ALPHA_MAX = 1000000
        R_MIN = 0
        R_MAX = 100
        THETA_MIN = -180
        THETA_MAX = 180
        Z_MIN = 0
        Z_MAX = 100
        SMOOTHING_FACTOR = 0.7
        R_DEADZONE = 10
        THETA_DEADZONE = 15
        Z_DEADZONE = 10

    config = MockConfig()
    mapper = CylindricalCoordinateMapper(config)

    print("\nTesting Cylindrical Coordinate Mapper\n")

    # Test cases
    test_cases = [
        (500000, 50, 50, "Medium alpha, centered attention/meditation"),
        (800000, 80, 70, "High alpha, high attention, high meditation"),
        (200000, 20, 30, "Low alpha, low attention, low meditation"),
        (500000, 90, 50, "Medium alpha, high attention (turn right)"),
        (500000, 10, 50, "Medium alpha, low attention (turn left)"),
    ]

    for alpha, attention, meditation, description in test_cases:
        print(f"\n{description}")
        print(f"Input: Alpha={alpha}, Attention={attention}, Meditation={meditation}")

        r, theta, z = mapper.map_alpha_to_coordinates(alpha, attention, meditation)
        print(f"Cylindrical: r={r:.1f}, theta={theta:.1f}°, z={z:.1f}")

        vx, vy, vz, vyaw = mapper.cylindrical_to_velocity(r, theta, z)
        print(f"Velocity: vx={vx}, vy={vy}, vz={vz}, vyaw={vyaw}")

        x, y, z_cart = mapper.get_cartesian_from_cylindrical(r, theta, z)
        print(f"Cartesian: x={x:.1f}, y={y:.1f}, z={z_cart:.1f}")
