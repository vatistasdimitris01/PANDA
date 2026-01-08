from flask import Flask, jsonify, render_template
from flask_cors import CORS
import threading
import time
from panda_core import PandaScanner

app = Flask(__name__)
CORS(app)

scanner = PandaScanner()
latest_scan = []

def background_scan():
    global latest_scan
    while True:
        try:
            devices = scanner.scan()
            for dev in devices:
                dev['risk'] = scanner.calculate_risk(dev)
            # Sort by risk
            devices.sort(key=lambda x: x['risk'], reverse=True)
            latest_scan = devices
        except Exception as e:
            print(f"Scan Error: {e}")
        time.sleep(3)

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/scan')
def get_scan():
    return jsonify({
        "status": "active",
        "timestamp": time.time(),
        "devices": latest_scan
    })

if __name__ == '__main__':
    # Start scanning thread
    scan_thread = threading.Thread(target=background_scan, daemon=True)
    scan_thread.start()
    # Run server
    app.run(host='0.0.0.0', port=5050)
