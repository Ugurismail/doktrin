"""
YENİ OYLAMA SİSTEMİ - LIQUID DEMOCRACY WITH HIERARCHICAL MULTIPLIERS

Temel Prensipler:
1. Lider Oy Ağırlığı:
   - Normal üye: 1 oy
   - Takım lideri: 2 oy (ekip lideri olmasa bile)
   - Birlik lideri: 3 oy
   - İl lideri: 4 oy

2. Otomatik Oy Kullandırma:
   - Lider oy verdiğinde, oy vermemiş üyeler liderle aynı oyu vermiş sayılır
   - Üye kendi oyunu verince, kendi oyu geçerli olur
   - Delege sistemi hala çalışır

3. Çarpan Sistemi (YENİ):
   - Ekip çarpanı (x2): Sadece takıma bağlı OLMAYAN ekipler
   - Takım çarpanı (x4): Sadece birliğe bağlı OLMAYAN takımlar
   - Birlik çarpanı (x8): Tüm birlikler
   - Çarpan için: Birlik lideri + TÜM alt liderler aynı oyu vermeli

4. Çekimser Oylar:
   - Önce EVET ve VETO çarpanlı sayılır
   - Hangisi çoksa, ÇEKİMSER oylar ona eklenir (çarpansız)

5. Kabul Eşiği:
   - Program (NORMAL_LAW): %75
   - İlke (FOUNDATION_LAW): %85
   - Hesaplama: Toplam üye sayısına göre
"""

from organization.models import Team, Squad, Union, ProvinceOrganization
from django.contrib.auth import get_user_model
from .models import Vote
from collections import defaultdict
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


def calculate_votes_with_multipliers(proposal):
    """
    YENİ ÇARPAN SİSTEMİ ile oyları hesapla

    Akış:
    1. Tüm kullanıcıların etkili oylarını topla (lider ağırlıklarıyla)
    2. Birlik seviyesinden başla (x8 potansiyeli)
    3. Standalone takımları işle (x4 potansiyeli)
    4. Standalone ekipleri işle (x2 potansiyeli)
    5. Örgütsüz üyeleri ekle
    """

    final_results = {'YES': 0, 'ABSTAIN': 0, 'VETO': 0}

    # 1. BİRLİK SEVİYESİ HESAPLAMA
    all_unions = Union.objects.filter(is_active=True)

    for union in all_unions:
        union_votes = process_union(union, proposal)
        for choice in ['YES', 'ABSTAIN', 'VETO']:
            final_results[choice] += union_votes[choice]

    # 2. STANDALONE TAKIMLAR (Birliğe bağlı OLMAYAN)
    standalone_squads = Squad.objects.filter(
        is_active=True,
        parent_union__isnull=True
    )

    for squad in standalone_squads:
        squad_votes = process_squad(squad, proposal)
        for choice in ['YES', 'ABSTAIN', 'VETO']:
            final_results[choice] += squad_votes[choice]

    # 3. STANDALONE EKİPLER (Takıma bağlı OLMAYAN)
    standalone_teams = Team.objects.filter(
        is_active=True,
        parent_squad__isnull=True
    )

    for team in standalone_teams:
        team_votes = process_team(team, proposal)
        for choice in ['YES', 'ABSTAIN', 'VETO']:
            final_results[choice] += team_votes[choice]

    # 4. ÖRGÜTSÜZ ÜYELER (Hiç ekibi olmayan)
    teamless_users = User.objects.filter(current_team__isnull=True)
    for user in teamless_users:
        vote = user.get_effective_vote_for(proposal)
        if vote:
            final_results[vote['choice']] += vote['weight']

    return final_results


def process_union(union, proposal):
    """
    Birlik seviyesi işleme (x8 çarpan potansiyeli)

    Çarpan Koşulu:
    - Birlik lideri oy vermiş
    - TÜM takım liderleri oy vermiş
    - TÜM takım liderleri aynı oyu vermiş
    - Takım liderleri birlik lideriyle aynı fikirde
    """

    # Birlik altındaki tüm takımları al
    squads = union.squads.filter(is_active=True)

    # Birlik lideri oyu
    union_leader_vote = None
    if union.leader:
        union_leader_vote_obj = Vote.objects.filter(
            user=union.leader,
            proposal=proposal
        ).first()
        if union_leader_vote_obj:
            union_leader_vote = union_leader_vote_obj.vote_choice

    # Tüm takım liderlerinin oylarını topla
    squad_leader_votes = []
    for squad in squads:
        if squad.leader:
            leader_vote = Vote.objects.filter(
                user=squad.leader,
                proposal=proposal
            ).first()
            if leader_vote:
                squad_leader_votes.append(leader_vote.vote_choice)

    # Tüm üyelerin etkili oylarını topla (ağırlıklarıyla)
    all_members = User.objects.filter(
        current_team__parent_squad__parent_union=union
    )

    union_result = {'YES': 0, 'ABSTAIN': 0, 'VETO': 0}

    for user in all_members:
        vote = user.get_effective_vote_for(proposal)
        if vote:
            union_result[vote['choice']] += vote['weight']

    # ÇARPAN KONTROLÜ
    if (union_leader_vote and
        len(squad_leader_votes) == len(squads) and  # TÜM takım liderleri oy verdi
        len(set(squad_leader_votes)) == 1 and  # Hepsi aynı oyu verdi
        squad_leader_votes[0] == union_leader_vote):  # Birlik lideriyle aynı

        # ÇARPAN UYGULA (x8)
        multiplied_choice = union_leader_vote
        union_result[multiplied_choice] *= 8

        logger.info(f"Birlik {union.name} için x8 çarpan uygulandı (Seçim: {multiplied_choice})")

    return union_result


