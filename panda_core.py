import os
import json
import subprocess
import time
import math
import re
import threading
import socket
import urllib.request

class PandaScanner:
    def __init__(self):
        self.platform = self._detect_platform()
        self.lock = threading.Lock()
        self.devices = {} # Map BSSID/MAC -> Device Object
        self.location = {'lat': 0, 'lon': 0, 'provider': 'initializing'}

    def _detect_platform(self):
        if os.path.exists('/data/data/com.termux'):
            return 'termux'
        if os.path.exists('/dev/ish') or os.path.exists('/proc/ish') or os.path.exists('/etc/alpine-release'):
            return 'ish'
        return 'generic'

    def get_location(self):
        # Try local first
        try:
            if self.platform == 'termux':
                # Termux API location
                res = subprocess.check_output(['termux-location'], stderr=subprocess.DEVNULL)
                data = json.loads(res)
                return {
                    'lat': data.get('latitude'),
                    'lon': data.get('longitude'),
                    'provider': data.get('provider', 'gps')
                }
        except:
            pass
        
        # Fallback to IP Geolocation (Works on iSH too)
        try:
            with urllib.request.urlopen("https://ipapi.co/json/", timeout=2) as url:
                data = json.loads(url.read().decode())
                return {
                    'lat': data.get('latitude'),
                    'lon': data.get('longitude'),
                    'provider': 'ip-geo'
                }
        except:
            return {'lat': 0, 'lon': 0, 'provider': 'offline'}

    def scan(self):
        """Unified scan method returning list of devices"""
        wifi = []
        ble = []
        
        if self.platform == 'termux':
            wifi = self._scan_termux_wifi()
            ble = self._scan_termux_ble()
        elif self.platform == 'ish':
            # iSH "Aggressive" Network Scan
            wifi = self._scan_ish_network()
            ble = [] # Impossible on iSH standard
        else:
            wifi = self._scan_mock_wifi()
            ble = self._scan_mock_ble()

        # Merge
        current_time = time.time()
        with self.lock:
            for d in wifi + ble:
                mac = d['bssid']
                if mac in self.devices:
                    self.devices[mac].update(d)
                else:
                    self.devices[mac] = d
                self.devices[mac]['last_seen'] = current_time
            
            # Decay old devices (remove > 60s)
            self.devices = {k:v for k,v in self.devices.items() if current_time - v['last_seen'] < 60}
            
            return list(self.devices.values())

    # --- Termux Methods ---
    def _scan_termux_wifi(self):
        try:
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
                    'score': 0 
                })
            return scanned
        except Exception:
            return []

    def _scan_termux_ble(self):
        try:
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
                    'channel': 37,
                    'distance': self._calculate_distance(rssi, 2400),
                    'security': 'BLE',
                    'score': 0
                })
            return scanned
        except Exception:
            return []

    # --- iSH / Network Methods ---
    def _scan_ish_network(self):
        """
        Since iSH cannot access Wi-Fi radio hardware directly,
        we scan the local network (ARP table) to find nearby devices
        connected to the SAME network.
        """
        # 1. Broad Ping to populate ARP (Background)
        # We try to ping the broadcast addr if possible, or just look at existing ARP
        
        devices = []
        try:
            # Read ARP table
            output = subprocess.check_output(['cat', '/proc/net/arp'], stderr=subprocess.DEVNULL).decode()
            # Format: IP address       HW type     Flags       HW address            Mask     Device
            #         192.168.1.1      0x1         0x2         00:11:22:33:44:55     *        eth0
            
            lines = output.split('\n')[1:]
            for line in lines:
                parts = line.split()
                if len(parts) >= 6:
                    ip = parts[0]
                    mac = parts[3]
                    device = parts[5]
                    
                    if mac == '00:00:00:00:00:00': continue

                    # Latency check (simulated RSSI)
                    rssi_fake = self._measure_latency(ip)
                    
                    devices.append({
                        'type': 'LAN-NODE',
                        'ssid': f"DEV: {ip}",
                        'bssid': mac,
                        'rssi': rssi_fake,
                        'frequency': 2400,
                        'channel': 1,
                        'distance': self._calculate_distance(rssi_fake, 2400),
                        'security': 'CONNECTED',
                        'score': 0
                    })
        except:
            # Fallback for BSD style arp -a if proc is missing
            try:
                output = subprocess.check_output(['arp', '-a'], stderr=subprocess.DEVNULL).decode()
                for line in output.split('\n'):
                    # ? (192.168.1.1) at 00:11:22:33:44:55 on en0
                     if 'at' in line:
                        parts = line.split()
                        ip = parts[1].strip('()')
                        mac = parts[3]
                        rssi_fake = self._measure_latency(ip)
                        devices.append({
                            'type': 'LAN-NODE',
                            'ssid': f"DEV: {ip}",
                            'bssid': mac,
                            'rssi': rssi_fake,
                            'frequency': 2400,
                            'channel': 1,
                            'distance': self._calculate_distance(rssi_fake, 2400),
                            'security': 'CONNECTED',
                            'score': 0
                        })
            except:
                pass
                
        return devices

    def _measure_latency(self, ip):
        # Ping to estimate distance/signal quality
        try:
            # -c 1 = count 1, -W 1 = timeout 1s
            cmd = ['ping', '-c', '1', '-W', '1', ip]
            out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode()
            match = re.search(r'time=([\d\.]+)', out)
            if match:
                ms = float(match.group(1))
                # Map ms to RSSI roughly. >100ms = -90, <2ms = -40
                if ms < 2: return -40
                if ms > 100: return -90
                return int(-40 - (ms/2))
        except:
            pass
        return -80

    # --- Mock Methods (for Debug on Mac) ---
    def _scan_mock_wifi(self):
        return [{
            'type': 'WIFI',
            'ssid': 'Mock-WiFi-5G',
            'bssid': '00:11:22:33:44:55',
            'rssi': -55,
            'frequency': 5220,
            'channel': 44,
            'distance': 3.5,
            'security': 'WPA2',
            'score': 0
        }]

    def _scan_mock_ble(self):
        return []

    # --- Utils ---
    def _freq_to_channel(self, freq):
        if 2412 <= freq <= 2484:
            return (freq - 2412) // 5 + 1
        elif 5170 <= freq <= 5825:
            return (freq - 5170) // 5 + 34
        return 0

    def _calculate_distance(self, rssi, freq):
        tx_power = -30 
        n = 2.5 
        if rssi >= tx_power: return 0.1
        try:
            return round(math.pow(10, (tx_power - rssi) / (10 * n)), 1)
        except:
            return 99.9

    def calculate_risk(self, device):
        score = 0
        if device.get('distance', 100) < 5: score += 10
        if device.get('distance', 100) < 2: score += 20
        if 'OPEN' in device.get('security', ''): score += 40
        return min(100, score)
