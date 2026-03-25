#!/bin/bash
# Setup script for XMPP server and SPADE agents
# Run this in WSL: bash setup-xmpp.sh

set -e

echo "========================================"
echo "SHEM - XMPP Server Setup"
echo "========================================"
echo ""

# Try ejabberd first
if command -v ejabberdctl &> /dev/null; then
    echo "[✓] ejabberd already installed"
    echo "[→] Starting ejabberd service..."
    sudo service ejabberd start 2>/dev/null || {
        echo "[✗] ejabberd failed to start"
        USE_PROSODY=1
    }
elif sudo apt-cache search ejabberd 2>/dev/null | grep -q ejabberd; then
    echo "[→] Installing ejabberd..."
    sudo apt update
    sudo apt install -y ejabberd
    echo "[→] Starting ejabberd service..."
    sudo service ejabberd start 2>/dev/null || {
        echo "[✗] ejabberd failed to start"
        USE_PROSODY=1
    }
else
    echo "[✗] ejabberd not available in repos"
    USE_PROSODY=1
fi

# Fallback to Prosody if ejabberd failed
if [ "$USE_PROSODY" = "1" ]; then
    echo "[→] Falling back to Prosody (with TLS disabled)..."
    if ! command -v prosodyctl &> /dev/null; then
        echo "[→] Installing Prosody..."
        sudo apt update
        sudo apt install -y prosody
    fi
    
    echo "[→] Disabling TLS in Prosody config..."
    sudo sed -i 's/"tls";/--"tls";/' /etc/prosody/prosody.cfg.lua 2>/dev/null || true
    
    echo "[→] Starting Prosody service..."
    sudo service prosody restart
    sleep 2
    
    echo "[→] Registering agent accounts..."
    sudo prosodyctl adduser solar_sensor@localhost << EOF
sensor123
EOF
    sudo prosodyctl adduser home_manager@localhost << EOF
manager123
EOF
else
    # ejabberd succeeded
    sleep 2
    echo "[→] Registering agent accounts..."
    sudo ejabberdctl register solar_sensor localhost sensor123
    sudo ejabberdctl register home_manager localhost manager123
fi

echo ""
echo "[✓] XMPP server ready at localhost:5222"
echo ""
echo "========================================"
echo "SHEM - Agent Setup"
echo "========================================"
echo ""

# Setup Python environment
if [ ! -d ".venv-wsl" ]; then
    echo "[→] Creating virtual environment..."
    python3 -m venv .venv-wsl
fi

echo "[→] Activating virtual environment..."
source .venv-wsl/bin/activate

echo "[→] Installing dependencies..."
python -m pip install -U pip setuptools wheel > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1

echo ""
echo "[✓] Setup complete!"
echo ""
echo "To run the main simulation:"
echo "  source .venv-wsl/bin/activate"
echo "  python main.py"
echo ""
echo "To run the stress test:"
echo "  source .venv-wsl/bin/activate"
echo "  python stress_test.py"
echo ""