def process_squad(squad, proposal):
    """
    Takım seviyesi işleme (x4 çarpan potansiyeli)

    Çarpan Koşulu:
    - Takım lideri oy vermiş
    - TÜM ekip liderleri oy vermiş
    - TÜM ekip liderleri aynı oyu vermiş
    - Ekip liderleri takım lideriyle aynı fikirde
    """

    # Takım altındaki tüm ekipleri al
    teams = squad.teams.filter(is_active=True)

    # Takım lideri oyu
    squad_leader_vote = None
    if squad.leader:
        squad_leader_vote_obj = Vote.objects.filter(
            user=squad.leader,
            proposal=proposal
        ).first()
        if squad_leader_vote_obj:
            squad_leader_vote = squad_leader_vote_obj.vote_choice

    # Tüm ekip liderlerinin oylarını topla
    team_leader_votes = []
    for team in teams:
        if team.leader:
            leader_vote = Vote.objects.filter(
                user=team.leader,
                proposal=proposal
            ).first()
            if leader_vote:
                team_leader_votes.append(leader_vote.vote_choice)

    # Tüm üyelerin etkili oylarını topla (ağırlıklarıyla)
    all_members = User.objects.filter(
        current_team__parent_squad=squad
    )

    squad_result = {'YES': 0, 'ABSTAIN': 0, 'VETO': 0}

    for user in all_members:
        vote = user.get_effective_vote_for(proposal)
        if vote:
            squad_result[vote['choice']] += vote['weight']

    # ÇARPAN KONTROLÜ
    if (squad_leader_vote and
        len(team_leader_votes) == len(teams) and  # TÜM ekip liderleri oy verdi
        len(set(team_leader_votes)) == 1 and  # Hepsi aynı oyu verdi
        team_leader_votes[0] == squad_leader_vote):  # Takım lideriyle aynı

        # ÇARPAN UYGULA (x4)
        multiplied_choice = squad_leader_vote
        squad_result[multiplied_choice] *= 4

        logger.info(f"Takım {squad.name} için x4 çarpan uygulandı (Seçim: {multiplied_choice})")

    return squad_result


def process_team(team, proposal):
    """
    Ekip seviyesi işleme (x2 çarpan potansiyeli)

    Çarpan Koşulu:
    - Ekip takıma bağlı DEĞİL (standalone)
    - TÜM üyeler oy vermiş
    - TÜM üyeler aynı oyu vermiş

    NOT: Takıma bağlı ekipler çarpan ALAMAZ (takım/birlik çarpanına dahil olurlar)
    """

    # Eğer ekip bir takıma bağlıysa, çarpan YOK
    if team.parent_squad is not None:
        # Bu ekip zaten takım seviyesinde işlendi
        # Burada tekrar sayma
        return {'YES': 0, 'ABSTAIN': 0, 'VETO': 0}

    # Tüm ekip üyelerinin etkili oylarını topla
    members = User.objects.filter(current_team=team)

    team_result = {'YES': 0, 'ABSTAIN': 0, 'VETO': 0}
    member_votes = []

    for user in members:
        vote = user.get_effective_vote_for(proposal)
        if vote:
            team_result[vote['choice']] += vote['weight']
            member_votes.append(vote['choice'])

    # ÇARPAN KONTROLÜ (Sadece standalone ekipler)
    if (len(member_votes) == team.member_count and  # Herkes oy verdi
        len(set(member_votes)) == 1):  # Hepsi aynı oyu verdi

        # ÇARPAN UYGULA (x2)
        multiplied_choice = member_votes[0]
        team_result[multiplied_choice] *= 2

        logger.info(f"Ekip {team.name} için x2 çarpan uygulandı (Seçim: {multiplied_choice})")

    return team_result


