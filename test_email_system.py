#!/usr/bin/env python
"""
E-posta sistemi test scripti
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import User
from organization.models import Team
from doctrine.models import Proposal
from notifications.models import Announcement
from users.emails import send_welcome_email, send_team_invite_email, send_new_proposal_email, send_announcement_email
from datetime import datetime, timedelta

def test_emails():
    print("=" * 80)
    print("E-POSTA SİSTEMİ TEST BAŞLIYOR")
    print("=" * 80)

    # Test kullanıcısı al veya oluştur
    try:
        user = User.objects.filter(email__isnull=False, email__gt='').first()
        if not user:
            user = User.objects.create_user(
                username='test_email_user',
                email='test@example.com',
                password='testpass123',
                province='İstanbul',
                district='Kadıköy'
            )
            print(f"✓ Yeni test kullanıcısı oluşturuldu: {user.username}")
        else:
            print(f"✓ Mevcut kullanıcı kullanılıyor: {user.username} ({user.email})")
    except Exception as e:
        print(f"✗ Kullanıcı oluşturma hatası: {e}")
        return

    # 1. Hoş geldiniz e-postası testi
    print("\n" + "-" * 80)
    print("1. HOŞ GELDİNİZ E-POSTASI TESTİ")
    print("-" * 80)
    try:
        send_welcome_email(user)
        print("✓ Hoş geldiniz e-postası gönderildi!")
    except Exception as e:
        print(f"✗ Hata: {e}")

    # 2. Davet kodu e-postası testi
    print("\n" + "-" * 80)
    print("2. DAVET KODU E-POSTASI TESTİ")
    print("-" * 80)
    try:
        team = Team.objects.first()
        if team:
            send_team_invite_email(user, team, 'ABC123XY', datetime.now() + timedelta(days=7))
            print(f"✓ Davet kodu e-postası gönderildi! (Ekip: {team.display_name})")
        else:
            print("⚠ Test için ekip bulunamadı, bu testi atlıyoruz")
    except Exception as e:
        print(f"✗ Hata: {e}")

    # 3. Yeni öneri bildirimi e-postası testi
    print("\n" + "-" * 80)
    print("3. YENİ ÖNERİ BİLDİRİMİ E-POSTASI TESTİ")
    print("-" * 80)
    try:
        proposal = Proposal.objects.first()
        if proposal:
            send_new_proposal_email(user, proposal)
            print(f"✓ Öneri bildirimi e-postası gönderildi! (Öneri ID: {proposal.id})")
        else:
            print("⚠ Test için öneri bulunamadı, bu testi atlıyoruz")
    except Exception as e:
        print(f"✗ Hata: {e}")

    # 4. Duyuru e-postası testi
    print("\n" + "-" * 80)
    print("4. DUYURU E-POSTASI TESTİ")
    print("-" * 80)
    try:
        announcement = Announcement.objects.first()
        if announcement:
            send_announcement_email(user, announcement)
            print(f"✓ Duyuru e-postası gönderildi! (Başlık: {announcement.title})")
        else:
            print("⚠ Test için duyuru bulunamadı, bu testi atlıyoruz")
    except Exception as e:
        print(f"✗ Hata: {e}")

    print("\n" + "=" * 80)
    print("E-POSTA SİSTEMİ TESTİ TAMAMLANDI")
    print("=" * 80)
    print("\nNOT: Email backend 'console' modunda olduğu için e-postalar")
    print("     terminal çıktısında görünmelidir (yukarıda).")
    print("=" * 80)

if __name__ == '__main__':
    test_emails()
