# Doktrin Platform - Production Deployment Guide

Bu dokümanda Doktrin platformunun production sunucusuna nasıl deploy edileceği anlatılmaktadır.

## 📋 Gereksinimler

- Python 3.11+
- PostgreSQL (önerilen) veya MySQL
- Redis (opsiyonel, caching için)
- SMTP Email servisi (Gmail veya başka)
- Domain adı ve SSL sertifikası

---

## 🚀 Adım Adım Deployment

### 1. Sunucu Hazırlığı

```bash
# Sistem güncellemeleri
sudo apt update && sudo apt upgrade -y

# Python ve pip kurulumu
sudo apt install python3.11 python3.11-venv python3-pip -y

# PostgreSQL kurulumu (önerilen)
sudo apt install postgresql postgresql-contrib -y

# Nginx kurulumu (web server)
sudo apt install nginx -y

# Git kurulumu
sudo apt install git -y
```

### 2. Veritabanı Oluşturma

```bash
# PostgreSQL veritabanı oluştur
sudo -u postgres psql

# PostgreSQL içinde:
CREATE DATABASE doktrin_db;
CREATE USER doktrin_user WITH PASSWORD 'güçlü_şifre_buraya';
ALTER ROLE doktrin_user SET client_encoding TO 'utf8';
ALTER ROLE doktrin_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE doktrin_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE doktrin_db TO doktrin_user;
\q
```

### 3. Proje Dosyalarını Sunucuya Yükleme

```bash
# Proje dizini oluştur
cd /var/www/
sudo mkdir doktrin
sudo chown $USER:$USER doktrin
cd doktrin

# Git ile projeyi çek
git clone <repository-url> .
git checkout feature/ux-improvements  # veya production branch
```

### 4. Python Virtual Environment

```bash
# Virtual environment oluştur
python3.11 -m venv venv

# Aktif et
source venv/bin/activate

# Dependencies yükle
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn psycopg2-binary python-dotenv
```

### 5. Environment Variables (.env dosyası)

```bash
# .env dosyası oluştur
nano .env
```

`.env` dosyasının içeriği:

```bash
# Django Settings
SECRET_KEY='production-secret-key-buraya-50-karakter-rastgele'
DEBUG=False
ALLOWED_HOSTS=doktrin.com,www.doktrin.com,sunucu-ip-adresi

# Database (PostgreSQL)
DB_NAME=doktrin_db
DB_USER=doktrin_user
DB_PASSWORD=güçlü_şifre_buraya
DB_HOST=localhost
DB_PORT=5432

# Email Configuration (Gmail)
EMAIL_HOST_USER=uguraygun1@gmail.com
EMAIL_HOST_PASSWORD=iyhk zdsp wgvv aeqb

# Site URL
SITE_URL=https://doktrin.com
```

Dosya izinlerini güvenli hale getir:
```bash
chmod 600 .env
```

### 6. settings.py Güncellemeleri

Production için `config/settings.py` dosyasını güncelle:

```python
import os
from dotenv import load_dotenv

load_dotenv()

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'fallback-key-for-dev')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost').split(',')

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'doktrin_db'),
        'USER': os.getenv('DB_USER', 'doktrin_user'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# Site URL
SITE_URL = os.getenv('SITE_URL', 'http://localhost:8000')

# Static files (production)
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Security Settings (Production)
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
```

### 7. Django Hazırlık Komutları

```bash
# Static dosyaları topla
python manage.py collectstatic --noinput

# Migrations çalıştır
python manage.py migrate

# Superuser oluştur
python manage.py createsuperuser

# Test et (development server)
python manage.py runserver 0.0.0.0:8000
```

### 8. Gunicorn Yapılandırması

Gunicorn systemd servis dosyası oluştur:

```bash
sudo nano /etc/systemd/system/doktrin.service
```

İçerik:

```ini
[Unit]
Description=Doktrin Gunicorn daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/doktrin
Environment="PATH=/var/www/doktrin/venv/bin"
ExecStart=/var/www/doktrin/venv/bin/gunicorn \
          --workers 3 \
          --bind unix:/var/www/doktrin/doktrin.sock \
          config.wsgi:application

[Install]
WantedBy=multi-user.target
```

Servisi başlat:

```bash
sudo systemctl start doktrin
sudo systemctl enable doktrin
sudo systemctl status doktrin
```

### 9. Nginx Yapılandırması

Nginx site yapılandırması:

```bash
sudo nano /etc/nginx/sites-available/doktrin
```

İçerik:

