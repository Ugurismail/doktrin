# Kullanıcı Yönetim Komutları

## cleanup_inactive_users

Son 60 gün içinde direkt oy vermemiş kullanıcıları siler.

### Kullanım

```bash
# Dry-run modu (sadece göster, silme)
python manage.py cleanup_inactive_users --dry-run

# Gerçekten sil
python manage.py cleanup_inactive_users

# Farklı gün parametresi ile (örn: 30 gün)
python manage.py cleanup_inactive_users --days=30 --dry-run
```

### Parametreler

- `--dry-run`: Hangi kullanıcıların silineceğini gösterir, gerçekten silmez
- `--days`: Kaç gün inaktif kullanıcılar silinecek (varsayılan: 60)

### Önemli Notlar

1. **Kurucu üyeler asla silinmez** (`is_founder=True`)
2. Sadece **direkt oylar** sayılır (lider üzerinden otomatik verilen oylar sayılmaz)
3. Komut çalıştırılmadan önce **mutlaka --dry-run ile test edin**
4. Silme işlemi geri alınamaz, **onay ister**

### Otomatik Çalıştırma (Cron)

Her gün gece saat 03:00'te otomatik çalıştırmak için:

```bash
# Crontab'ı düzenle
crontab -e

# Şu satırı ekle:
0 3 * * * cd /path/to/doktrin-project && /path/to/venv/bin/python manage.py cleanup_inactive_users >> /var/log/doktrin_cleanup.log 2>&1
```

### Örnek Çıktı

```
60 gün önce: 2025-08-27 16:52:41

📊 İstatistikler:
  • Toplam kullanıcı: 324
  • Aktif kullanıcı (son 60 gün içinde oy vermiş): 107
  • Kurucu üye (korunuyor): 2
  • Silinecek inaktif kullanıcı: 215

📋 Silinecek kullanıcılar:
  • admin (hiç oy vermemiş)
  • user1_6 (hiç oy vermemiş)
  ...

✅ DRY RUN modu - Hiçbir kullanıcı silinmedi
```
