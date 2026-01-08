import os
import json
import subprocess
import time
import math
from datetime import datetime

class PandaScanner:
    def __init__(self):
        self.platform = self._detect_platform()
        self.history = []
        self.known_devices = {} # MAC -> Info

    def _detect_platform(self):
        if os.path.exists('/data/data/com.termux'):
            return 'termux'
        if os.path.exists('/dev/ish'):
            return 'ish'
        return 'generic'

    def scan(self):
        wifi = self.scan_wifi()
        ble = self.scan_ble()
        return wifi + ble

    def scan_wifi(self):
        if self.platform == 'termux':
            return self._scan_termux_wifi()
        elif self.platform == 'ish':
            return self._scan_ish_wifi()
        else:
            return self._scan_mock_wifi()

    def scan_ble(self):
        if self.platform == 'termux':
            return self._scan_termux_ble()
        return []

    def _scan_termux_ble(self):
        try:
            # Note: termux-bluetooth-scan usually runs in background or needs a delay
            # For simplicity, we assume we want immediate results if possible
            result = subprocess.check_output(['termux-bluetooth-scan', '-t', '2'], stderr=subprocess.DEVNULL)
            # This often returns a list of devices or status. Termux-api varies.
            # We'll mock the parse for now as termux-api output can be complex
            return [] 
        except Exception:
            return []

    def _scan_termux_wifi(self):
        try:
            result = subprocess.check_output(['termux-wifi-scaninfo'], stderr=subprocess.DEVNULL)
            data = json.loads(result)
            return self._parse_termux_wifi(data)
        except Exception:
            return []

    def _parse_termux_wifi(self, data):
        scanned = []
        for item in data:
            rssi = item.get('rssi', -100)
            scanned.append({
                'ssid': item.get('ssid', 'Unknown'),
                'bssid': item.get('bssid', '??:??:??:??:??:??'),
                'rssi': rssi,
                'distance': self._calculate_distance(rssi),
                'security': item.get('capabilities', 'Unknown'),
                'timestamp': time.time()
            })
        return scanned

    def _scan_ish_wifi(self):
        # iSH can't do raw wifi scanning. We fallback to ARP scanning or network neighbors.
        # This is a limitation of iOS/iSH.
        try:
            # We look at ARP table for nearby active devices
            result = subprocess.check_output(['arp', '-an'], stderr=subprocess.DEVNULL).decode()
            scanned = []
            for line in result.split('\n'):
                if '(' in line and 'at' in line:
                    parts = line.split()
                    ip = parts[1].strip('()')
                    mac = parts[3]
                    scanned.append({
                        'ssid': f"NetDev: {ip}",
                        'bssid': mac,
                        'rssi': -50, # Fake constant rssi for ARP
                        'distance': 5.0,
                        'security': 'Connected',
                        'timestamp': time.time()
                    })
            return scanned
        except Exception:
            return []

    def _scan_mock_wifi(self):
        # Mock data for development on Mac
        import random
        mocks = [
            {'ssid': 'Home_WiFi', 'bssid': '00:11:22:33:44:55', 'rssi': random.randint(-80, -30)},
            {'ssid': 'Starbucks', 'bssid': 'AA:BB:CC:DD:EE:FF', 'rssi': random.randint(-90, -60)},
            {'ssid': 'Hidden_Net', 'bssid': '12:34:56:78:90:AB', 'rssi': random.randint(-70, -40)},
        ]
        return [{
            'ssid': m['ssid'],
            'bssid': m['bssid'],
            'rssi': m['rssi'],
            'distance': self._calculate_distance(m['rssi']),
            'security': 'WPA2',
            'timestamp': time.time()
        } for m in mocks]

    def _calculate_distance(self, rssi):
        # basic Friis path loss model relative to -30dBm at 1m
        # distance = 10 ^ ((MeasuredPower - RSSI) / (10 * N))
        # N is path loss exponent (2 for free space, 3-4 for indoor)
        measured_power = -30 
        n = 3.0
        if rssi >= 0: return 0.1
        dist = math.pow(10, (measured_power - rssi) / (10 * n))
        return round(dist, 1)

    def calculate_risk(self, device):
        score = 0
        # Open Wifi check
        if 'WPA' not in device['security'] and 'WEP' not in device['security']:
            score += 40
        
        # Proximity check
        if device['distance'] < 2.0:
            score += 30
        elif device['distance'] < 5.0:
            score += 15
            
        # Signal strength
        if device['rssi'] > -40:
            score += 20
            
        return min(100, score)
