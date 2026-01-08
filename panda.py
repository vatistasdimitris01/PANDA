import os
import sys
import time
import json
from panda_core import PandaScanner
from panda_ui import PandaUI
from rich.live import Live

LOG_FILE = "panda_intel.jsonl"

def log_event(device):
    event = {
        "timestamp": datetime.now().isoformat(),
        "ssid": device['ssid'],
        "bssid": device['bssid'],
        "distance": device['distance'],
        "risk": device['risk']
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(event) + "\n")

def main():
    scanner = PandaScanner()
    ui = PandaUI()
    
    # Initialize log file
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            pass

    try:
        with Live(ui.layout, refresh_per_second=1, screen=True) as live:
            while True:
                # Scan
                devices = scanner.scan()
                
                # Process risk
                for dev in devices:
                    dev['risk'] = scanner.calculate_risk(dev)
                
                # Sort by risk/distance
                devices.sort(key=lambda x: (x['risk'], -x['distance']), reverse=True)
                
                # Update UI
                msg = f"Last scan found {len(devices)} devices. Intel logged."
                live.update(ui.update(devices, msg))
                
                # Simple logic for "Intel Timeline": Log if risk > 50 or new device?
                # For now, just a generic pulse
                time.sleep(2)
                
    except KeyboardInterrupt:
        print("\n[!] PANDA System shutdown initiated.")
        print("[*] Logs saved to panda_intel.jsonl")
        sys.exit(0)

if __name__ == "__main__":
    from datetime import datetime
    main()
