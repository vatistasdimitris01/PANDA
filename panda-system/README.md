# 🐼 PANDA - Passive Surveillance Defense System

PANDA is a tactical Terminal User Interface (TUI) for real-time signal awareness. Designed for travel, rentals, and field security.

## 🚀 Features
- **HUD Radar View**: Satellite-style signal map for immediate proximity awareness.
- **Intel Timeline**: Local logging of transient vs. static devices.
- **Risk Scoring**: Automatic threat assessment based on signal distance and security.
- **Offline-First**: Zero cloud connection, zero data leaks.
- **Cross-Platform**: Optimized for **Termux (Android)** and **iSH (iOS)**.

## 🛠 Installation

### Android (Termux)
1. Install [Termux](https://termux.dev/) and the [Termux:API](https://f-droid.org/en/packages/com.termux.api/) app.
2. In Termux, run:
```bash
git clone https://github.com/USER/panda-system.git
cd panda-system
bash install.sh
```

### iOS (iSH)
1. Install [iSH Shell](https://ish.app/) from the App Store.
2. In iSH, run:
```bash
bash install.sh
```

## 🎮 How to Use
Run the system with:
```bash
python3 panda.py
```

- **X**: Your location.
- **● / ▲**: Nearby signals (Green = Low Risk, Yellow = Alert, Red = High Risk).
- **HUD Radar**: Displays devices relative to their signal strength (distance).

## 🛡 Security Mode
- **No Cameras**: Pure radio frequency detection.
- **No Cloud**: All processing is done locally on your CPU.
- **Stealth**: PANDA is a passive listener. It does not broadcast your location.

## ⚠️ Requirements
- **Termux**: requires `Termux:API` app and package.
- **iSH**: uses network neighbor discovery (ARP) due to iOS hardware limitations.
