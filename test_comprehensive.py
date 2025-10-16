#!/usr/bin/env python
"""
DOKTRİN SİSTEMİ KAPSAMLI TEST SCRIPTI
Tüm örgütlenme seviyelerini ve öneri sistemini test eder
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import User, InviteCode
from organization.models import Team, Squad, Union, ProvinceOrganization, OrganizationFormationProposal, FormationVote, LeaderVote
from doctrine.models import DoctrineArticle, Proposal, Vote, ArticleTag
from django.utils import timezone
from datetime import timedelta
import random

class TestReport:
    def __init__(self):
        self.results = []
        self.errors = []

    def log(self, test_name, status, message=""):
        result = f"{'✅' if status else '❌'} {test_name}"
        if message:
            result += f" - {message}"
        self.results.append(result)
        print(result)

    def error(self, test_name, error_msg):
        err = f"🔴 ERROR in {test_name}: {error_msg}"
        self.errors.append(err)
        print(err)

    def print_summary(self):
        print("\n" + "="*60)
        print("TEST RAPORU ÖZETI")
        print("="*60)
        passed = len([r for r in self.results if r.startswith('✅')])
        failed = len([r for r in self.results if r.startswith('❌')])
        print(f"Toplam Test: {len(self.results)}")
        print(f"Başarılı: {passed}")
        print(f"Başarısız: {failed}")
        print(f"Hata: {len(self.errors)}")

        if self.errors:
            print("\n=== HATALAR ===")
            for err in self.errors:
                print(err)

report = TestReport()

print("="*60)
print("DOKTRİN SİSTEMİ KAPSAMLI TEST")
print("="*60)

# TEST 1: KULLANICI OLUŞTURMA
print("\n[1] KULLANICI OLUŞTURMA TESTİ")
print("-"*40)

provinces = ["İstanbul", "Ankara", "İzmir"]
districts = {
    "İstanbul": ["Kadıköy", "Beşiktaş", "Şişli", "Üsküdar"],
    "Ankara": ["Çankaya", "Keçiören", "Mamak", "Yenimahalle"],
    "İzmir": ["Konak", "Karşıyaka", "Bornova", "Buca"]
}

# Her ilden 50'şer kullanıcı oluştur (toplam 150) - daha fazla ekip için
created_users = []
for province in provinces:
    for i in range(50):
        district = districts[province][i % len(districts[province])]
        username = f"test_{province[:3].lower()}_{i+1}"

        # Zaten varsa atla
        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            created_users.append(user)
            continue

        try:
            user = User.objects.create_user(
                username=username,
                email=f"{username}@test.com",
                password="test123",
                province=province,
                district=district
            )
            created_users.append(user)
            report.log(f"Kullanıcı: {username}", True, f"{province}/{district}")
        except Exception as e:
            report.error(f"Kullanıcı oluşturma: {username}", str(e))

print(f"\nToplam kullanıcı: {User.objects.count()}")

# TEST 2: EKİP OLUŞTURMA (Her ilçeden 4 ekip = 48 ekip)
print("\n[2] EKİP OLUŞTURMA TESTİ")
print("-"*40)

created_teams = []
for province in provinces:
    for district in districts[province]:
        # Her ilçeden 4 ekip oluştur
        for team_num in range(1, 5):
            team_name = f"{district} {team_num}"

            # Zaten varsa atla
            if Team.objects.filter(official_name=team_name).exists():
                team = Team.objects.get(official_name=team_name)
                created_teams.append(team)
                continue

            # Bu ilçeden bir kullanıcı bul
            potential_leaders = User.objects.filter(
                province=province,
                district=district,
                current_team__isnull=True
            )

            if not potential_leaders.exists():
                report.log(f"Ekip: {team_name}", False, "Lider bulunamadı")
                continue

            leader = potential_leaders.first()

            try:
                team = Team.objects.create(
                    official_name=team_name,
                    custom_name=f"Test Ekip {len(created_teams)+1}",
                    district=district,
                    province=province,
                    leader=leader
                )

                # Lideri ekibe ata
                leader.current_team = team
                leader.save()

                # 10-15 arası üye ekle (öneri oluşturabilsin ve takım oluşturabilsin)
                team_size = random.randint(10, 15)
                potential_members = User.objects.filter(
                    province=province,
                    district=district,
                    current_team__isnull=True
                ).exclude(id=leader.id)[:team_size-1]

                for member in potential_members:
                    member.current_team = team
                    member.save()

                created_teams.append(team)
                report.log(f"Ekip: {team_name}", True, f"{team.member_count} üye")
            except Exception as e:
                report.error(f"Ekip oluşturma: {team_name}", str(e))

print(f"\nToplam ekip: {Team.objects.count()}")

# TEST 3: TAKIM OLUŞTURMA (Her ilden 1 takım = 3 takım)
print("\n[3] TAKIM OLUŞTURMA TESTİ")
print("-"*40)

created_squads = []
for province in provinces:
    squad_name = f"{province} Takımı"

    # Zaten varsa atla
    if Squad.objects.filter(name=squad_name).exists():
        squad = Squad.objects.get(name=squad_name)
        created_squads.append(squad)
        continue

    # Bu ildeki ekipleri al (min 3 ekip gerekli)
    province_teams = Team.objects.filter(province=province, parent_squad__isnull=True)[:3]

    if province_teams.count() < 3:
        report.log(f"Takım: {squad_name}", False, f"Yeterli ekip yok ({province_teams.count()}/3)")
        continue

    # Toplam üye sayısını kontrol et (min 45)
    total_members = sum([team.member_count for team in province_teams])
    if total_members < 45:
        report.log(f"Takım: {squad_name}", False, f"Yeterli üye yok ({total_members}/45)")
        continue

    # Lider seç (ilk ekip lideri)
    leader = province_teams[0].leader

    try:
        # Öneri oluştur
        proposal = OrganizationFormationProposal.objects.create(
            level='SQUAD',
            proposed_name=squad_name,
            proposed_leader=leader,
            participating_entities=[str(team.id) for team in province_teams]
        )

        # Tüm ekip liderlerinin onayını simüle et
        for team in province_teams:
            FormationVote.objects.create(
                formation_proposal=proposal,
                voter=team.leader,
                vote='APPROVE'
            )

        # Takımı oluştur
        squad = Squad.objects.create(
            name=squad_name,
            province=province,
            leader=leader
        )

        # Ekipleri takıma bağla
        province_teams.update(parent_squad=squad)

        proposal.status = 'APPROVED'
        proposal.save()

        created_squads.append(squad)
        report.log(f"Takım: {squad_name}", True, f"{squad.team_count} ekip, {squad.member_count} üye")
    except Exception as e:
        report.error(f"Takım oluşturma: {squad_name}", str(e))

print(f"\nToplam takım: {Squad.objects.count()}")

# TEST 4: BİRLİK OLUŞTURMA (İstanbul'da 1 birlik)
print("\n[4] BİRLİK OLUŞTURMA TESTİ")
print("-"*40)

union_name = "İstanbul Birliği"
istanbul_squads = Squad.objects.filter(province="İstanbul", parent_union__isnull=True)

if istanbul_squads.count() >= 3:
    # Toplam üye kontrolü (min 135)
    total_members = sum([squad.member_count for squad in istanbul_squads[:3]])

    if total_members >= 135:
        # Zaten varsa atla
        if Union.objects.filter(name=union_name).exists():
            union = Union.objects.get(name=union_name)
            report.log(f"Birlik: {union_name}", True, "Zaten mevcut")
        else:
            try:
                leader = istanbul_squads[0].leader

                # Öneri oluştur
                proposal = OrganizationFormationProposal.objects.create(
                    level='UNION',
                    proposed_name=union_name,
                    proposed_leader=leader,
                    participating_entities=[str(squad.id) for squad in istanbul_squads[:3]]
                )

                # Tüm takım liderlerinin onayını simüle et
                for squad in istanbul_squads[:3]:
                    FormationVote.objects.create(
                        formation_proposal=proposal,
                        voter=squad.leader,
                        vote='APPROVE'
                    )

                # Birliği oluştur
                union = Union.objects.create(
                    name=union_name,
                    province="İstanbul",
                    leader=leader
                )

                # Takımları birliğe bağla
                istanbul_squads[:3].update(parent_union=union)

                proposal.status = 'APPROVED'
                proposal.save()

                report.log(f"Birlik: {union_name}", True, f"{union.squad_count} takım, {union.member_count} üye")
            except Exception as e:
                report.error(f"Birlik oluşturma: {union_name}", str(e))
    else:
        report.log(f"Birlik: {union_name}", False, f"Yeterli üye yok ({total_members}/135)")
else:
    report.log(f"Birlik: {union_name}", False, f"Yeterli takım yok ({istanbul_squads.count()}/3)")

print(f"\nToplam birlik: {Union.objects.count()}")

# TEST 5: YENİ MADDE EKLEME ÖNERİSİ
print("\n[5] YENİ MADDE EKLEME ÖNERİSİ TESTİ")
print("-"*40)

# Ekip seviyesinden öneri oluştur (8+ üyeli ekip bul)
test_team = None
for team in Team.objects.all():
    if team.member_count >= 8:
        test_team = team
        break
if test_team and test_team.leader:
    try:
        # Etiket oluştur
        tag, _ = ArticleTag.objects.get_or_create(
            name="Test Kategori",
            slug="test-kategori",
            defaults={'color': '#3B82F6'}
        )

        proposal = Proposal.objects.create(
            proposal_type='ADD',
            proposed_content="Test maddesi: Bu bir test yasasıdır.",
            justification="Test amaçlı oluşturulmuştur.",
            proposed_by_level='TEAM',
            proposed_by_entity_id=test_team.id,
            end_date=timezone.now() + timedelta(days=14)
        )
        report.log("Yeni madde önerisi", True, f"Proposal #{proposal.id}")

        # Oy kullanımını test et
        team_members = User.objects.filter(current_team=test_team)[:5]
        votes_cast = 0
        for member in team_members:
            vote_choice = random.choice(['YES', 'ABSTAIN', 'VETO'])
            Vote.objects.create(
                proposal=proposal,
                user=member,
                vote_choice=vote_choice
            )
            votes_cast += 1

        report.log("Oy kullanımı", True, f"{votes_cast} oy")
    except Exception as e:
        report.error("Yeni madde önerisi", str(e))
else:
    report.log("Yeni madde önerisi", False, "Uygun ekip bulunamadı")

# TEST 6: MADDE DEĞİŞTİRME ÖNERİSİ
print("\n[6] MADDE DEĞİŞTİRME ÖNERİSİ TESTİ")
print("-"*40)

existing_article = DoctrineArticle.objects.filter(article_type='NORMAL_LAW').first()
if existing_article and test_team:
    try:
        proposal = Proposal.objects.create(
            proposal_type='MODIFY',
            related_article=existing_article,
            original_article_content=existing_article.content,
            proposed_content=existing_article.content + " [DEĞİŞİKLİK: Test eklentisi]",
            justification="Test amaçlı değişiklik önerisi",
            proposed_by_level='TEAM',
            proposed_by_entity_id=test_team.id,
            end_date=timezone.now() + timedelta(days=14)
        )
        report.log("Madde değiştirme önerisi", True, f"Proposal #{proposal.id}, Madde #{existing_article.article_number}")
    except Exception as e:
        report.error("Madde değiştirme önerisi", str(e))
else:
    report.log("Madde değiştirme önerisi", False, "Madde veya ekip bulunamadı")

# TEST 7: MADDE SİLME ÖNERİSİ
print("\n[7] MADDE SİLME ÖNERİSİ TESTİ")
print("-"*40)

if existing_article and test_team:
    try:
        proposal = Proposal.objects.create(
            proposal_type='REMOVE',
            related_article=existing_article,
            original_article_content=existing_article.content,
            proposed_content=f"[Madde {existing_article.article_number} kaldırılıyor]",
            justification="Test amaçlı silme önerisi",
            proposed_by_level='TEAM',
            proposed_by_entity_id=test_team.id,
            end_date=timezone.now() + timedelta(days=14)
        )
        report.log("Madde silme önerisi", True, f"Proposal #{proposal.id}")
    except Exception as e:
        report.error("Madde silme önerisi", str(e))
else:
    report.log("Madde silme önerisi", False, "Madde veya ekip bulunamadı")

# TEST 8: LİDER SEÇİMİ
print("\n[8] LİDER SEÇİMİ TESTİ")
print("-"*40)

if test_team:
    try:
        # Ekipteki tüm üyeler bir adaya oy birliği ile oy verseler
        team_members = User.objects.filter(current_team=test_team)
        new_leader_candidate = team_members.exclude(id=test_team.leader.id).first()

        if new_leader_candidate:
            # Oy birliği simüle et
            for member in team_members:
                LeaderVote.objects.update_or_create(
                    voter=member,
                    voter_level='TEAM',
                    defaults={'candidate': new_leader_candidate}
                )

            # Manuel lider değişimi kontrolü (normalde sistem otomatik yapar)
            votes = LeaderVote.objects.filter(voter__current_team=test_team, voter_level='TEAM')
            unique_candidates = set(votes.values_list('candidate_id', flat=True))

            if len(unique_candidates) == 1 and votes.count() == test_team.member_count:
                report.log("Lider seçimi - Oy birliği", True, f"Tüm oylar {new_leader_candidate.username}'e")
            else:
                report.log("Lider seçimi - Oy birliği", False, "Oy birliği sağlanamadı")
        else:
            report.log("Lider seçimi", False, "Aday bulunamadı")
    except Exception as e:
        report.error("Lider seçimi", str(e))
else:
    report.log("Lider seçimi", False, "Test ekibi yok")

# ÖZET İSTATİSTİKLER
print("\n" + "="*60)
print("SİSTEM DURUMU - SON HAL")
print("="*60)
print(f"Kullanıcılar: {User.objects.count()}")
print(f"Ekipler: {Team.objects.count()}")
print(f"  - 8+ üyeli ekipler: {Team.objects.filter(members__isnull=False).distinct().count()}")
print(f"Takımlar: {Squad.objects.count()}")
print(f"Birlikler: {Union.objects.count()}")
print(f"İl Örgütleri: {ProvinceOrganization.objects.count()}")
print(f"Doktrin Maddeleri: {DoctrineArticle.objects.count()}")
print(f"Aktif Öneriler: {Proposal.objects.filter(status='ACTIVE').count()}")
print(f"Toplam Öneriler: {Proposal.objects.count()}")
print(f"Toplam Oylar: {Vote.objects.count()}")

# İller bazında detay
print(f"\nİL BAZINDA DURUM:")
for province in provinces:
    teams = Team.objects.filter(province=province).count()
    squads = Squad.objects.filter(province=province).count()
    unions = Union.objects.filter(province=province).count()
    print(f"  {province}: {teams} ekip, {squads} takım, {unions} birlik")

# RAPOR ÖZETI
report.print_summary()
