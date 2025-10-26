from organization.models import Team, Squad, Union, ProvinceOrganization
from .models import Vote
from collections import defaultdict

def calculate_votes_with_multipliers(proposal):
    """
    Çarpan mekanizması ile oyları hesapla
    - Ekip tam oy birliği: x2
    - Takım liderleri tam oy birliği: Takımın TOPLAM oyu x4
    - Birlik liderleri tam oy birliği: Birliğin TOPLAM oyu x8

    ÖNEMLİ: Sadece ÇOĞUNLUK çarpanı alır, azınlık x1 kalır!
    NOT: İl örgütü çarpanı kaldırıldı (x16 yok artık)
    """
    all_votes = Vote.objects.filter(proposal=proposal).select_related(
        'user',
        'user__current_team',
        'user__current_team__parent_squad',
        'user__current_team__parent_squad__parent_union',
        'user__current_team__parent_squad__parent_union__parent_province_org'
    )

    # Oy yoksa boş döndür
    if not all_votes.exists():
        return {'YES': 0, 'ABSTAIN': 0, 'VETO': 0}

    # Ekip olmayan kullanıcılar varsa basit sayıma geç
    if not all(v.user.current_team for v in all_votes):
        return {
            'YES': Vote.objects.filter(proposal=proposal, vote_choice='YES').count(),
            'ABSTAIN': Vote.objects.filter(proposal=proposal, vote_choice='ABSTAIN').count(),
            'VETO': Vote.objects.filter(proposal=proposal, vote_choice='VETO').count(),
        }

    # 1. ADIM: Ekip bazında oyları topla ve ekip çarpanını uygula
    team_results = {}
    team_votes_dict = defaultdict(list)

    for vote in all_votes:
        team_id = vote.user.current_team.id
        team_votes_dict[team_id].append(vote)

    # Ekip çarpanını uygula
    for team_id, votes in team_votes_dict.items():
        team = Team.objects.get(id=team_id)
        vote_choices = [v.vote_choice for v in votes]

        # Ekip tam oy birliği kontrolü (x2 çarpan)
        if len(votes) == team.member_count and len(set(vote_choices)) == 1:
            choice = vote_choices[0]
            team_results[team_id] = {'YES': 0, 'ABSTAIN': 0, 'VETO': 0}
            team_results[team_id][choice] = len(votes) * 2
        else:
            # Çarpan yok, tek tek say
            team_results[team_id] = {'YES': 0, 'ABSTAIN': 0, 'VETO': 0}
            for vote in votes:
                team_results[team_id][vote.vote_choice] += 1

    # 2. ADIM: Takım bazında topla ve takım lideri çarpanını kontrol et (x4)
    squad_results = {}
    squad_leader_votes = defaultdict(list)

    for team_id, team_result in team_results.items():
        team = Team.objects.get(id=team_id)
        if team.parent_squad:
            squad_id = team.parent_squad.id

            # Takımın oylarını birliğe ekle
            if squad_id not in squad_results:
                squad_results[squad_id] = {'YES': 0, 'ABSTAIN': 0, 'VETO': 0}

            for choice in ['YES', 'ABSTAIN', 'VETO']:
                squad_results[squad_id][choice] += team_result[choice]

            # Ekip liderinin oyunu kaydet (takım lideri çarpanı için)
            if team.leader and team.id in team_votes_dict:
                leader_vote = next((v for v in team_votes_dict[team.id] if v.user == team.leader), None)
                if leader_vote:
                    squad_leader_votes[squad_id].append(leader_vote.vote_choice)

    # Takım liderleri oy birliği yapıyorsa x4 çarpan uygula
    final_squad_results = {}
    for squad_id, squad_result in squad_results.items():
        squad = Squad.objects.get(id=squad_id)
        leader_votes = squad_leader_votes.get(squad_id, [])

        # En az 3 ekip lideri oy vermişse ve hepsi aynı tarafa ise
        if len(leader_votes) >= 3 and len(set(leader_votes)) == 1:
            leader_choice = leader_votes[0]
            # Çoğunluk hangisi?
            majority_choice = max(squad_result.items(), key=lambda x: x[1])[0]

            # Liderler çoğunlukla aynı fikirde mi?
            if leader_choice == majority_choice:
                # Sadece çoğunluğu x4 ile çarp, azınlığı olduğu gibi bırak
                final_squad_results[squad_id] = {
                    'YES': squad_result['YES'] * 4 if majority_choice == 'YES' else squad_result['YES'],
                    'ABSTAIN': squad_result['ABSTAIN'] * 4 if majority_choice == 'ABSTAIN' else squad_result['ABSTAIN'],
                    'VETO': squad_result['VETO'] * 4 if majority_choice == 'VETO' else squad_result['VETO']
                }
            else:
                final_squad_results[squad_id] = squad_result
        else:
            final_squad_results[squad_id] = squad_result

    # 3. ADIM: Birlik bazında topla ve birlik lideri çarpanını kontrol et (x8)
    union_results = {}
    union_leader_votes = defaultdict(list)

    for squad_id, squad_result in final_squad_results.items():
        squad = Squad.objects.get(id=squad_id)
        if squad.parent_union:
            union_id = squad.parent_union.id

            # Birliğin oylarını topla
            if union_id not in union_results:
                union_results[union_id] = {'YES': 0, 'ABSTAIN': 0, 'VETO': 0}

            for choice in ['YES', 'ABSTAIN', 'VETO']:
                union_results[union_id][choice] += squad_result[choice]

            # Takım liderinin oyunu kaydet (birlik lideri çarpanı için)
            if squad.leader:
                # Takım liderinin ekibini bul ve oyunu al
                for team_id in team_votes_dict.keys():
                    team = Team.objects.get(id=team_id)
                    if team.parent_squad_id == squad_id:
                        leader_vote = next((v for v in team_votes_dict[team_id] if v.user == squad.leader), None)
                        if leader_vote:
                            union_leader_votes[union_id].append(leader_vote.vote_choice)
                            break

    # Birlik liderleri oy birliği yapıyorsa x8 çarpan uygula
    final_union_results = {}
    for union_id, union_result in union_results.items():
        union = Union.objects.get(id=union_id)
        leader_votes = union_leader_votes.get(union_id, [])

        # En az 3 takım lideri oy vermişse ve hepsi aynı tarafa ise
        if len(leader_votes) >= 3 and len(set(leader_votes)) == 1:
            leader_choice = leader_votes[0]
            # Çoğunluk hangisi?
            majority_choice = max(union_result.items(), key=lambda x: x[1])[0]

            # Liderler çoğunlukla aynı fikirde mi?
            if leader_choice == majority_choice:
                # Sadece çoğunluğu x8 ile çarp, azınlığı olduğu gibi bırak
                final_union_results[union_id] = {
                    'YES': union_result['YES'] * 8 if majority_choice == 'YES' else union_result['YES'],
                    'ABSTAIN': union_result['ABSTAIN'] * 8 if majority_choice == 'ABSTAIN' else union_result['ABSTAIN'],
                    'VETO': union_result['VETO'] * 8 if majority_choice == 'VETO' else union_result['VETO']
                }
            else:
                final_union_results[union_id] = union_result
        else:
            final_union_results[union_id] = union_result

    # 4. ADIM: Tüm sonuçları birleştir
    final_results = {'YES': 0, 'ABSTAIN': 0, 'VETO': 0}

    # Hiçbir takıma bağlı olmayan ekipleri ekle
    for team_id, team_result in team_results.items():
        team = Team.objects.get(id=team_id)
        if not team.parent_squad:
            for choice in ['YES', 'ABSTAIN', 'VETO']:
                final_results[choice] += team_result[choice]

    # Hiçbir birliğe bağlı olmayan takımları ekle
    for squad_id, squad_result in final_squad_results.items():
        squad = Squad.objects.get(id=squad_id)
        if not squad.parent_union:
            for choice in ['YES', 'ABSTAIN', 'VETO']:
                final_results[choice] += squad_result[choice]

    # Tüm birlikleri ekle
    for union_result in final_union_results.values():
        for choice in ['YES', 'ABSTAIN', 'VETO']:
            final_results[choice] += union_result[choice]

    return final_results


