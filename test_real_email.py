#!/usr/bin/env python
"""
Gerçek e-posta gönderimi test scripti (Gmail SMTP)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import User
from users.emails import send_welcome_email
from django.conf import settings

def test_real_email():
    print("=" * 80)
    print("GERÇEK E-POSTA GÖNDERİMİ TESTİ")
    print("=" * 80)

    # Email ayarlarını kontrol et
    print(f"\n📧 Email Backend: {settings.EMAIL_BACKEND}")
    print(f"📧 SMTP Host: {settings.EMAIL_HOST}")
    print(f"📧 SMTP Port: {settings.EMAIL_PORT}")
    print(f"📧 Email User: {settings.EMAIL_HOST_USER}")
    print(f"📧 From Email: {settings.DEFAULT_FROM_EMAIL}")

    if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
        print("\n❌ HATA: EMAIL_HOST_USER veya EMAIL_HOST_PASSWORD .env dosyasında tanımlanmamış!")
        print("Lütfen .env dosyasını kontrol edin.")
        return

    # Test kullanıcısı al
    user = User.objects.filter(email__isnull=False, email__gt='').first()
    if not user:
        print("\n❌ HATA: Email adresi olan kullanıcı bulunamadı!")
        return

    print(f"\n👤 Test Kullanıcısı: {user.username}")
    print(f"📧 Email Adresi: {user.email}")

    print("\n" + "-" * 80)
    print("E-POSTA GÖNDERİLİYOR...")
    print("-" * 80)

    try:
        send_welcome_email(user)
        print("\n✅ E-POSTA BAŞARIYLA GÖNDERİLDİ!")
        print(f"\n📬 Lütfen {user.email} adresinin gelen kutusunu kontrol edin.")
        print("   (Eğer görünmüyorsa spam/junk klasörüne bakın)")

    except Exception as e:
        print(f"\n❌ HATA: E-posta gönderilemedi!")
        print(f"Hata mesajı: {e}")
        print("\nOlası nedenler:")
        print("- Gmail App Password yanlış girilmiş olabilir")
        print("- Gmail hesabında 2-Step Verification kapalı olabilir")
        print("- İnternet bağlantısı problemi olabilir")

    print("\n" + "=" * 80)

if __name__ == '__main__':
    test_real_email()
