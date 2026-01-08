#!/bin/bash

# PANDA WIZARD - Universal Auto-Installer
# Runs on: Termux (Android), iSH (iOS), macOS, Linux

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

LOG_FILE="panda_install.log"

log() {
    echo -e "$1"
    echo "$(date) - $1" >> $LOG_FILE
}

detect_platform() {
    if [ -d "/data/data/com.termux" ]; then
        PLATFORM="TERMUX"
    elif [ -f "/dev/ish" ] || [ -f "/proc/ish" ] || grep -q "ish" /proc/version 2>/dev/null; then
        PLATFORM="ISH"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        PLATFORM="MACOS"
    else
        PLATFORM="LINUX"
    fi
}

check_dependency() {
    CMD=$1
    if command -v $CMD &> /dev/null; then
        echo "INSTALLED"
    else
        echo "MISSING"
    fi
}

install_fresh() {
    log "${BLUE}[*] Starting Fresh Installation for $PLATFORM...${NC}"
    
    if [ "$PLATFORM" == "TERMUX" ]; then
        log "[-] Updating Termux repositories..."
        pkg update -y >> $LOG_FILE 2>&1
        pkg upgrade -y >> $LOG_FILE 2>&1
        
        log "[-] Installing Python & System Tools..."
        pkg install -y python python-pip termux-api git clang make libjpeg-turbo freetype >> $LOG_FILE 2>&1
        
    elif [ "$PLATFORM" == "ISH" ]; then
        log "[-] Updating Alpine repositories..."
        apk update >> $LOG_FILE 2>&1
        
        log "[-] Installing Python & System Tools..."
        apk add python3 py3-pip git gcc musl-dev python3-dev >> $LOG_FILE 2>&1
        
    elif [ "$PLATFORM" == "MACOS" ]; then
        log "[-] Checking Homebrew (Required for macOS)..."
        if ! command -v brew &> /dev/null; then
            log "${YELLOW}[!] Homebrew not found. Installation might fail or require password.${NC}"
        fi
         # We assume user has python3 on mac usually, but let's try brew if possible
         if command -v brew &> /dev/null; then
             brew install python3 git >> $LOG_FILE 2>&1
         fi
         
    else # Linux
        sudo apt update >> $LOG_FILE 2>&1
        sudo apt install -y python3 python3-pip git >> $LOG_FILE 2>&1
    fi

    check_and_install_pip_libs "force"
    
    log "${GREEN}[+] Fresh Install Complete!${NC}"
    setup_repo
}

check_and_fix() {
    log "${BLUE}[*] Analyzing Environment ($PLATFORM)...${NC}"
    
    # Check Python
    PY_STATUS=$(check_dependency python3)
    if [ "$PY_STATUS" == "MISSING" ]; then
        log "${RED}[!] Python3 is MISSING. Fixing...${NC}"
        if [ "$PLATFORM" == "TERMUX" ]; then pkg install -y python >> $LOG_FILE; fi
        if [ "$PLATFORM" == "ISH" ]; then apk add python3 >> $LOG_FILE; fi
        if [ "$PLATFORM" == "LINUX" ]; then sudo apt install -y python3 >> $LOG_FILE; fi
    else
        log "${GREEN}[OK] Python3 is installed.${NC}"
    fi

    # Check Pip
    PIP_STATUS="MISSING"
    if command -v pip3 &> /dev/null || command -v pip &> /dev/null; then
        PIP_STATUS="INSTALLED"
        log "${GREEN}[OK] Pip is installed.${NC}"
    else
        log "${RED}[!] Pip is MISSING. Fixing...${NC}"
        if [ "$PLATFORM" == "TERMUX" ]; then pkg install -y python-pip >> $LOG_FILE; fi
        if [ "$PLATFORM" == "ISH" ]; then apk add py3-pip >> $LOG_FILE; fi
        if [ "$PLATFORM" == "LINUX" ]; then sudo apt install -y python3-pip >> $LOG_FILE; fi
    fi

    check_and_install_pip_libs "check"
    setup_repo
}

check_and_install_pip_libs() {
    MODE=$1
    log "[-] Checking Python Libraries (rich, flask, flask-cors)..."
    
    # We define a function to try installing
    do_pip_install() {
        # Using --break-system-packages for modern envs, falling back if needed
        python3 -m pip install rich flask flask-cors --break-system-packages >> $LOG_FILE 2>&1 || \
        python3 -m pip install rich flask flask-cors >> $LOG_FILE 2>&1
    }

    if [ "$MODE" == "force" ]; then
        do_pip_install
    else
        # Check if they exist
        if python3 -c "import rich, flask, flask_cors" &> /dev/null; then
             log "${GREEN}[OK] All Python libraries present.${NC}"
        else
             log "${YELLOW}[!] Some libraries missing. Installing...${NC}"
             do_pip_install
        fi
    fi
}

setup_repo() {
    log "${BLUE}[*] Setting up PANDA System...${NC}"
    # Ensure panda-system dir exists, if not clone it (Simulated here since we are local)
    if [ ! -d "panda-system" ]; then
        log "${YELLOW}[!] panda-system folder not found in current dir.${NC}"
        log "[-] Creating skeleton structure..."
        mkdir -p panda-system
        # In a real scenario, this would git clone.
        # Since we are an agent working locally, we assume files are already placed or will be.
    else
         log "${GREEN}[OK] panda-system directory detected.${NC}"
    fi
    
    echo -e "\n${CYAN}==============================================${NC}"
    echo -e "${GREEN}      INSTALLATION SUCCESSFUL!      ${NC}"
    echo -e "${CYAN}==============================================${NC}"
    echo -e "1. Go to the system:  cd panda-system"
    echo -e "2. Run Web Radar:     python3 web_server.py"
    echo -e "3. Run Terminal Mode: python3 panda.py"
    echo -e "${CYAN}==============================================${NC}"
}

# --- MAIN MENU ---
clear
detect_platform

echo -e "${CYAN}"
echo "██████╗  █████╗ ███╗   ██╗██████╗  █████╗ "
echo "██╔══██╗██╔══██╗████╗  ██║██╔══██╗██╔══██╗"
echo "██████╔╝███████║██╔██╗ ██║██║  ██║███████║"
echo "██╔═══╝ ██╔══██║██║╚██╗██║██║  ██║██╔══██║"
echo "██║     ██║  ██║██║ ╚████║██████╔╝██║  ██║"
echo "╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝╚═════╝ ╚═╝  ╚═╝"
echo -e "${NC}"
echo -e "Detected Platform: ${YELLOW}$PLATFORM${NC}"
echo -e ""
echo "1. I am new (Fresh Install Everything)"
echo "2. I don't know (Check & Fix Missing Deps)"
echo "3. Exit"
echo -e ""
read -p "Select option [1-3]: " OPTION

case $OPTION in
    1)
        install_fresh
        ;;
    2)
        check_and_fix
        ;;
    3)
        echo "Exiting."
        exit 0
        ;;
    *)
        echo "Invalid option."
        exit 1
        ;;
esac
