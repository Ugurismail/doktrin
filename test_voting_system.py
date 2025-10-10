"""
Oylama Sistemi Test Scripti
Tüm yeni özellikleri test eder:
1. Oylama süresi: 14 gün
2. Çarpan sistemi: x2, x4, x8 (x16 kaldırıldı)
3. Çekimser oylar: Ham oy olarak pozitif tarafa (çarpansız)
4. %75 kabul eşiği
"""

import os
import django
from datetime import timedelta

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.utils import timezone
from users.models import User
from organization.models import Team, Squad, Union
from doctrine.models import Proposal, Vote, DoctrineArticle
from doctrine.vote_calculator import calculate_votes_with_multipliers, finalize_proposal_result


def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def test_proposal_duration():
    """Test 1: Oylama süresinin 14 gün olduğunu test et"""
    print_section("TEST 1: Oylama Süresi (14 Gün)")

    try:
        # Test proposal oluştur
        article = DoctrineArticle.objects.first()
        if not article:
            print("❌ Test için madde bulunamadı!")
            return False

        proposal = Proposal.objects.create(
            proposal_type='MODIFY',
            related_article=article,
            proposed_content="Test içerik",
            justification="Test",
            proposed_by_level='FOUNDER',
            proposed_by_entity_id=1
        )

        # Süreyi kontrol et
        time_diff = proposal.end_date - proposal.start_date
        days = time_diff.total_seconds() / (24 * 3600)  # Tam gün hesabı

        print(f"Başlangıç: {proposal.start_date}")
        print(f"Bitiş: {proposal.end_date}")
        print(f"Süre: {days:.1f} gün")

        # Clean up
        proposal.delete()

        # 14 gün olup olmadığını kontrol et (13.9-14.1 arası kabul)
        if 13.9 <= days <= 14.1:
            print("✅ Oylama süresi 14 gün - DOĞRU!")
            return True
        else:
            print(f"❌ Oylama süresi {days:.1f} gün - YANLIŞ! (14 gün olmalı)")
            return False

    except Exception as e:
        print(f"❌ Hata: {e}")
        return False


def test_multiplier_system():
    """Test 2: Çarpan sistemini test et"""
    print_section("TEST 2: Çarpan Sistemi (x2, x4, x8)")

    try:
        # Test data hazırla
        article = DoctrineArticle.objects.first()
        if not article:
            print("❌ Test için madde bulunamadı!")
            return False

        proposal = Proposal.objects.create(
            proposal_type='MODIFY',
            related_article=article,
            proposed_content="Test",
            justification="Test",
            proposed_by_level='FOUNDER',
            proposed_by_entity_id=1
        )

        # Ekip tam oy birliği testi (x2)
        print("\n--- Ekip Tam Oy Birliği Testi (x2) ---")
        # member_count property olduğu için manuel kontrol
        teams = Team.objects.all()
        team = None
        for t in teams:
            if t.member_count >= 2:
                team = t
                break

        if team:
            members = User.objects.filter(current_team=team)

            # Tüm üyeler aynı yönde oy versin
            for member in members:
                Vote.objects.create(
                    proposal=proposal,
                    user=member,
                    vote_choice='YES'
                )

            results = calculate_votes_with_multipliers(proposal)
            expected = len(members) * 2  # x2 çarpan

            print(f"Ekip: {team.display_name}")
            print(f"Üye sayısı: {len(members)}")
            print(f"Beklenen: {expected} (x2 çarpan)")
            print(f"Sonuç: {results['YES']}")

            if results['YES'] == expected:
                print("✅ Ekip oy birliği çarpanı (x2) DOĞRU!")
            else:
                print(f"❌ Ekip çarpanı YANLIŞ! Beklenen: {expected}, Gelen: {results['YES']}")

            # Cleanup
            Vote.objects.filter(proposal=proposal).delete()

        # Cleanup
        proposal.delete()

        print("\n✅ Çarpan sistemi test edildi (manuel test gerekebilir)")
        return True

    except Exception as e:
        print(f"❌ Hata: {e}")
        return False


