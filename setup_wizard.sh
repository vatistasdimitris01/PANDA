#!/bin/bash

# PANDA SYSTEM - COMMAND CENTER
# Runs on: Termux (Android), iSH (iOS), macOS, Linux

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

LOG_FILE="panda_install.log"
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYSTEM_DIR="$BASE_DIR/panda-system"

# --- SYSTEM UTILS ---

log() {
    # Echo to file only, quiet UI
    echo "$(date) - $1" >> "$SYSTEM_DIR/$LOG_FILE"
}

detect_platform() {
    if [ -d "/data/data/com.termux" ]; then
        PLATFORM="TERMUX"
        RC_FILE="$HOME/.bashrc"
    elif [ -f "/dev/ish" ] || [ -f "/proc/ish" ] || grep -q "ish" /proc/version 2>/dev/null; then
        PLATFORM="ISH"
        RC_FILE="$HOME/.profile"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        PLATFORM="MACOS"
        RC_FILE="$HOME/.zshrc"
    else
        PLATFORM="LINUX"
        RC_FILE="$HOME/.bashrc"
    fi
}

install_alias() {
    echo -e "${BLUE}[*] Creating 'panda' shortcut...${NC}"
    if grep -q "alias panda=" "$RC_FILE"; then
        echo -e "${YELLOW}[!] Alias already exists in $RC_FILE${NC}"
    else
        echo "alias panda=\"bash $BASE_DIR/setup_wizard.sh\"" >> "$RC_FILE"
        echo -e "${GREEN}[+] Shortcut added!${NC}"
        echo -e "    Run: ${CYAN}source $RC_FILE${NC} or restart shell to use 'panda'."
    fi
    sleep 2
}

check_dependencies() {
    MISSING=0
    # Check Python
    if ! command -v python3 &> /dev/null; then MISSING=1; fi
    # Check PipLibs
    if ! python3 -c "import rich, flask, flask_cors" &> /dev/null; then MISSING=1; fi
    
    if [ $MISSING -eq 1 ]; then
        echo -e "${YELLOW}[!] Missing required packages/libraries.${NC}"
        read -p "    Auto-install now? (Y/n): " CONFIRM
        if [[ "$CONFIRM" =~ ^[Nn]$ ]]; then
            echo "Skipping installation. System may fail."
            sleep 1
        else
            install_deps
        fi
    fi
}

install_deps() {
    echo -e "${BLUE}[*] Installing Dependencies for $PLATFORM...${NC}"
    
    if [ "$PLATFORM" == "TERMUX" ]; then
        pkg update -y >> "$SYSTEM_DIR/$LOG_FILE" 2>&1
        pkg install -y python python-pip termux-api >> "$SYSTEM_DIR/$LOG_FILE" 2>&1
    elif [ "$PLATFORM" == "ISH" ]; then
        apk update >> "$SYSTEM_DIR/$LOG_FILE" 2>&1
        apk add python3 py3-pip >> "$SYSTEM_DIR/$LOG_FILE" 2>&1
    elif [ "$PLATFORM" == "MACOS" ]; then
         if ! command -v python3 &> /dev/null; then brew install python3; fi
    else
        sudo apt update >> "$SYSTEM_DIR/$LOG_FILE" 2>&1
        sudo apt install -y python3 python3-pip >> "$SYSTEM_DIR/$LOG_FILE" 2>&1
    fi

    echo -e "${BLUE}[*] Installing Python Libraries...${NC}"
    python3 -m pip install rich flask flask-cors --break-system-packages >> "$SYSTEM_DIR/$LOG_FILE" 2>&1 || \
    python3 -m pip install rich flask flask-cors >> "$SYSTEM_DIR/$LOG_FILE" 2>&1
    
    echo -e "${GREEN}[+] Check Complete.${NC}"
    sleep 1
}

run_web_server() {
    clear
    echo -e "${CYAN}===================================${NC}"
    echo -e "${GREEN}    PANDA WEB RADAR ACTIVE${NC}"
    echo -e "${CYAN}===================================${NC}"
    echo -e "Server: http://localhost:5050"
    echo -e "${YELLOW}[INFO] Press 'q' to Stop and Return.${NC}"
    
    # Kill any existing
    pkill -f web_server.py > /dev/null 2>&1
    
    # Start background
    cd "$SYSTEM_DIR"
    python3 web_server.py > "$SYSTEM_DIR/server.log" 2>&1 &
    SERVER_PID=$!
    
    # Input Loop
    while true; do
        read -rsn1 key
        if [[ "$key" == "q" ]]; then
            echo -e "\n${RED}[!] Stopping Server...${NC}"
            kill $SERVER_PID
            wait $SERVER_PID 2>/dev/null
            break
        fi
    done
}

run_terminal_ui() {
    clear
    cd "$SYSTEM_DIR"
    python3 panda.py
}

# --- MAIN LOOP ---
detect_platform
mkdir -p "$SYSTEM_DIR"

while true; do
    clear
    echo -e "${CYAN}"
    echo " 🐼 PANDA COMMAND CENTER "
    echo -e "${NC}"
    echo -e "Platform: ${YELLOW}$PLATFORM${NC}"
    echo "---------------------------"
    echo "1. Start Web Radar (SOPHIA)"
    echo "2. Start Terminal HUD"
    echo "3. Install/Fix Dependencies"
    echo "4. Create 'panda' Shortcut"
    echo "Q. Quit"
    echo "---------------------------"
    read -p "Select >> " OPT

    case $OPT in
        1)
            check_dependencies
            run_web_server
            ;;
        2)
            check_dependencies
            run_terminal_ui
            ;;
        3)
            install_deps
            read -p "Press Enter to continue..."
            ;;
        4)
            install_alias
            read -p "Press Enter to continue..."
            ;;
        [Qq])
            echo "Exiting..."
            exit 0
            ;;
        *)
            ;;
    esac
done