```nginx
server {
    listen 80;
    server_name doktrin.com www.doktrin.com;

    location = /favicon.ico { access_log off; log_not_found off; }

    location /static/ {
        alias /var/www/doktrin/staticfiles/;
    }

    location /media/ {
        alias /var/www/doktrin/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/doktrin/doktrin.sock;
    }
}
```

Siteyi aktif et:

```bash
sudo ln -s /etc/nginx/sites-available/doktrin /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 10. SSL Sertifikası (Let's Encrypt)

```bash
# Certbot kur
sudo apt install certbot python3-certbot-nginx -y

# SSL sertifikası al
sudo certbot --nginx -d doktrin.com -d www.doktrin.com

# Otomatik yenileme testi
sudo certbot renew --dry-run
```

---

## 🔄 Güncelleme İşlemleri

Yeni bir güncelleme deploy etmek için:

```bash
cd /var/www/doktrin

# Kodları çek
git pull origin feature/ux-improvements

# Virtual environment aktif et
source venv/bin/activate

# Yeni dependencies varsa yükle
pip install -r requirements.txt

# Migration varsa çalıştır
python manage.py migrate

# Static dosyaları güncelle
python manage.py collectstatic --noinput

# Servisleri yeniden başlat
sudo systemctl restart doktrin
sudo systemctl restart nginx
```

---

## 🔧 Bakım ve İzleme

### Log Dosyaları

```bash
# Gunicorn logs
sudo journalctl -u doktrin -f

# Nginx logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

### Veritabanı Backup

```bash
# Backup oluştur
pg_dump doktrin_db > backup_$(date +%Y%m%d).sql

# Backup'tan geri yükle
psql doktrin_db < backup_20250101.sql
```

### Cron Jobs

Süresi dolmuş davet kodlarını temizlemek için:

```bash
# Crontab düzenle
crontab -e

# Her gece 03:00'te çalıştır
0 3 * * * cd /var/www/doktrin && /var/www/doktrin/venv/bin/python manage.py runcrons
```

---

## ⚠️ Güvenlik Kontrol Listesi

- [ ] DEBUG=False olduğundan emin ol
- [ ] SECRET_KEY production için rastgele 50 karakter
- [ ] ALLOWED_HOSTS doğru domain'leri içeriyor
- [ ] SSL sertifikası yüklü ve çalışıyor
- [ ] .env dosyası izinleri 600
- [ ] .env dosyası git'e gitmiyor (.gitignore'da)
- [ ] PostgreSQL şifresi güçlü
- [ ] Firewall aktif (sadece 80, 443, 22 portları açık)
- [ ] Email credentials güvenli
- [ ] Static files doğru serve ediliyor
- [ ] Admin panel /admin/ erişilebilir

---

## 📧 Email Yapılandırması

### Gmail Kullanıyorsanız

1. Gmail hesabınızda 2-Step Verification aktif olmalı
2. App Password oluşturun: https://myaccount.google.com/apppasswords
3. `.env` dosyasına ekleyin:
   ```
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=16-haneli-app-password
   ```

### Alternatif Email Servisleri

**SendGrid (Önerilen - Günde 100 ücretsiz email)**
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'apikey'
EMAIL_HOST_PASSWORD = 'sendgrid-api-key-buraya'
```

**AWS SES (Ölçeklenebilir)**
```python
EMAIL_BACKEND = 'django_ses.SESBackend'
AWS_ACCESS_KEY_ID = 'your-access-key'
AWS_SECRET_ACCESS_KEY = 'your-secret-key'
AWS_SES_REGION_NAME = 'eu-west-1'
AWS_SES_REGION_ENDPOINT = 'email.eu-west-1.amazonaws.com'
```

---

## 🐛 Yaygın Sorunlar ve Çözümleri

### Static dosyalar yüklenmiyor
```bash
python manage.py collectstatic --noinput
sudo systemctl restart nginx
```

### 502 Bad Gateway
```bash
sudo systemctl status doktrin
sudo journalctl -u doktrin -n 50
```

### Database bağlantı hatası
```bash
# PostgreSQL çalışıyor mu?
sudo systemctl status postgresql

# .env dosyasındaki credentials doğru mu?
cat .env
```

### Email gönderilmiyor
```bash
# Django shell ile test et
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Test mesajı', 'from@example.com', ['to@example.com'])
```

---

## 📚 Ek Kaynaklar

- Django Deployment Checklist: https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/
- Nginx Dokumentasyonu: https://nginx.org/en/docs/
- Let's Encrypt: https://letsencrypt.org/
- Gunicorn Deployment: https://docs.gunicorn.org/en/stable/deploy.html

---

**Son Güncelleme:** 2025-10-11
**Platform Versiyonu:** 1.0.0-beta