def add_abstain_votes_to_majority(results):
    """
    Çekimser oyları çoğunluğa ekle (çarpansız)

    Mantık:
    1. EVET ve VETO karşılaştır
    2. Hangisi çoksa, ÇEKİMSER oylar ona eklenir
    3. Eşitlikte EVET'e eklenir
    """

    yes_votes = results['YES']
    veto_votes = results['VETO']
    abstain_votes = results['ABSTAIN']

    if yes_votes >= veto_votes:
        # EVET çoğunluk (veya eşitlik)
        results['YES'] += abstain_votes
    else:
        # VETO çoğunluk
        results['VETO'] += abstain_votes

    results['ABSTAIN'] = 0  # Çekimser oylar dağıtıldı

    return results


def finalize_proposal_result(proposal):
    """
    Öneriyi sonuçlandır

    YENİ SİSTEM:
    1. Çarpanlı oyları hesapla
    2. Çekimser oyları çoğunluğa ekle
    3. Toplam üye sayısına göre yüzde hesapla
    4. İlke için %85, Program için %75 eşiği kontrol et
    """

    # 1. Çarpanlı oyları hesapla
    results = calculate_votes_with_multipliers(proposal)

    # 2. Çekimser oyları çoğunluğa ekle
    results = add_abstain_votes_to_majority(results)

    # 3. Toplam üye sayısını al (ekibi olan herkes)
    total_members = User.objects.filter(current_team__isnull=False).count()

    # Örgütsüz üyeleri de ekle
    total_members += User.objects.filter(current_team__isnull=True).count()

    yes_votes = results['YES']
    veto_votes = results['VETO']
    total_votes = yes_votes + veto_votes

    # Hiç oy yoksa ARŞİV
    if total_votes == 0:
        proposal.status = 'ARCHIVED'
        proposal.save()
        return {
            'yes_votes': 0,
            'veto_votes': 0,
            'yes_percentage': 0,
            'passed': False
        }

    # 4. Yüzde hesapla (toplam üye sayısına göre)
    yes_percentage = (yes_votes / total_members) * 100

    # 5. Eşik kontrolü
    if proposal.related_article and proposal.related_article.article_type == 'FOUNDATION_LAW':
        threshold = 85  # İlke için %85
    else:
        threshold = 75  # Program için %75

    if yes_percentage >= threshold:
        proposal.status = 'PASSED'
    else:
        proposal.status = 'REJECTED'

    proposal.save()

    logger.info(
        f"Öneri {proposal.id} sonuçlandı: {proposal.status} "
        f"(EVET: {yes_votes}/{total_members} = %{yes_percentage:.1f}, Eşik: %{threshold})"
    )

    return {
        'yes_votes': yes_votes,
        'veto_votes': veto_votes,
        'total_members': total_members,
        'yes_percentage': yes_percentage,
        'threshold': threshold,
        'passed': proposal.status == 'PASSED'
    }


def get_vote_breakdown(proposal):
    """
    Frontend için detaylı oy dağılımı

    Gösterir:
    - Kaç kişi direkt oy kullandı
    - Kaç kişi delege üzerinden
    - Kaç kişi ekip/takım/birlik lideri üzerinden
    - Çarpandan gelen ekstra oy sayısı
    """

    all_users = User.objects.all()

    breakdown = {
        'direct_votes': 0,
        'delegate_votes': 0,
        'team_leader_votes': 0,
        'squad_leader_votes': 0,
        'union_leader_votes': 0,
        'total_yes': 0,
        'total_veto': 0,
        'total_abstain': 0,
        'multiplier_bonus': 0,
    }

    for user in all_users:
        vote = user.get_effective_vote_for(proposal)
        if vote:
            # Kaynak türüne göre say
            breakdown[f"{vote['source']}_votes"] += 1

            # Toplama ekle
            breakdown[f"total_{vote['choice'].lower()}"] += vote['weight']

    # Çarpan bonusunu hesapla (çarpanlı - çarpansız)
    multiplied = calculate_votes_with_multipliers(proposal)

    # Çarpansız hesaplama için basit sayım
    base_yes = breakdown['total_yes']
    base_veto = breakdown['total_veto']
    base_abstain = breakdown['total_abstain']

    # Çarpan bonusu
    breakdown['multiplier_bonus'] = (
        (multiplied['YES'] - base_yes) +
        (multiplied['VETO'] - base_veto) +
        (multiplied['ABSTAIN'] - base_abstain)
    )

    # Çarpanlı sonuçları ekle
    breakdown['final_yes'] = multiplied['YES']
    breakdown['final_veto'] = multiplied['VETO']
    breakdown['final_abstain'] = multiplied['ABSTAIN']

    return breakdown
