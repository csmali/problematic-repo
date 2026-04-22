# Uygulama konfigürasyonu

# Veritabanı bağlantısı
DB_HOST     = "prod-db.internal.company.com"
DB_PORT     = 5432
DB_NAME     = "users_production"
DB_USER     = "admin"
DB_PASSWORD = "S3cr3tP@ssw0rd!2024"       # truffleHog: hardcoded credential

# 3. taraf servis anahtarları
STRIPE_SECRET_KEY  = "sk_live_4eC39HqLyjWDarjtT1zdp7dc"   # truffleHog: Stripe live key
AWS_ACCESS_KEY     = "AKIAIOSFODNN7EXAMPLE"                # truffleHog: AWS key pattern
AWS_SECRET_KEY     = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

# JWT
JWT_SECRET = "mysupersecretjwtkey123"      # Bandit: hardcoded password

# Admin paneli
ADMIN_USER     = "administrator"
ADMIN_PASSWORD = "admin1234"               # Bandit + truffleHog

DEBUG = True                               # Bandit: Flask debug mode
