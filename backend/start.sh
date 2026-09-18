#!/bin/bash

echo "[*] Ultimate Hacking Panel - Startup Script"
echo "[*] Installing dependencies..."

pip3 install -r requirements.txt

echo "[*] Creating directories..."
mkdir -p leaks wordlists payloads logs

echo "[*] Downloading wordlists..."
if [ ! -f "wordlists/rockyou.txt" ]; then
    echo "[*] Downloading rockyou.txt..."
    wget -q https://github.com/brannondorsey/naive-hashcat/releases/download/data/rockyou.txt -O wordlists/rockyou.txt
fi

echo "[*] Starting server..."
python3 app.py
