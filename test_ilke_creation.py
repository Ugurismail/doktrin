import os
import django
from datetime import timedelta
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from doctrine.models import Proposal, Reference, ProposalReference, Vote

User = get_user_model()

print("=" * 80)
print("İLKE EKLEME SİSTEMİ TEST")
print("=" * 80)

# Önceki test verilerini temizle
print("\n0. Önceki test verileri temizleniyor...")
User.objects.filter(username__startswith='founder_test').delete()
User.objects.filter(username__startswith='voter_').delete()
print("   ✓ Test verileri temizlendi")

# 1. FOUNDER seviyesinde test kullanıcısı oluştur
print("\n1. Test kullanıcısı oluşturuluyor (FOUNDER seviyesi)...")
test_user = User.objects.create_user(
    username='founder_test',
    email='founder@test.com',
    password='testpass123',
    province='İstanbul',
    district='Kadıköy',
    is_founder=True  # Kurucu yetkisi
)
print(f"   ✓ Kurucu kullanıcı oluşturuldu: {test_user.username} (is_founder: {test_user.is_founder})")

# 2. İlke önerisi oluştur
print("\n2. İlke önerisi oluşturuluyor...")
proposal = Proposal.objects.create(
    proposal_type='ADD',
    proposed_article_type='FOUNDATION_LAW',  # İLKE
    proposed_content='Tüm üyeler eşit haklara sahiptir. Hiçbir üye, ırk, cinsiyet, etnik köken, din, dil veya sosyal statü nedeniyle ayrımcılığa uğratılamaz.',
    justification='Eşitlik ve adalet temel ilkelerimizdendir. Bu ilke, tüm örgütsel yapılanmamızın temelini oluşturur.',
    proposed_tags='İnsan Hakları,Örgütlenme',
    created_by=test_user,
    proposed_by_level='FOUNDER',
    proposed_by_entity_id=0,
    status='ACTIVE',  # check_proposal_deadlines ACTIVE status arıyor
    start_date=timezone.now() - timedelta(days=15),  # 15 gün önce başlamış
    end_date=timezone.now() - timedelta(hours=1)  # Süresi dolmuş
)
print(f"   ✓ İlke önerisi oluşturuldu (ID: {proposal.id})")
print(f"     Tür: {proposal.get_proposed_article_type_display()}")
print(f"     İçerik: {proposal.proposed_content[:80]}...")

# 3. 10 adet kaynak ekle
print("\n3. 10 adet kaynak ekleniyor...")
references_data = [
    ("Birleşmiş Milletler", "İnsan Hakları Evrensel Beyannamesi", 1948, "https://www.un.org/tr/universal-declaration-human-rights/"),
    ("Türkiye Cumhuriyeti", "Türkiye Cumhuriyeti Anayasası - Madde 10", 1982, "https://www.mevzuat.gov.tr/"),
    ("Avrupa Konseyi", "Avrupa İnsan Hakları Sözleşmesi - Madde 14", 1950, "https://www.echr.coe.int/"),
    ("ILO", "Sözleşme No. 111 - İşte ve Meslekte Ayrımcılık", 1958, "https://www.ilo.org/"),
    ("Birleşmiş Milletler", "CEDAW - Kadınlara Karşı Her Türlü Ayrımcılığın Önlenmesi Sözleşmesi", 1979, "https://www.un.org/womenwatch/daw/cedaw/"),
    ("Birleşmiş Milletler", "ICERD - Irk Ayrımcılığının Önlenmesi Sözleşmesi", 1965, "https://www.ohchr.org/"),
    ("Birleşmiş Milletler", "CRPD - Engelli Hakları Sözleşmesi Madde 5", 2006, "https://www.un.org/disabilities/"),
    ("Birleşmiş Milletler", "ICESCR - Ekonomik, Sosyal ve Kültürel Haklar Sözleşmesi", 1966, "https://www.ohchr.org/"),
    ("ILO", "Temel İlkeler Bildirisi - İşçi Hakları", 1998, "https://www.ilo.org/"),
    ("AGİT", "Helsinki Nihai Senedi - İnsan Hakları", 1975, "https://www.osce.org/")
]

