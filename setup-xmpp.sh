#!/bin/bash
# Setup script for XMPP server and SPADE agents
# Run this in WSL: bash setup-xmpp.sh

echo "========================================"
echo "SHEM - XMPP Server Setup"
echo "========================================"
echo ""

USE_PROSODY=0

# Try ejabberd first
if command -v ejabberdctl &> /dev/null; then
    echo "[✓] ejabberd already installed"
    echo "[→] Starting ejabberd service..."
    if sudo service ejabberd start 2>/dev/null; then
        sleep 2
        echo "[✓] ejabberd started successfully"
        echo "[→] Registering agent accounts..."
        sudo ejabberdctl register solar_sensor localhost sensor123
        sudo ejabberdctl register home_manager localhost manager123
    else
        echo "[✗] ejabberd failed to start - falling back to Prosody"
        USE_PROSODY=1
    fi
elif sudo apt-cache search ejabberd 2>/dev/null | grep -q ejabberd; then
    echo "[→] Installing ejabberd..."
    sudo apt update >/dev/null 2>&1
    if sudo apt install -y ejabberd >/dev/null 2>&1; then
        echo "[→] Starting ejabberd service..."
        if sudo service ejabberd start 2>/dev/null; then
            sleep 2
            echo "[✓] ejabberd started successfully"
            echo "[→] Registering agent accounts..."
            sudo ejabberdctl register solar_sensor localhost sensor123
            sudo ejabberdctl register home_manager localhost manager123
        else
            echo "[✗] ejabberd failed to start - falling back to Prosody"
            USE_PROSODY=1
        fi
    else
        echo "[✗] ejabberd install failed - falling back to Prosody"
        USE_PROSODY=1
    fi
else
    echo "[!] ejabberd not found in repos - using Prosody"
    USE_PROSODY=1
fi

# Fallback to Prosody if needed
if [ "$USE_PROSODY" = "1" ]; then
    echo ""
    echo "[→] Setting up Prosody (with TLS disabled)..."
    if ! command -v prosodyctl &> /dev/null; then
        echo "[→] Installing Prosody..."
        sudo apt update >/dev/null 2>&1
        sudo apt install -y prosody >/dev/null 2>&1
    fi
    
    echo "[→] Disabling TLS in Prosody config..."
    sudo sed -i 's/"tls";/--"tls";/g' /etc/prosody/prosody.cfg.lua 2>/dev/null || true
    
    echo "[→] Starting Prosody service..."
    sudo service prosody restart >/dev/null 2>&1
    sleep 3
    
    echo "[→] Registering agent accounts..."
    echo "sensor123" | sudo prosodyctl adduser solar_sensor@localhost 2>/dev/null
    echo "manager123" | sudo prosodyctl adduser home_manager@localhost 2>/dev/null
    
    # Verify Prosody is listening
    if nc -zv 127.0.0.1 5222 >/dev/null 2>&1; then
        echo "[✓] Prosody ready at localhost:5222"
    else
        echo "[✗] WARNING: Prosody may not be listening on 5222"
    fi
fi

echo ""
echo "[✓] XMPP server setup complete"
echo ""
echo "========================================"
echo "SHEM - Python Environment Setup"
echo "========================================"
echo ""

# Setup Python environment
if [ ! -d ".venv-wsl" ]; then
    echo "[→] Creating virtual environment..."
    python3 -m venv .venv-wsl
fi

echo "[→] Activating virtual environment..."
source .venv-wsl/bin/activate

echo "[→] Installing Python dependencies..."
python -m pip install -U pip setuptools wheel >/dev/null 2>&1
pip install -r requirements.txt >/dev/null 2>&1

echo ""
echo "[✓] Setup complete!"
echo ""
echo "Next steps:"
echo "  1. source .venv-wsl/bin/activate"
echo "  2. python main.py              (open-ended simulation)"
echo "  3. python stress_test.py       (bounded evaluation)"
echo ""