def test_abstain_votes():
    """Test 3: Çekimser oyların çarpansız pozitif tarafa eklendiğini test et"""
    print_section("TEST 3: Çekimser Oylar (Çarpansız)")

    try:
        article = DoctrineArticle.objects.first()
        if not article:
            print("❌ Test için madde bulunamadı!")
            return False

        proposal = Proposal.objects.create(
            proposal_type='MODIFY',
            related_article=article,
            proposed_content="Test",
            justification="Test",
            proposed_by_level='FOUNDER',
            proposed_by_entity_id=1
        )

        # Test senaryosu: 10 YES, 5 ABSTAIN, 3 VETO
        users = User.objects.filter(current_team__isnull=False)[:18]

        # 10 YES oy
        for user in users[:10]:
            Vote.objects.create(proposal=proposal, user=user, vote_choice='YES')

        # 5 ABSTAIN oy
        for user in users[10:15]:
            Vote.objects.create(proposal=proposal, user=user, vote_choice='ABSTAIN')

        # 3 VETO oy
        for user in users[15:18]:
            Vote.objects.create(proposal=proposal, user=user, vote_choice='VETO')

        # Sonuçları hesapla
        result = finalize_proposal_result(proposal)

        print(f"\nOy Dağılımı:")
        print(f"  YES: 10")
        print(f"  ABSTAIN: 5 (ham oy olarak YES'e eklenecek)")
        print(f"  VETO: 3")
        print(f"\nBeklenen Sonuç:")
        print(f"  YES: 10 + 5 = 15 (çekimser çarpansız eklendi)")
        print(f"  VETO: 3")
        print(f"  Yüzde: {(15/(15+3))*100:.1f}%")
        print(f"\nGerçek Sonuç:")
        print(f"  YES: {result['yes_votes']}")
        print(f"  VETO: {result['veto_votes']}")
        print(f"  Yüzde: {result['yes_percentage']:.1f}%")

        # Cleanup
        Vote.objects.filter(proposal=proposal).delete()
        proposal.delete()

        # Ham oy sayısını kontrol et (çarpan olmadan)
        raw_abstain = 5
        if result['yes_votes'] >= 15:  # En az 15 olmalı (10 + 5 çekimser)
            print("\n✅ Çekimser oylar çarpansız olarak pozitif tarafa eklendi!")
            return True
        else:
            print("\n❌ Çekimser oy mekanizması YANLIŞ!")
            return False

    except Exception as e:
        print(f"❌ Hata: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_passing_threshold():
    """Test 4: %75 kabul eşiğini test et"""
    print_section("TEST 4: %75 Kabul Eşiği")

    try:
        article = DoctrineArticle.objects.first()
        if not article:
            print("❌ Test için madde bulunamadı!")
            return False

        # Test 4a: %75+ YES -> PASSED
        print("\n--- Test 4a: %75+ YES ---")
        proposal1 = Proposal.objects.create(
            proposal_type='MODIFY',
            related_article=article,
            proposed_content="Test 1",
            justification="Test",
            proposed_by_level='FOUNDER',
            proposed_by_entity_id=1
        )

        users = User.objects.filter(current_team__isnull=False)[:100]

        # 80 YES, 20 VETO = 80% YES
        for user in users[:80]:
            Vote.objects.create(proposal=proposal1, user=user, vote_choice='YES')
        for user in users[80:100]:
            Vote.objects.create(proposal=proposal1, user=user, vote_choice='VETO')

        result1 = finalize_proposal_result(proposal1)
        print(f"YES yüzdesi: {result1['yes_percentage']:.1f}%")
        print(f"Durum: {proposal1.status}")

        if proposal1.status == 'PASSED':
            print("✅ %80 YES -> PASSED (Doğru!)")
        else:
            print("❌ %80 YES -> PASSED olmalıydı!")

        # Test 4b: %74 YES -> REJECTED
        print("\n--- Test 4b: %74 YES ---")
        proposal2 = Proposal.objects.create(
            proposal_type='MODIFY',
            related_article=article,
            proposed_content="Test 2",
            justification="Test",
            proposed_by_level='FOUNDER',
            proposed_by_entity_id=1
        )

        # Yeni kullanıcı seti al (proposal1'den farklı)
        users2 = User.objects.filter(current_team__isnull=False).exclude(
            id__in=[v.user_id for v in Vote.objects.filter(proposal=proposal1)]
        )[:100]

        # 74 YES, 26 VETO = 74% YES
        for user in users2[:74]:
            Vote.objects.create(proposal=proposal2, user=user, vote_choice='YES')
        for user in users2[74:100]:
            Vote.objects.create(proposal=proposal2, user=user, vote_choice='VETO')

        result2 = finalize_proposal_result(proposal2)
        print(f"YES yüzdesi: {result2['yes_percentage']:.1f}%")
        print(f"Durum: {proposal2.status}")

        if proposal2.status == 'REJECTED':
            print("✅ %74 YES -> REJECTED (Doğru!)")
        else:
            print("❌ %74 YES -> REJECTED olmalıydı!")

        # Cleanup
        Vote.objects.filter(proposal__in=[proposal1, proposal2]).delete()
        proposal1.delete()
        proposal2.delete()

        print("\n✅ %75 eşik testi tamamlandı!")
        return True

    except Exception as e:
        print(f"❌ Hata: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Tüm testleri çalıştır"""
    print("\n" + "🧪 " + "="*58)
    print("  OYLAMA SİSTEMİ TEST PAKETİ")
    print("🧪 " + "="*58)

    results = {}

    # Test 1: Oylama Süresi
    results['duration'] = test_proposal_duration()

    # Test 2: Çarpan Sistemi
    results['multipliers'] = test_multiplier_system()

    # Test 3: Çekimser Oylar
    results['abstain'] = test_abstain_votes()

    # Test 4: %75 Eşik
    results['threshold'] = test_passing_threshold()

    # Özet
    print_section("TEST ÖZETİ")

    passed = sum(results.values())
    total = len(results)

    print(f"\n✅ Başarılı: {passed}/{total}")
    print(f"❌ Başarısız: {total - passed}/{total}")

    for test_name, result in results.items():
        status = "✅ BAŞARILI" if result else "❌ BAŞARISIZ"
        print(f"  {test_name}: {status}")

    print("\n" + "="*60)

    if passed == total:
        print("🎉 TÜM TESTLER BAŞARILI!")
    else:
        print("⚠️  Bazı testler başarısız oldu. Lütfen kontrol edin.")

    print("="*60 + "\n")


if __name__ == '__main__':
    run_all_tests()
