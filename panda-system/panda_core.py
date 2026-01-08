import os
import json
import subprocess
import time
import math
import re
import threading

class PandaScanner:
    def __init__(self):
        self.platform = self._detect_platform()
        self.lock = threading.Lock()
        self.devices = {} # Map BSSID/MAC -> Device Object

    def _detect_platform(self):
        if os.path.exists('/data/data/com.termux'):
            return 'termux'
        if os.path.exists('/dev/ish') or os.path.exists('/proc/ish'):
            return 'ish'
        return 'generic'

    def scan(self):
        """Unified scan method returning list of devices"""
        wifi = []
        ble = []
        
        if self.platform == 'termux':
            wifi = self._scan_termux_wifi()
            ble = self._scan_termux_ble()
        elif self.platform == 'ish':
            wifi = self._scan_ish_arp()
            # iSH has no bluetooth access usually, returning empty or mock if needed
            ble = [] 
        else:
            wifi = self._scan_mock_wifi()
            ble = self._scan_mock_ble()

        # Merge into main device list
        current_time = time.time()
        with self.lock:
            # Mark all as not seen efficiently if needed, but for now we just upsert
            for d in wifi + ble:
                mac = d['bssid']
                if mac in self.devices:
                    # Update existing
                    self.devices[mac].update(d)
                else:
                    self.devices[mac] = d
                self.devices[mac]['last_seen'] = current_time
            
            # Convert dict to list
            return list(self.devices.values())

    # --- Termux Methods ---
    def _scan_termux_wifi(self):
        try:
            # cmd = "termux-wifi-scaninfo"
            result = subprocess.check_output(['termux-wifi-scaninfo'], stderr=subprocess.DEVNULL)
            data = json.loads(result)
            scanned = []
            for item in data:
                rssi = item.get('rssi', -100)
                freq = item.get('frequency', 2412)
                scanned.append({
                    'type': 'WIFI',
                    'ssid': item.get('ssid', 'Hidden'),
                    'bssid': item.get('bssid', '??:??:??:??:??:??'),
                    'rssi': rssi,
                    'frequency': freq,
                    'channel': self._freq_to_channel(freq),
                    'distance': self._calculate_distance(rssi, freq),
                    'security': item.get('capabilities', '[OPEN]'),
                    'vendor': 'Unknown', # Could add OUI lookup later
                    'score': 0 
                })
            return scanned
        except Exception:
            return []

    def _scan_termux_ble(self):
        try:
            # termux-bluetooth-scan -t 2
            # Output is JSON list
            result = subprocess.check_output(['termux-bluetooth-scan', '-t', '2'], stderr=subprocess.DEVNULL)
            data = json.loads(result)
            scanned = []
            for item in data:
                rssi = item.get('rssi', -100)
                mac = item.get('address', '??:??:??:??:??:??')
                name = item.get('name') or "BLE Device"
                scanned.append({
                    'type': 'BLE',
                    'ssid': name,
                    'bssid': mac,
                    'rssi': rssi,
                    'frequency': 2400,
                    'channel': 37, # Generic BLE adv channel
                    'distance': self._calculate_distance(rssi, 2400),
                    'security': 'BLE',
                    'vendor': 'Unknown',
                    'score': 0
                })
            return scanned
        except Exception:
            return []

    # --- iSH Methods ---
    def _scan_ish_arp(self):
        # 1. Get neighbors
        try:
            result = subprocess.check_output(['arp', '-an'], stderr=subprocess.DEVNULL).decode()
            scanned = []
            for line in result.split('\n'):
                # ? (192.168.1.1) at 00:11:22:33:44:55 [ether] on eth0
                if 'at' in line:
                    parts = line.split()
                    try:
                        ip_chunk = parts[1].strip('()')
                        mac_chunk = parts[3]
                        if ':' in mac_chunk:
                            # 2. Ping to estimate "presence" and "latency" (as fake RSSI)
                            lat = self._ping_latency(ip_chunk)
                            # Latency mapping: 2ms -> -40dBm, 100ms -> -90dBm
                            fake_rssi = -40 - (lat if lat < 60 else 60)
                            
                            scanned.append({
                                'type': 'WIFI-NET',
                                'ssid': f"Net: {ip_chunk}",
                                'bssid': mac_chunk,
                                'rssi': int(fake_rssi),
                                'frequency': 2400, # Unknown
                                'channel': 0,
                                'distance': self._calculate_distance(fake_rssi, 2400),
                                'security': 'LAN',
                                'vendor': 'Unknown',
                                'score': 0
                            })
                    except:
                        pass
            return scanned
        except:
            return []

    def _ping_latency(self, ip):
        try:
            # Ping 1 packet, timeout 0.2s
            out = subprocess.check_output(['ping', '-c', '1', '-W', '1', ip], stderr=subprocess.DEVNULL).decode()
            # Extract time=xx.xx ms
            match = re.search(r'time=([\d\.]+)', out)
            if match:
                return float(match.group(1))
        except:
            pass
        return 100.0

    # --- Mock Methods ---
    def _scan_mock_wifi(self):
        import random
        base = [
            {'ssid': 'AndroidAuto-7f11', 'bssid': '50:5a:65:9b:7f:11', 'rssi': -77, 'freq': 5745, 'sec': '[WPA2-PSK-CCMP][ESS]'},
            {'ssid': 'SpectrumSetup-40', 'bssid': '34:53:d2:46:15:47', 'rssi': -92, 'freq': 5220, 'sec': '[WPA2-PSK]'},
            {'ssid': '[hidden]', 'bssid': '32:1b:9e:e3:ba:36', 'rssi': -85, 'freq': 5220, 'sec': '[WPA2][WPS]'},
            {'ssid': 'HP-Print-55', 'bssid': 'aa:bb:cc:11:22:33', 'rssi': -45, 'freq': 2412, 'sec': '[WPA2]'},
        ]
        scanned = []
        for b in base:
            # Jitter
            rssi = b['rssi'] + random.randint(-2, 2)
            scanned.append({
                'type': 'WIFI',
                'ssid': b['ssid'],
                'bssid': b['bssid'],
                'rssi': rssi,
                'frequency': b['freq'],
                'channel': self._freq_to_channel(b['freq']),
                'distance': self._calculate_distance(rssi, b['freq']),
                'security': b['sec'],
                'vendor': 'Unknown',
                'score': 0
            })
        return scanned

    def _scan_mock_ble(self):
        import random
        return [{
            'type': 'BLE',
            'ssid': 'Tile',
            'bssid': 'FE:E4:D2:C1:B0:A9',
            'rssi': random.randint(-95, -60),
            'frequency': 2402,
            'channel': 37,
            'distance': random.uniform(1.0, 15.0),
            'security': 'BLE-Lvl1',
            'vendor': 'Tile Inc.',
            'score': 0
        }]

    # --- Utils ---
    def _freq_to_channel(self, freq):
        if 2412 <= freq <= 2484:
            return (freq - 2412) // 5 + 1
        elif 5170 <= freq <= 5825:
            return (freq - 5170) // 5 + 34
        return 0

    def _calculate_distance(self, rssi, freq):
        # FSPL = 20log10(d) + 20log10(f) - 147.55
        # d = 10 ^ ((FSPL - 20log10(f) + 147.55) / 20)
        # Simplified:
        # RSSI = TxPower - 10 * n * log10(d)
        # d = 10 ^ ((TxPower - RSSI) / (10 * n))
        tx_power = -30 # Assumed
        n = 2.5 # Environment factor
        if rssi >= tx_power: return 0.1
        try:
            return round(math.pow(10, (tx_power - rssi) / (10 * n)), 1)
        except:
            return 99.9

    def calculate_risk(self, device):
        score = 0
        # 1. Distance
        if device['distance'] < 5: score += 10
        if device['distance'] < 2: score += 20
        # 2. Security
        if 'OPEN' in device['security'] or 'WEP' in device['security']:
            score += 40
        elif 'WPS' in device['security']:
            score += 10
        # 3. Type
        if device['ssid'] == '[hidden]':
            score += 15
        
        return min(100, score)
