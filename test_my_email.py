#!/usr/bin/env python
"""
Kendi Gmail adresime test e-postası gönder
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import User
from users.emails import send_welcome_email
from django.conf import settings

def test_my_email():
    print("=" * 80)
    print("KENDİ GMAIL ADRESİNE TEST E-POSTASI GÖNDERİLİYOR")
    print("=" * 80)

    # Mevcut kullanıcıyı al veya oluştur
    try:
        user = User.objects.get(username='test_gmail_user')
        # Email adresini güncelle
        user.email = 'uguraygun1@gmail.com'
        user.save()
        print(f"✓ Mevcut kullanıcı güncellendi: {user.username}")
    except User.DoesNotExist:
        # Yeni kullanıcı oluştur
        user = User.objects.create_user(
            username='test_gmail_user',
            email='uguraygun1@gmail.com',
            password='testpass123',
            province='İstanbul',
            district='Beşiktaş'
        )
        print(f"✓ Yeni kullanıcı oluşturuldu: {user.username}")

    print(f"\n📧 Gönderen: {settings.DEFAULT_FROM_EMAIL}")
    print(f"📧 Alıcı: {user.email}")

    print("\n" + "-" * 80)
    print("E-POSTA GÖNDERİLİYOR...")
    print("-" * 80)

    try:
        send_welcome_email(user)
        print("\n✅ E-POSTA BAŞARIYLA GÖNDERİLDİ!")
        print(f"\n📬 Lütfen {user.email} adresinin gelen kutusunu kontrol edin.")
        print("   Gmail'de gelen kutusuna veya spam klasörüne bakın!")
        print("\n💡 E-posta genellikle 10-30 saniye içinde gelir.")

    except Exception as e:
        print(f"\n❌ HATA: E-posta gönderilemedi!")
        print(f"Hata mesajı: {e}")

    print("\n" + "=" * 80)

if __name__ == '__main__':
    test_my_email()
