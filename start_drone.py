#!/usr/bin/env python3
"""
EEG Drone Startup Script
Simple script to start the EEG-controlled drone system with better error handling
"""

import sys
import os
import subprocess
import time

def check_system():
    """Check system requirements"""
    print("Checking system requirements...")
    
    # Check if the system is on the right platform
    if os.name != 'posix':
        print("ERROR: This script is designed for Linux/Raspberry Pi")
        return False
    
    # Check if the script is in the right directory
    if not os.path.exists('main.py'):
        print("ERROR: main.py not found. Please run from the project directory")
        return False
    
    # Check if required files exist
    required_files = ['config.py', 'eeg_interface.py', 'tello_controller.py', 'coordinate_mapper.py']
    for file in required_files:
        if not os.path.exists(file):
            print(f"ERROR: Required file not found: {file}")
            return False
    
    print("System requirements check passed")
    return True

def check_connections():
    """Check if devices are connected"""
    print("\nChecking device connections...")
    
    # Check if MindWave device exists
    if os.path.exists('/dev/rfcomm0'):
        print("SUCCESS: MindWave device found at /dev/rfcomm0")
    else:
        print("WARNING: MindWave device not found. Make sure it's paired and connected")
        print("   Run: sudo rfcomm bind /dev/rfcomm0 <MAC_ADDRESS> 1")
    
    # Check if the system can reach Tello
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2)
        sock.connect(('192.168.10.1', 8889))
        sock.close()
        print("SUCCESS: Tello drone reachable at 192.168.10.1")
    except:
        print("WARNING: Cannot reach Tello drone. Make sure:")
        print("   - Tello is powered on")
        print("   - Pi is connected to Tello WiFi")
        print("   - Tello IP is 192.168.10.1")

def install_dependencies():
    """Install required dependencies"""
    print("\nChecking dependencies...")
    
    try:
        import serial
        import numpy
        print("SUCCESS: All dependencies are installed")
        return True
    except ImportError as e:
        print(f"ERROR: Missing dependency: {e}")
        print("Installing dependencies...")
        
        try:
            subprocess.run(['pip3', 'install', 'pyserial', 'numpy'], check=True)
            print("SUCCESS: Dependencies installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("ERROR: Failed to install dependencies")
            print("Please run: pip3 install pyserial numpy")
            return False

def main():
    """Main startup function"""
    print("EEG-Controlled Drone System Startup")
    print("=" * 50)
    
    # Check system
    if not check_system():
        print("\nERROR: System check failed. Please fix the issues above.")
        return 1
    
    # Check dependencies
    if not install_dependencies():
        print("\nERROR: Dependency check failed. Please install required packages.")
        return 1
    
    # Check connections
    check_connections()
    
    print("\nStarting EEG-Drone Control System...")
    print("Press Ctrl+C to stop and land the drone")
    print("=" * 50)
    
    # Start the main system
    try:
        import main
        main.main()
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"\nERROR: System error: {e}")
        return 1
    
    print("\nSystem shutdown complete")
    return 0

if __name__ == "__main__":
    sys.exit(main())
