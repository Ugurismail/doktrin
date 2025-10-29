# 🚀 Bizlik - PythonAnywhere Deployment Rehberi

Bu rehber, Bizlik platformunu PythonAnywhere'e deploy etmek için adım adım talimatları içerir.

---

## 📋 Ön Hazırlık

### 1. Gmail App Password Alma

Email göndermek için Gmail App Password'e ihtiyacınız var:

1. Google hesabınıza gidin: https://myaccount.google.com/
2. **Security** → **2-Step Verification** (Aktif olmalı!)
3. **App passwords** → **Select app**: "Mail" → **Select device**: "Other"
4. İsim girin: "Bizlik PythonAnywhere"
5. **Generate** butonuna tıklayın
6. **16 haneli şifreyi kopyalayın** (boşluksuz: abcd efgh ijkl mnop)

---

## 🌐 PythonAnywhere'de Proje Kurulumu

### Adım 1: PythonAnywhere Hesabı

1. https://www.pythonanywhere.com/ adresine gidin
2. **Pricing & signup** → **Create a Beginner account** (ücretsiz)
3. Hesabınızı aktive edin

### Adım 2: GitHub'a Projeyi Yükleyin

**Yerel bilgisayarınızda:**

```bash
# Git'i başlatın (eğer başlatmadıysanız)
git init

# Tüm dosyaları ekleyin
git add .

# Commit oluşturun
git commit -m "Production deployment için hazır"

# GitHub'da yeni repo oluşturun ve ekleyin
git remote add origin https://github.com/KULLANICI_ADINIZ/bizlik.git
git branch -M main
git push -u origin main
```

### Adım 3: PythonAnywhere'de Bash Console

1. PythonAnywhere dashboard'da → **Consoles** → **Bash**
2. Projeyi klonlayın:

```bash
# GitHub'dan projeyi çekin
git clone https://github.com/KULLANICI_ADINIZ/bizlik.git
cd bizlik

# Virtual environment oluşturun (Python 3.11)
mkvirtualenv bizlik --python=/usr/bin/python3.11

# Gereksinimleri yükleyin
pip install -r requirements.txt
```

### Adım 4: Environment Variables (.env) Ayarlama

```bash
# .env dosyası oluşturun
nano .env
```

**Aşağıdaki içeriği yapıştırın ve değerleri doldurun:**

```bash
# Django Core Settings
DEBUG=False
SECRET_KEY=buraya-50-karakterden-uzun-rastgele-bir-key-girin
ALLOWED_HOSTS=KULLANICI_ADINIZ.pythonanywhere.com

# Site URL
SITE_URL=https://KULLANICI_ADINIZ.pythonanywhere.com

# Database (PythonAnywhere'de SQLite kullanıyoruz)
USE_POSTGRESQL=False

# Email Configuration (Gmail App Password)
EMAIL_HOST_USER=sizin-email@gmail.com
EMAIL_HOST_PASSWORD=abcdefghijklmnop
```

**Not:** `SECRET_KEY` üretmek için:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**Kaydet:** Ctrl+O, Enter, Ctrl+X

### Adım 5: Database Kurulumu

```bash
# Migrations çalıştırın
python manage.py migrate

# Static dosyaları toplayın
python manage.py collectstatic --noinput

# Superuser oluşturun
python manage.py createsuperuser
```

### Adım 6: Web App Yapılandırması

1. Dashboard → **Web** → **Add a new web app**
2. **Manual configuration** seçin → **Python 3.11**
3. **Configuration** sayfasında:

#### A. Source Code

```
Source code: /home/KULLANICI_ADINIZ/bizlik
Working directory: /home/KULLANICI_ADINIZ/bizlik
```

#### B. Virtualenv

```
Virtualenv: /home/KULLANICI_ADINIZ/.virtualenvs/bizlik
```

#### C. WSGI Configuration File

**Web sekmesinde WSGI configuration file linkine tıklayın** ve içeriği şununla değiştirin:

```python
import os
import sys

# Proje dizinini ekle
path = '/home/KULLANICI_ADINIZ/bizlik'
if path not in sys.path:
    sys.path.append(path)

# Django settings modülünü ayarla
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

# .env dosyasını yükle
from dotenv import load_dotenv
project_folder = os.path.expanduser(path)
load_dotenv(os.path.join(project_folder, '.env'))

# Django WSGI application'ı yükle
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

#### D. Static Files

**Web sekmesinde Static files bölümüne ekleyin:**

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/KULLANICI_ADINIZ/bizlik/staticfiles` |
| `/media/` | `/home/KULLANICI_ADINIZ/bizlik/media` |

### Adım 7: Reload & Test

1. **Web** sekmesinde **Reload** butonuna tıklayın
2. Site URL'nize gidin: `https://KULLANICI_ADINIZ.pythonanywhere.com`

---

## ✅ Deployment Checklist

- [ ] Gmail App Password alındı
- [ ] GitHub'a proje yüklendi
- [ ] PythonAnywhere hesabı oluşturuldu
- [ ] Proje klonlandı
- [ ] Virtual environment kuruldu
- [ ] Requirements yüklendi
- [ ] .env dosyası oluşturuldu ve dolduruldu
- [ ] Migrations çalıştırıldı
- [ ] Static files toplandı
- [ ] Superuser oluşturuldu
- [ ] WSGI configuration ayarlandı
- [ ] Static files path'leri eklendi
- [ ] Web app reload edildi
- [ ] Site test edildi ve çalışıyor

---

## 🔧 Güncelleme Yapmak

Projeyi güncellemek için:

```bash
# PythonAnywhere Bash Console'da
cd ~/bizlik
git pull origin main
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput

# Web sekmesinde Reload butonuna tıklayın
```

---

## 🐛 Sorun Giderme

### 1. "DisallowedHost" Hatası

`.env` dosyasında `ALLOWED_HOSTS` doğru mu kontrol edin.

### 2. Static Files Yüklenmiyor

```bash
python manage.py collectstatic --noinput
```
Web sekmesinde Static files path'leri doğru mu kontrol edin.

### 3. Email Gönderilmiyor

- Gmail App Password doğru mu?
- `.env` dosyasında boşluksuz mu?
- 2-Step Verification aktif mi?

### 4. Error Log'larını Görme

**Web** sekmesinde → **Log files** → **Error log** ve **Server log**

---

## 📞 Destek

PythonAnywhere forumları: https://www.pythonanywhere.com/forums/

---

**🎉 Tebrikler! Bizlik platformu artık canlıda!**
