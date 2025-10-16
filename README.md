# 📜 Doktrin Platform

Topluluk tabanlı siyasi örgütlenme ve doktrin yönetim platformu. Liquid democracy prensipleriyle çalışan, hiyerarşik organizasyon ve demokratik karar alma sistemi.

## 🎯 Özellikler

### 📊 Hiyerarşik Organizasyon
- **4 Seviyeli Yapı**: Ekip → Takım → Birlik → İl Örgütü
- **Matematiksel Üye Gereksinimleri**: Her seviye için belirli minimum üye sayısı
- **Coğrafi Organizasyon**: İl ve ilçe bazlı yapılanma

### 🗳️ Demokratik Oylama
- **Çarpan Mekanizması**: Hiyerarşik oy ağırlıklandırma
- **14 Günlük Oylama Süresi**: Her öneri için standart süre
- **Oy Seçenekleri**: Evet, Çekimser, Veto
- **Oy Değiştirme**: 24 saat bekleme süresi ile

### 👑 Sürekli Lider Seçimi
- **Oy Birliği Mekanizması**: Tüm oylar aynı adaya giderse lider değişir
- **Seviye Bazlı Oylama**: Her seviyede farklı oy yetkisi
- **Bildirim Sistemi**: Lider değişimlerinde otomatik bildirim

### 📝 Doktrin Yönetimi
- **2 Madde Türü**: İlkeler ve Yasalar
- **5 Öneri Türü**: Ekleme, Değiştirme, Silme, İsim Değişikliği, Kurucu Revizyonu
- **Versiyon Kontrol**: Her değişiklik kaydedilir
- **Akademik Kaynak Sistemi**: Önerilere kaynak/atıf ekleme

### 🔮 Tahmin Sistemi
- **Öngörülülük Puanı**: Doğru tahminlerle puan kazanma
- **3 Günlük Doğrulama**: Tahmin süresi dolunca topluluk doğrular
- **Takip Sistemi**: Tahminleri takip edebilme

### 🔔 Bildirim Sistemi
- **Gerçek Zamanlı**: Anlık bildirimler
- **Filtreleme**: Okunmuş/okunmamış ayrımı
- **Otomatik Temizlik**: 30 gün sonra eski bildirimler silinir
- **Email Entegrasyonu**: Önemli olaylar için email

## 🚀 Kurulum

### Gereksinimler
- Python 3.11+
- pip
- virtualenv (önerilir)

### Adımlar

1. **Projeyi Klonlayın**
```bash
git clone https://github.com/YOUR_USERNAME/doktrin-project.git
cd doktrin-project
```

2. **Virtual Environment Oluşturun**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# veya
venv\Scripts\activate  # Windows
```

3. **Bağımlılıkları Yükleyin**
```bash
pip install -r requirements.txt
```

4. **Environment Değişkenlerini Ayarlayın**
```bash
cp .env.example .env
# .env dosyasını düzenleyin:
# - SECRET_KEY'i değiştirin
# - EMAIL ayarlarını yapılandırın (opsiyonel)
```

5. **Veritabanını Hazırlayın**
```bash
python manage.py migrate
```

6. **Süper Kullanıcı Oluşturun**
```bash
python manage.py createsuperuser
```

7. **Sunucuyu Başlatın**
```bash
python manage.py runserver
```

Uygulama `http://127.0.0.1:8000/` adresinde çalışacak.

## 📦 Proje Yapısı

```
doktrin-project/
├── config/              # Django ayarları
├── users/               # Kullanıcı yönetimi
├── organization/        # Organizasyon yapısı
├── doctrine/            # Doktrin maddeleri ve öneriler
├── notifications/       # Bildirim sistemi
├── predictions/         # Tahmin sistemi
├── templates/           # HTML şablonları
├── static/              # CSS, JS, images
├── media/               # Kullanıcı yüklemeleri
├── manage.py
├── requirements.txt
└── README.md
```

## 🔒 Güvenlik

### Production Ortamı İçin
1. `DEBUG = False` yapın
2. `SECRET_KEY`'i güçlü bir değer ile değiştirin
3. `ALLOWED_HOSTS`'u ayarlayın
4. HTTPS kullanın
5. Güçlü veritabanı şifreleri kullanın
6. Rate limiting aktif

### Hassas Bilgiler
- `.env` dosyası Git'e eklenmez (`.gitignore`)
- Email şifreleri ve API anahtarları `.env`'de
- `db.sqlite3` Git'e eklenmez

## 🧪 Test

```bash
# Tüm testleri çalıştır
python manage.py test

# Kapsamlı test scripti
python test_comprehensive.py
```

## 📊 Organizasyon Gereksinimleri

| Seviye | Min Üye | Min Alt Birim | Oluşturma Yetkisi |
|--------|---------|---------------|-------------------|
| Ekip | 3 | - | Herkes |
| Takım | 45 | 3 ekip | Ekip Liderleri |
| Birlik | 135 | 3 takım | Takım Liderleri |
| İl Örgütü | 375 | 3 birlik | Birlik Liderleri |

## 🎯 Öneri Oluşturma Yetkileri

| Seviye | Öneri Hakkı | Özel Yetki |
|--------|-------------|------------|
| Ekip | ✅ Evet (8+ üye gerekli) | - |
| Takım | ✅ Evet | - |
| Birlik | ✅ Evet | İlkeleri değiştirebilir |
| İl Örgütü | ✅ Evet | - |
| Kurucu | ✅ Evet | Her şeyi değiştirebilir |

## 🛠️ Teknolojiler

- **Backend**: Django 5.2.2
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Database**: SQLite3 (development), PostgreSQL (production önerilir)
- **Authentication**: Django Auth
- **Email**: SMTP (Gmail)
- **Task Scheduling**: django-crontab

## 📝 Lisans

Bu proje şu anda lisanssızdır. Kullanım koşulları için proje sahibi ile iletişime geçin.

## 👥 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Değişikliklerinizi commit edin (`git commit -m 'feat: Add amazing feature'`)
4. Branch'inizi push edin (`git push origin feature/amazing-feature`)
5. Pull Request açın

## 📧 İletişim

Proje Sahibi: [GitHub Kullanıcı Adınız]

Proje Linki: [https://github.com/YOUR_USERNAME/doktrin-project](https://github.com/YOUR_USERNAME/doktrin-project)

## 🙏 Teşekkürler

Bu platform, topluluk tabanlı demokratik karar alma süreçlerini dijitalleştirmek amacıyla geliştirilmiştir.

---

Made with ❤️ by Doktrin Team