for i, (author, title, year, url) in enumerate(references_data, 1):
    # Global kaynak oluştur
    ref = Reference.objects.create(
        created_by=test_user,
        reference_type='WEBSITE',
        author=author,
        title=title,
        year=year,
        url=url
    )
    # Öneriye bağla
    ProposalReference.objects.create(
        reference=ref,
        proposal=proposal
    )
    print(f"   ✓ Kaynak {i}/10: {title}")

# 4. Test için oy kullanacak kullanıcılar oluştur
print("\n4. Test kullanıcıları oluşturuluyor (toplam 100 kullanıcı)...")
voters = []
for i in range(100):
    voter = User.objects.create_user(
        username=f'voter_{i}',
        email=f'voter_{i}@test.com',
        password='testpass123',
        province='İstanbul',
        district='Kadıköy'
    )
    voters.append(voter)

print(f"   ✓ {len(voters)} kullanıcı oluşturuldu")

# 5. %92 onay sağlayacak şekilde oylar oluştur
print("\n5. Oylar oluşturuluyor (%92 EVET oyu)...")
yes_votes = 92
abstain_votes = 5
veto_votes = 3

vote_count = 0
for i, voter in enumerate(voters):
    if i < yes_votes:
        vote_choice = 'YES'
    elif i < yes_votes + abstain_votes:
        vote_choice = 'ABSTAIN'
    else:
        vote_choice = 'VETO'

    Vote.objects.create(
        proposal=proposal,
        user=voter,
        vote_choice=vote_choice
    )
    vote_count += 1

print(f"   ✓ {yes_votes} EVET oyu")
print(f"   ✓ {abstain_votes} ÇEKİMSER oyu")
print(f"   ✓ {veto_votes} VETO oyu")
print(f"   Toplam: {vote_count} oy")
print(f"   Onay oranı: {(yes_votes/vote_count)*100:.1f}%")

# Proposal'ın oy sayılarını güncelle
proposal.vote_yes_count = yes_votes
proposal.vote_abstain_count = abstain_votes
proposal.vote_veto_count = veto_votes
proposal.save()
print(f"   ✓ Öneri oy sayıları güncellendi")

# 6. Otomatik finalize işlemini tetikle
print("\n6. Otomatik finalize işlemi tetikleniyor...")
print("   (check_proposal_deadlines komutu çalıştırılıyor...)")

from django.core.management import call_command
call_command('check_proposal_deadlines')

# 7. Sonuçları kontrol et
print("\n7. Sonuçlar kontrol ediliyor...")
proposal.refresh_from_db()

print(f"\n   Öneri Durumu: {proposal.get_status_display()}")
print(f"   Oy Durumu:")
print(f"     - EVET: {proposal.vote_yes_count}")
print(f"     - VETO: {proposal.vote_veto_count}")
print(f"     - ÇEKİMSER: {proposal.vote_abstain_count}")

if proposal.status == 'PASSED':
    print("\n   ✅ ÖNERİ KABUL EDİLDİ!")

    # İlkenin oluşturulduğunu kontrol et
    from doctrine.models import DoctrineArticle

    ilke = DoctrineArticle.objects.filter(
        article_type='FOUNDATION_LAW'
    ).order_by('-created_date').first()

    if ilke:
        print(f"\n   ✅ YENİ İLKE OLUŞTURULDU!")
        print(f"      - Madde No: {ilke.article_number}")
        print(f"      - Tür: {ilke.get_article_type_display()}")
        print(f"      - İçerik: {ilke.content[:100]}...")
        print(f"      - Gerekçe: {ilke.justification[:100]}...")

        # Kaynakları kontrol et
        ref_count = ProposalReference.objects.filter(proposal=proposal).count()
        print(f"      - Kaynak sayısı: {ref_count}")

        # Etiketleri kontrol et
        tags = ilke.tags.all()
        print(f"      - Etiketler: {', '.join([tag.name for tag in tags])}")

        print("\n" + "=" * 80)
        print("TEST BAŞARIYLA TAMAMLANDI! ✅")
        print("=" * 80)
    else:
        print("\n   ❌ HATA: İlke oluşturulamadı!")
else:
    print(f"\n   ❌ ÖNERİ REDDEDİLDİ! (Durum: {proposal.get_status_display()})")

print("\nTest tamamlandı!")