def finalize_proposal_result(proposal):
    """
    Öneri süresini bitir ve sonucu hesapla
    - Çekimser oyları pozitif tarafa ekle (çarpan etkisi olmadan, ham oylar olarak)
    - %75 eşiğini kontrol et
    """
    results = calculate_votes_with_multipliers(proposal)

    yes_votes = results['YES']
    abstain_votes = results['ABSTAIN']
    veto_votes = results['VETO']

    # Çekimser oyları pozitif tarafa ekle (ham oy olarak - çarpan etkisi YOK)
    # Çarpan hesaplaması zaten yapıldı, burada çekimser oyları sadece YES tarafına ekliyoruz
    raw_abstain_votes = Vote.objects.filter(proposal=proposal, vote_choice='ABSTAIN').count()
    yes_votes += raw_abstain_votes

    total_votes = yes_votes + veto_votes

    # %75 eşiğini kontrol et
    if total_votes > 0:
        yes_percentage = (yes_votes / total_votes) * 100

        if yes_percentage >= 75:
            proposal.status = 'PASSED'
        else:
            proposal.status = 'REJECTED'
    else:
        proposal.status = 'REJECTED'

    proposal.save()

    return {
        'yes_votes': yes_votes,
        'veto_votes': veto_votes,
        'yes_percentage': yes_percentage if total_votes > 0 else 0,
        'passed': proposal.status == 'PASSED'
    }
