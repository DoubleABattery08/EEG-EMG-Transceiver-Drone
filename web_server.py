#!/usr/bin/env python3
"""
EEG Visualization Web Server
Real-time EEG data visualization using Flask and SocketIO
Broadcasts alpha, beta, theta waves to a web dashboard
"""

import logging
import threading
import time
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS

logger = logging.getLogger(__name__)


class EEGWebServer:
    """Web server for real-time EEG data visualization"""

    def __init__(self, eeg_interface, config):
        """
        Initialize web server

        Args:
            eeg_interface: MindWaveInterface instance
            config: Configuration object
        """
        self.eeg = eeg_interface
        self.config = config
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'eeg-drone-secret-key'

        # Enable CORS for cross-origin requests
        CORS(self.app)

        # Initialize SocketIO for real-time communication
        self.socketio = SocketIO(self.app, cors_allowed_origins="*", async_mode='threading')

        # Server state
        self.is_running = False
        self.broadcast_thread = None

        # Data history for graphs (last 100 data points)
        self.max_history = 100
        self.history = {
            'timestamps': [],
            'delta': [],
            'theta': [],
            'low_alpha': [],
            'high_alpha': [],
            'alpha': [],
            'low_beta': [],
            'high_beta': [],
            'low_gamma': [],
            'mid_gamma': [],
            'attention': [],
            'meditation': [],
            'signal_quality': []
        }

        # Setup routes
        self._setup_routes()
        self._setup_socketio_events()

    def _setup_routes(self):
        """Setup Flask routes"""

        @self.app.route('/')
        def index():
            """Main dashboard page"""
            return render_template('dashboard.html',
                                 port=self.config.WEB_PORT,
                                 update_rate=self.config.WEB_UPDATE_RATE)

        @self.app.route('/api/status')
        def status():
            """API endpoint for system status"""
            eeg_data = self.eeg.read_data()
            return jsonify({
                'eeg_connected': self.eeg.is_connected,
                'signal_quality': eeg_data['signal_quality'],
                'signal_good': self.eeg.is_signal_good(),
                'server_running': self.is_running
            })

        @self.app.route('/api/current')
        def current_data():
            """API endpoint for current EEG data"""
            return jsonify(self.eeg.read_data())

        @self.app.route('/api/history')
        def history():
            """API endpoint for historical data"""
            return jsonify(self.history)

    def _setup_socketio_events(self):
        """Setup SocketIO event handlers"""

        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection"""
            logger.info(f"Client connected")
            emit('status', {'connected': True, 'message': 'Connected to EEG server'})

        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            logger.info(f"Client disconnected")

        @self.socketio.on('request_data')
        def handle_request_data():
            """Handle data request from client"""
            eeg_data = self.eeg.read_data()
            emit('eeg_data', eeg_data)

    def _update_history(self, data):
        """Update data history for graphs"""
        current_time = time.time()

        # Add new data
        self.history['timestamps'].append(current_time)
        self.history['delta'].append(data['delta'])
        self.history['theta'].append(data['theta'])
        self.history['low_alpha'].append(data['low_alpha'])
        self.history['high_alpha'].append(data['high_alpha'])
        self.history['alpha'].append(data['alpha'])
        self.history['low_beta'].append(data['low_beta'])
        self.history['high_beta'].append(data['high_beta'])
        self.history['low_gamma'].append(data['low_gamma'])
        self.history['mid_gamma'].append(data['mid_gamma'])
        self.history['attention'].append(data['attention'])
        self.history['meditation'].append(data['meditation'])
        self.history['signal_quality'].append(data['signal_quality'])

        # Remove old data if exceeding max history
        if len(self.history['timestamps']) > self.max_history:
            for key in self.history:
                self.history[key] = self.history[key][-self.max_history:]

    def _broadcast_loop(self):
        """Background thread for broadcasting EEG data"""
        logger.info("Starting EEG data broadcast loop...")

        while self.is_running:
            try:
                # Read current EEG data
                eeg_data = self.eeg.read_data()

                # Update history
                self._update_history(eeg_data)

                # Broadcast to all connected clients
                self.socketio.emit('eeg_data', eeg_data)

                # Sleep for update interval
                time.sleep(1.0 / self.config.WEB_UPDATE_RATE)

            except Exception as e:
                logger.error(f"Error in broadcast loop: {e}")
                time.sleep(0.1)

    def start(self):
        """Start the web server"""
        logger.info(f"Starting EEG web server on port {self.config.WEB_PORT}...")
        logger.info(f"Dashboard URL: http://{self.config.WEB_HOST}:{self.config.WEB_PORT}")
        logger.info(f"Access from network: http://<raspberry-pi-ip>:{self.config.WEB_PORT}")

        # Start broadcast thread
        self.is_running = True
        self.broadcast_thread = threading.Thread(target=self._broadcast_loop, daemon=True)
        self.broadcast_thread.start()

        # Start Flask server
        self.socketio.run(
            self.app,
            host=self.config.WEB_HOST,
            port=self.config.WEB_PORT,
            debug=False,
            use_reloader=False,
            allow_unsafe_werkzeug=True
        )

    def stop(self):
        """Stop the web server"""
        logger.info("Stopping EEG web server...")
        self.is_running = False
        if self.broadcast_thread:
            self.broadcast_thread.join(timeout=2)


if __name__ == "__main__":
    # Test the web server standalone
    logging.basicConfig(level=logging.INFO)

    from eeg_interface import MindWaveInterface
    from config import Config

    print("EEG Web Server Test")
    print("Starting MindWave interface...")

    config = Config()
    eeg = MindWaveInterface(port=config.EEG_PORT)

    if eeg.is_connected:
        print(f"\nStarting web server on http://0.0.0.0:{config.WEB_PORT}")
        print("Press Ctrl+C to stop")

        server = EEGWebServer(eeg, config)
        try:
            server.start()
        except KeyboardInterrupt:
            print("\nStopping...")
            server.stop()
            eeg.disconnect()
    else:
        print("Failed to connect to MindWave headset")
