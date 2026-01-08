#!/bin/bash

# PANDA Installation Script
# Supports Termux (Android) and iSH (iOS)

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
echo "██████╗  █████╗ ███╗   ██╗██████╗  █████╗ "
echo "██╔══██╗██╔══██╗████╗  ██║██╔══██╗██╔══██╗"
echo "██████╔╝███████║██╔██╗ ██║██║  ██║███████║"
echo "██╔═══╝ ██╔══██║██║╚██╗██║██║  ██║██╔══██║"
echo "██║     ██║  ██║██║ ╚████║██████╔╝██║  ██║"
echo "╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝╚═════╝ ╚═╝  ╚═╝"
echo "PANDA - Passive Surveillance Defense"
echo -e "${NC}"

# Detect Environment
if [ -d "/data/data/com.termux" ]; then
    ENV="TERMUX"
    echo -e "[*] Detected Environment: ${GREEN}Termux${NC}"
elif [ -f "/dev/ish" ] || [ -f "/proc/ish" ]; then
    ENV="ISH"
    echo -e "[*] Detected Environment: ${GREEN}iSH (iOS)${NC}"
else
    ENV="GENERIC"
    echo -e "[*] Detected Environment: ${BLUE}Generic Linux${NC}"
fi

# Install System dependencies
echo -e "[*] Installing system dependencies..."

if [ "$ENV" == "TERMUX" ]; then
    pkg update -y
    pkg install -y python python-pip termux-api
    echo -e "[!] IMPORTANT: Please install the 'Termux:API' app from Play Store/F-Droid for full Wi-Fi support."
elif [ "$ENV" == "ISH" ]; then
    apk update
    apk add python3 py3-pip
elif [ "$ENV" == "GENERIC" ]; then
    # Assume Debian/Ubuntu for generic
    if command -v apt &> /dev/null; then
        sudo apt update
        sudo apt install -y python3 python3-pip
    fi
fi

# Install Python dependencies
echo -e "[*] Installing Python libraries..."
python3 -m pip install rich flask flask-cors --break-system-packages

echo -e "${GREEN}[+] PANDA Installation Complete!${NC}"
echo -e "${CYAN}[*] To start the Terminal HUD, run:${NC} python3 panda.py"
echo -e "${CYAN}[*] To start the Web Interface, run:${NC} python3 web_server.py"
echo -e "${CYAN}[*] Then open:${NC} http://localhost:5050"
