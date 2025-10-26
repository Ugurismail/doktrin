from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Team, Squad, Union, OrganizationFormationProposal, FormationVote, LeaderVote, LeaderRemovalVote, RemovalVoteCast
from users.models import InviteCode, User
from notifications.utils import notify_leader_change, notify_formation_approved
import uuid
from datetime import datetime, timedelta


@login_required
def my_team(request):
    """Ekibim sayfası"""
    team = request.user.current_team
    pending_proposals = []
    leader_votes_data = {}
    
    if team and team.leader == request.user:
        # Takım önerilerini al
        all_pending = OrganizationFormationProposal.objects.filter(
            level='SQUAD',
            status='PENDING'
        )
        pending_proposals = [p for p in all_pending if str(team.id) in p.participating_entities]
        
        for proposal in pending_proposals:
            user_vote = FormationVote.objects.filter(
                formation_proposal=proposal,
                voter=request.user
            ).first()
            proposal.user_voted = user_vote is not None
            if user_vote:
                proposal.user_vote_choice = user_vote.get_vote_display()
            
            team_ids = [int(tid) for tid in proposal.participating_entities]
            proposal.teams = Team.objects.filter(id__in=team_ids)
    
    # Lider seçimi oylarını al
    if team:
        leader_votes = LeaderVote.objects.filter(
            voter__current_team=team,
            voter_level='TEAM'
        ).select_related('voter', 'candidate')

        from collections import Counter
        vote_counts = Counter(vote.candidate for vote in leader_votes)

        # Oy kullanmayan üyeler mevcut lidere oy vermiş sayılır
        votes_cast = leader_votes.count()
        if team.leader and votes_cast < team.member_count:
            # Mevcut liderin oy sayısını hesapla
            leader_current_votes = vote_counts.get(team.leader, 0)
            # Oy kullanmayanları ekle
            remaining_votes = team.member_count - votes_cast
            vote_counts[team.leader] = leader_current_votes + remaining_votes

        # Eğer hiç oy yoksa, mevcut liderin tüm oyları aldığını göster
        if not vote_counts and team.leader:
            vote_counts = {team.leader: team.member_count}

        leader_votes_data = {
            'votes': leader_votes,
            'vote_counts': dict(vote_counts),
            'total_votes': team.member_count,  # Her zaman toplam üye sayısı
            'member_count': team.member_count,
        }
    
    context = {
        'team': team,
        'pending_proposals': pending_proposals,
        'leader_votes_data': leader_votes_data,
    }
    return render(request, 'organization/my_team.html', context)


@login_required
def create_invite(request):
    """Davet kodu oluştur"""
    if not request.user.current_team:
        messages.error(request, 'Önce bir ekibe katılmalısınız.')
        return redirect('organization:my_team')

    new_invite = None
    if request.method == 'POST':
        code = str(uuid.uuid4())[:8].upper()
        invite = InviteCode.objects.create(
            code=code,
            team=request.user.current_team,
            created_by=request.user,
            expires_at=datetime.now() + timedelta(days=7)
        )

        new_invite = invite
        messages.success(request, 'Davet kodu başarıyla oluşturuldu!')

    context = {
        'new_invite': new_invite
    }
    return render(request, 'organization/create_invite.html', context)

@login_required
def my_squad(request):
    """Takımım sayfası"""
    squad = None
    pending_proposals = []

    if request.user.current_team:
        squad = request.user.current_team.parent_squad

    if squad and squad.leader == request.user:
        # Birlik önerilerini al
        all_pending = OrganizationFormationProposal.objects.filter(
            level='UNION',
            status='PENDING'
        )
        pending_proposals = [p for p in all_pending if str(squad.id) in p.participating_entities]

        for proposal in pending_proposals:
            user_vote = FormationVote.objects.filter(
                formation_proposal=proposal,
                voter=request.user
            ).first()
            proposal.user_voted = user_vote is not None
            if user_vote:
                proposal.user_vote_choice = user_vote.get_vote_display()

            squad_ids = [int(sid) for sid in proposal.participating_entities]
            proposal.squads = Squad.objects.filter(id__in=squad_ids)

    # Lider seçimi oylarını al
    leader_votes_data = {}
    if squad:
        squad_team_leaders = User.objects.filter(
            led_team__parent_squad=squad,
            led_team__is_active=True
        )

        leader_votes = LeaderVote.objects.filter(
            voter__in=squad_team_leaders,
            voter_level='SQUAD'
        ).select_related('voter', 'candidate')

        from collections import Counter
        vote_counts = Counter(vote.candidate for vote in leader_votes)

        # Oy kullanmayan liderler mevcut lidere oy vermiş sayılır
        leader_count = squad_team_leaders.count()
        votes_cast = leader_votes.count()
        if squad.leader and votes_cast < leader_count:
            # Mevcut liderin oy sayısını hesapla
            leader_current_votes = vote_counts.get(squad.leader, 0)
            # Oy kullanmayanları ekle
            remaining_votes = leader_count - votes_cast
            vote_counts[squad.leader] = leader_current_votes + remaining_votes

        # Eğer hiç oy yoksa, mevcut liderin tüm oyları aldığını göster
        if not vote_counts and squad.leader:
            vote_counts = {squad.leader: leader_count}

        leader_votes_data = {
            'votes': leader_votes,
            'vote_counts': dict(vote_counts),
            'total_votes': leader_count,  # Her zaman toplam lider sayısı
            'leader_count': leader_count,
        }

    context = {
        'squad': squad,
        'pending_proposals': pending_proposals,
        'leader_votes_data': leader_votes_data,
    }
    return render(request, 'organization/my_squad.html', context)

@login_required
def my_union(request):
    """Birliğim sayfası"""
    union = None
    pending_proposals = []

    if request.user.current_team and request.user.current_team.parent_squad:
        union = request.user.current_team.parent_squad.parent_union

    if union and union.leader == request.user:
        # İl örgütü önerilerini al
        from .models import ProvinceOrganization
        all_pending = OrganizationFormationProposal.objects.filter(
            level='PROVINCE_ORG',
            status='PENDING'
        )
        pending_proposals = [p for p in all_pending if str(union.id) in p.participating_entities]

        for proposal in pending_proposals:
            user_vote = FormationVote.objects.filter(
                formation_proposal=proposal,
                voter=request.user
            ).first()
            proposal.user_voted = user_vote is not None
            if user_vote:
                proposal.user_vote_choice = user_vote.get_vote_display()

            union_ids = [int(uid) for uid in proposal.participating_entities]
            proposal.unions = Union.objects.filter(id__in=union_ids)

    # Lider seçimi oylarını al
    leader_votes_data = {}
    if union:
        union_squad_leaders = User.objects.filter(
            led_squad__parent_union=union,
            led_squad__is_active=True
        )

        leader_votes = LeaderVote.objects.filter(
            voter__in=union_squad_leaders,
            voter_level='UNION'
        ).select_related('voter', 'candidate')

        from collections import Counter
        vote_counts = Counter(vote.candidate for vote in leader_votes)

        # Oy kullanmayan liderler mevcut lidere oy vermiş sayılır
        leader_count = union_squad_leaders.count()
        votes_cast = leader_votes.count()
        if union.leader and votes_cast < leader_count:
            # Mevcut liderin oy sayısını hesapla
            leader_current_votes = vote_counts.get(union.leader, 0)
            # Oy kullanmayanları ekle
            remaining_votes = leader_count - votes_cast
            vote_counts[union.leader] = leader_current_votes + remaining_votes

        # Eğer hiç oy yoksa, mevcut liderin tüm oyları aldığını göster
        if not vote_counts and union.leader:
            vote_counts = {union.leader: leader_count}

        leader_votes_data = {
            'votes': leader_votes,
            'vote_counts': dict(vote_counts),
            'total_votes': leader_count,  # Her zaman toplam lider sayısı
            'leader_count': leader_count,
        }

    context = {
        'union': union,
        'pending_proposals': pending_proposals,
        'leader_votes_data': leader_votes_data,
    }
    return render(request, 'organization/my_union.html', context)

@login_required
def create_team(request):
    """Yeni ekip oluştur"""
    if request.user.current_team:
        messages.error(request, 'Zaten bir ekiptesiniz.')
        return redirect('organization:my_team')
    
    if request.method == 'POST':
        custom_name = request.POST.get('custom_name', '')
        
        # Aynı ilçede kaç ekip var?
        team_count = Team.objects.filter(
            district=request.user.district,
            province=request.user.province
        ).count()
        
        # Resmi isim oluştur
        official_name = f"{request.user.district} {team_count + 1}"
        
        # Ekip oluştur
        team = Team.objects.create(
            official_name=official_name,
            custom_name=custom_name if custom_name else None,
            district=request.user.district,
            province=request.user.province,
            leader=request.user
        )
        
        # Kullanıcıyı ekibe ata
        request.user.current_team = team
        request.user.save()

        # Aktivite oluştur
        from doctrine.models import Activity
        Activity.objects.create(
            activity_type='TEAM_CREATED',
            user=request.user,
            description=f'yeni bir ekip oluşturdu: {team.display_name}',
            related_url=f'/organization/my-team/'
        )

        messages.success(request, f'Ekip oluşturuldu: {team.display_name}')
        return redirect('organization:my_team')
    
    return render(request, 'organization/create_team.html')


@login_required
def join_team(request):
    """Davet koduyla ekibe katıl"""
    if request.user.current_team:
        messages.error(request, 'Zaten bir ekiptesiniz.')
        return redirect('organization:my_team')

    if request.method == 'POST':
        code = request.POST.get('invite_code', '').strip().upper()

        try:
            invite = InviteCode.objects.get(code=code)

            # Kontroller
            if invite.is_used:
                messages.error(request, 'Bu davet kodu zaten kullanılmış.')
            elif invite.expires_at < timezone.now():
                messages.error(request, 'Bu davet kodunun süresi dolmuş.')
            elif invite.team.member_count >= 15:
                messages.error(request, 'Bu ekip dolu (15 kişi limiti).')
            elif invite.team.province != request.user.province:
                messages.error(request, 'Sadece kendi ilinizden ekiplere katılabilirsiniz.')
            else:
                # Ekibe katıl
                request.user.current_team = invite.team
                request.user.save()

                # Daveti kullanıldı olarak işaretle
                invite.is_used = True
                invite.used_by = request.user
                invite.save()

                messages.success(request, f'{invite.team.display_name} ekibine katıldınız!')
                return redirect('organization:my_team')

        except InviteCode.DoesNotExist:
            messages.error(request, 'Geçersiz davet kodu.')

    return render(request, 'organization/join_team.html')


@login_required
def propose_squad(request):
    """Takım oluşturma önerisi"""
    user_team = request.user.current_team
    
    if not user_team:
        messages.error(request, 'Önce bir ekibe katılmalısınız.')
        return redirect('organization:my_team')
    
    if user_team.leader != request.user:
        messages.error(request, 'Sadece ekip liderleri takım önerisi oluşturabilir.')
        return redirect('organization:my_team')
    
    if user_team.parent_squad:
        messages.error(request, 'Ekibiniz zaten bir takıma bağlı.')
        return redirect('organization:my_squad')
    
    if request.method == 'POST':
        squad_name = request.POST.get('squad_name')
        leader_id = request.POST.get('leader_id')
        team_ids = request.POST.getlist('team_ids')
        
        if len(team_ids) < 3:
            messages.error(request, 'En az 3 ekip seçmelisiniz.')
        else:
            # Öneriyi oluştur
            proposal = OrganizationFormationProposal.objects.create(
                level='SQUAD',
                proposed_name=squad_name,
                proposed_leader_id=leader_id,
                participating_entities=team_ids
            )
            messages.success(request, 'Takım öneriniz oluşturuldu. Diğer ekip liderlerinin onayı bekleniyor.')
            return redirect('organization:my_team')
    
    # Aynı ildeki diğer ekipleri listele (takıma bağlı olmayanlar)
    available_teams = Team.objects.filter(
        province=user_team.province,
        parent_squad__isnull=True,
        is_active=True
    ).exclude(id=user_team.id)
    
    # Tüm kullanıcıları lider adayı olarak listele
    all_teams = list(available_teams) + [user_team]
    potential_leaders = User.objects.filter(
        current_team__in=all_teams
    ).distinct()
    
    context = {
        'user_team': user_team,
        'available_teams': available_teams,
        'potential_leaders': potential_leaders,
    }
    return render(request, 'organization/propose_squad.html', context)


@login_required
def vote_squad_formation(request, proposal_id):
    """Takım oluşturma önerisine oy ver"""
    proposal = get_object_or_404(OrganizationFormationProposal, id=proposal_id)
    user_team = request.user.current_team

    if not user_team or user_team.leader != request.user:
        messages.error(request, 'Sadece ekip liderleri oy kullanabilir.')
        return redirect('organization:my_team')

    if str(user_team.id) not in proposal.participating_entities:
        messages.error(request, 'Bu öneriye oy kullanamazsınız.')
        return redirect('organization:my_team')

    if request.method == 'POST':
        vote = request.POST.get('vote')

        FormationVote.objects.update_or_create(
            formation_proposal=proposal,
            voter=request.user,
            defaults={'vote': vote}
        )

        # Tüm ekip liderleri oy verdi mi kontrol et
        votes = FormationVote.objects.filter(formation_proposal=proposal)
        if votes.count() == len(proposal.participating_entities):
            # Tüm oylar APPROVE mu?
            if all(v.vote == 'APPROVE' for v in votes):
                # İl kontrolü - tüm ekipler aynı ilde mi?
                team_ids = [int(tid) for tid in proposal.participating_entities]
                teams = Team.objects.filter(id__in=team_ids)
                provinces = set(team.province for team in teams)

                if len(provinces) > 1:
                    proposal.status = 'REJECTED'
                    proposal.save()
                    messages.error(request, 'Takım oluşturulamadı: Tüm ekipler aynı ilde olmalıdır.')
                    return redirect('organization:my_team')

                # Takımı oluştur
                squad = Squad.objects.create(
                    name=proposal.proposed_name,
                    province=user_team.province,
                    leader_id=proposal.proposed_leader_id
                )

                # Ekipleri takıma bağla
                Team.objects.filter(id__in=proposal.participating_entities).update(parent_squad=squad)

                proposal.status = 'APPROVED'
                proposal.save()

                # Aktivite oluştur
                from doctrine.models import Activity
                Activity.objects.create(
                    activity_type='SQUAD_CREATED',
                    user=squad.leader,
                    description=f'yeni bir takım kurdu: {squad.name}',
                    related_url=f'/organization/my-team/'
                )

                # Bildirim gönder
                members = User.objects.filter(current_team__parent_squad=squad)
                notify_formation_approved(squad, 'SQUAD', members)

                messages.success(request, f'{squad.name} takımı oluşturuldu!')
            else:
                proposal.status = 'REJECTED'
                proposal.save()
                messages.info(request, 'Takım önerisi reddedildi.')
        else:
            messages.success(request, 'Oyunuz kaydedildi.')

        return redirect('organization:my_team')

    return redirect('organization:my_team')


@login_required
def propose_union(request):
    """Birlik oluşturma önerisi"""
    user_team = request.user.current_team

    if not user_team or not user_team.parent_squad:
        messages.error(request, 'Önce bir takıma katılmalısınız.')
        return redirect('organization:my_squad')

    user_squad = user_team.parent_squad

    if user_squad.leader != request.user:
        messages.error(request, 'Sadece takım liderleri birlik önerisi oluşturabilir.')
        return redirect('organization:my_squad')

    if user_squad.parent_union:
        messages.error(request, 'Takımınız zaten bir birliğe bağlı.')
        return redirect('organization:my_union')

    if request.method == 'POST':
        union_name = request.POST.get('union_name')
        leader_id = request.POST.get('leader_id')
        squad_ids = request.POST.getlist('squad_ids')

        if len(squad_ids) < 3:
            messages.error(request, 'En az 3 takım seçmelisiniz.')
        else:
            # Minimum üye kontrolü
            squads = Squad.objects.filter(id__in=squad_ids)
            total_members = sum(squad.member_count for squad in squads)

            if total_members < 135:
                messages.error(request, f'Birlik oluşturmak için en az 135 üye gerekli. Toplam: {total_members}')
            else:
                # Öneriyi oluştur
                proposal = OrganizationFormationProposal.objects.create(
                    level='UNION',
                    proposed_name=union_name,
                    proposed_leader_id=leader_id,
                    participating_entities=squad_ids
                )
                messages.success(request, 'Birlik öneriniz oluşturuldu. Diğer takım liderlerinin onayı bekleniyor.')
                return redirect('organization:my_squad')

    # Aynı ildeki diğer takımları listele (birliğe bağlı olmayanlar)
    available_squads = Squad.objects.filter(
        province=user_squad.province,
        parent_union__isnull=True,
        is_active=True
    ).exclude(id=user_squad.id)

    # Tüm takımları lider adayı olarak listele
    all_squads = list(available_squads) + [user_squad]
    potential_leaders = User.objects.filter(
        current_team__parent_squad__in=all_squads
    ).distinct()

    context = {
        'user_squad': user_squad,
        'available_squads': available_squads,
        'potential_leaders': potential_leaders,
    }
    return render(request, 'organization/propose_union.html', context)


@login_required
def vote_union_formation(request, proposal_id):
    """Birlik oluşturma önerisine oy ver"""
    proposal = get_object_or_404(OrganizationFormationProposal, id=proposal_id)
    user_team = request.user.current_team

    if not user_team or not user_team.parent_squad:
        messages.error(request, 'Bir takıma dahil olmalısınız.')
        return redirect('organization:my_squad')

    user_squad = user_team.parent_squad

    if user_squad.leader != request.user:
        messages.error(request, 'Sadece takım liderleri oy kullanabilir.')
        return redirect('organization:my_squad')

    if str(user_squad.id) not in proposal.participating_entities:
        messages.error(request, 'Bu öneriye oy kullanamazsınız.')
        return redirect('organization:my_squad')

    if request.method == 'POST':
        vote = request.POST.get('vote')

        FormationVote.objects.update_or_create(
            formation_proposal=proposal,
            voter=request.user,
            defaults={'vote': vote}
        )

        # Tüm takım liderleri oy verdi mi kontrol et
        votes = FormationVote.objects.filter(formation_proposal=proposal)
        if votes.count() == len(proposal.participating_entities):
            # Tüm oylar APPROVE mu?
            if all(v.vote == 'APPROVE' for v in votes):
                # İl kontrolü - tüm takımlar aynı ilde mi?
                squad_ids = [int(sid) for sid in proposal.participating_entities]
                squads = Squad.objects.filter(id__in=squad_ids)
                provinces = set(squad.province for squad in squads)

                if len(provinces) > 1:
                    proposal.status = 'REJECTED'
                    proposal.save()
                    messages.error(request, 'Birlik oluşturulamadı: Tüm takımlar aynı ilde olmalıdır.')
                    return redirect('organization:my_squad')

                # Minimum üye kontrolü
                total_members = sum(squad.member_count for squad in squads)
                if total_members < 135:
                    proposal.status = 'REJECTED'
                    proposal.save()
                    messages.error(request, f'Birlik oluşturulamadı: En az 135 üye gerekli. Toplam: {total_members}')
                    return redirect('organization:my_squad')

                # Birliği oluştur
                union = Union.objects.create(
                    name=proposal.proposed_name,
                    province=user_squad.province,
                    leader_id=proposal.proposed_leader_id
                )

                # Takımları birliğe bağla
                Squad.objects.filter(id__in=proposal.participating_entities).update(parent_union=union)

                proposal.status = 'APPROVED'
                proposal.save()

                # Aktivite oluştur
                from doctrine.models import Activity
                Activity.objects.create(
                    activity_type='UNION_CREATED',
                    user=union.leader,
                    description=f'yeni bir birlik kurdu: {union.name}',
                    related_url=f'/organization/my-team/'
                )

                # Bildirim gönder
                members = User.objects.filter(current_team__parent_squad__parent_union=union)
                notify_formation_approved(union, 'UNION', members)

                messages.success(request, f'{union.name} birliği oluşturuldu!')
            else:
                proposal.status = 'REJECTED'
                proposal.save()
                messages.info(request, 'Birlik önerisi reddedildi.')
        else:
            messages.success(request, 'Oyunuz kaydedildi.')

        return redirect('organization:my_squad')

    return redirect('organization:my_squad')


@login_required
def vote_team_leader(request):
    """Ekip lideri için oy ver"""
    from django.shortcuts import get_object_or_404
    
    user_team = request.user.current_team
    
    if not user_team:
        messages.error(request, 'Bir ekibe dahil olmalısınız.')
        return redirect('organization:my_team')

    # Eski lider kontrolü - eğer bu kullanıcı yakın zamanda atılmış bir lidersse oy veremez
    from django.utils import timezone
    recent_removal = LeaderRemovalVote.objects.filter(
        level='TEAM',
        entity_id=user_team.id,
        current_leader=request.user,
        status='PASSED',
        end_date__gte=timezone.now() - timezone.timedelta(days=30)  # Son 30 gün içinde
    ).first()

    if recent_removal:
        messages.error(request, 'Atılmış lider olarak yeni lider seçiminde oy kullanamazsınız.')
        return redirect('organization:my_team')
    
    if request.method == 'POST':
        candidate_id = request.POST.get('candidate_id')
        
        if not candidate_id:
            messages.error(request, 'Lütfen bir aday seçin.')
            return redirect('organization:my_team')
        
        candidate = get_object_or_404(User, id=candidate_id)
        
        if candidate.current_team != user_team:
            messages.error(request, 'Sadece kendi ekibinizdeki birine oy verebilirsiniz.')
            return redirect('organization:my_team')
        
        LeaderVote.objects.update_or_create(
            voter=request.user,
            voter_level='TEAM',
            defaults={'candidate': candidate}
        )

        # Oy sayımında eski lideri hariç tut
        team_votes = LeaderVote.objects.filter(
            voter__current_team=user_team,
            voter_level='TEAM'
        )
        if recent_removal:
            team_votes = team_votes.exclude(voter=recent_removal.current_leader)

        # Ekip üye sayısından eski lideri çıkar
        expected_vote_count = user_team.member_count
        if recent_removal:
            expected_vote_count -= 1

        if team_votes.count() == expected_vote_count:
            candidates = team_votes.values_list('candidate', flat=True)
            unique_candidates = set(candidates)

            if len(unique_candidates) == 1:
                new_leader_id = list(unique_candidates)[0]
                new_leader = User.objects.get(id=new_leader_id)
                old_leader = user_team.leader
                user_team.leader = new_leader
                user_team.save()

                # Oyları temizle - yeni lider seçildi
                team_votes.delete()

                # Bildirim gönder
                if old_leader != new_leader:
                    notify_leader_change(user_team, new_leader, 'TEAM')

                messages.success(request, f'{new_leader.username} yeni ekip lideri oldu!')
            else:
                # Oy birliği sağlanmadı, mevcut lider devam etsin
                # Oyları SİLME - sayfa yenilendiğinde kullanıcılar görebilsin
                messages.info(request, 'Oy birliği sağlanmadı, mevcut lider görevine devam ediyor.')
        else:
            messages.success(request, 'Oyunuz kaydedildi.')
        
        return redirect('organization:my_team')

    return redirect('organization:my_team')


@login_required
def vote_squad_leader(request):
    """Takım lideri için oy ver"""
    user_team = request.user.current_team

    if not user_team or not user_team.parent_squad:
        messages.error(request, 'Bir takıma dahil olmalısınız.')
        return redirect('organization:my_squad')

    user_squad = user_team.parent_squad

    # Sadece ekip liderleri oy kullanabilir
    if user_team.leader != request.user:
        messages.error(request, 'Sadece ekip liderleri takım lideri oylamasına katılabilir.')
        return redirect('organization:my_squad')

    # Eski lider kontrolü - eğer bu kullanıcı yakın zamanda atılmış bir lidersse oy veremez
    recent_removal = LeaderRemovalVote.objects.filter(
        level='SQUAD',
        entity_id=user_squad.id,
        current_leader=request.user,
        status='PASSED',
        end_date__gte=timezone.now() - timezone.timedelta(days=30)
    ).first()

    if recent_removal:
        messages.error(request, 'Atılmış lider olarak yeni lider seçiminde oy kullanamazsınız.')
        return redirect('organization:my_squad')

    if request.method == 'POST':
        candidate_id = request.POST.get('candidate_id')

        if not candidate_id:
            messages.error(request, 'Lütfen bir aday seçin.')
            return redirect('organization:my_squad')

        candidate = get_object_or_404(User, id=candidate_id)

        # Aday takımdaki bir ekip lideri olmalı
        if not (candidate.current_team and candidate.current_team.parent_squad == user_squad and candidate.current_team.leader == candidate):
            messages.error(request, 'Aday takımdaki bir ekip lideri olmalıdır.')
            return redirect('organization:my_squad')

        LeaderVote.objects.update_or_create(
            voter=request.user,
            voter_level='SQUAD',
            defaults={'candidate': candidate}
        )

        # Tüm ekip liderleri oy verdi mi kontrol et
        squad_team_leaders = User.objects.filter(
            led_team__parent_squad=user_squad,
            led_team__is_active=True
        )

        # Oy sayımında eski lideri hariç tut
        squad_votes = LeaderVote.objects.filter(
            voter__in=squad_team_leaders,
            voter_level='SQUAD'
        )
        if recent_removal:
            squad_votes = squad_votes.exclude(voter=recent_removal.current_leader)
            squad_team_leaders = squad_team_leaders.exclude(id=recent_removal.current_leader.id)

        if squad_votes.count() == squad_team_leaders.count():
            candidates = squad_votes.values_list('candidate', flat=True)
            unique_candidates = set(candidates)

            if len(unique_candidates) == 1:
                new_leader_id = list(unique_candidates)[0]
                new_leader = User.objects.get(id=new_leader_id)
                old_leader = user_squad.leader
                user_squad.leader = new_leader
                user_squad.save()

                # Oyları temizle - yeni lider seçildi
                squad_votes.delete()

                # Bildirim gönder
                if old_leader != new_leader:
                    notify_leader_change(user_squad, new_leader, 'SQUAD')

                messages.success(request, f'{new_leader.username} yeni takım lideri oldu!')
            else:
                # Oy birliği sağlanmadı, mevcut lider devam etsin
                # Oyları SİLME - sayfa yenilendiğinde kullanıcılar görebilsin
                messages.info(request, 'Oy birliği sağlanmadı, mevcut lider görevine devam ediyor.')
        else:
            messages.success(request, 'Oyunuz kaydedildi.')

        return redirect('organization:my_squad')

    return redirect('organization:my_squad')


@login_required
def vote_union_leader(request):
    """Birlik lideri için oy ver"""
    user_team = request.user.current_team

    if not user_team or not user_team.parent_squad or not user_team.parent_squad.parent_union:
        messages.error(request, 'Bir birliğe dahil olmalısınız.')
        return redirect('organization:my_union')

    user_union = user_team.parent_squad.parent_union

    # Sadece takım liderleri oy kullanabilir
    if user_team.parent_squad.leader != request.user:
        messages.error(request, 'Sadece takım liderleri birlik lideri oylamasına katılabilir.')
        return redirect('organization:my_union')

    # Eski lider kontrolü - eğer bu kullanıcı yakın zamanda atılmış bir lidersse oy veremez
    recent_removal = LeaderRemovalVote.objects.filter(
        level='UNION',
        entity_id=user_union.id,
        current_leader=request.user,
        status='PASSED',
        end_date__gte=timezone.now() - timezone.timedelta(days=30)
    ).first()

    if recent_removal:
        messages.error(request, 'Atılmış lider olarak yeni lider seçiminde oy kullanamazsınız.')
        return redirect('organization:my_union')

    if request.method == 'POST':
        candidate_id = request.POST.get('candidate_id')

        if not candidate_id:
            messages.error(request, 'Lütfen bir aday seçin.')
            return redirect('organization:my_union')

        candidate = get_object_or_404(User, id=candidate_id)

        # Aday birlikteki bir takım lideri olmalı
        if not (candidate.led_squad.exists() and candidate.led_squad.first().parent_union == user_union):
            messages.error(request, 'Aday birlikteki bir takım lideri olmalıdır.')
            return redirect('organization:my_union')

        LeaderVote.objects.update_or_create(
            voter=request.user,
            voter_level='UNION',
            defaults={'candidate': candidate}
        )

        # Tüm takım liderleri oy verdi mi kontrol et
        union_squad_leaders = User.objects.filter(
            led_squad__parent_union=user_union,
            led_squad__is_active=True
        )

        # Oy sayımında eski lideri hariç tut
        union_votes = LeaderVote.objects.filter(
            voter__in=union_squad_leaders,
            voter_level='UNION'
        )
        if recent_removal:
            union_votes = union_votes.exclude(voter=recent_removal.current_leader)
            union_squad_leaders = union_squad_leaders.exclude(id=recent_removal.current_leader.id)

        if union_votes.count() == union_squad_leaders.count():
            candidates = union_votes.values_list('candidate', flat=True)
            unique_candidates = set(candidates)

            if len(unique_candidates) == 1:
                new_leader_id = list(unique_candidates)[0]
                new_leader = User.objects.get(id=new_leader_id)
                old_leader = user_union.leader
                user_union.leader = new_leader
                user_union.save()

                # Oyları temizle - yeni lider seçildi
                union_votes.delete()

                # Bildirim gönder
                if old_leader != new_leader:
                    notify_leader_change(user_union, new_leader, 'UNION')

                messages.success(request, f'{new_leader.username} yeni birlik lideri oldu!')
            else:
                # Oy birliği sağlanmadı, mevcut lider devam etsin
                # Oyları SİLME - sayfa yenilendiğinde kullanıcılar görebilsin
                messages.info(request, 'Oy birliği sağlanmadı, mevcut lider görevine devam ediyor.')
        else:
            messages.success(request, 'Oyunuz kaydedildi.')

        return redirect('organization:my_union')

    return redirect('organization:my_union')


@login_required
def my_province_org(request):
    """İl Örgütüm sayfası"""
    province_org = None
    pending_proposals = []

    if request.user.current_team and request.user.current_team.parent_squad:
        squad = request.user.current_team.parent_squad
        if squad.parent_union:
            province_org = squad.parent_union.parent_province_org

    if province_org and province_org.leader == request.user:
        # İl örgütü önerilerini al
        from .models import ProvinceOrganization
        all_pending = OrganizationFormationProposal.objects.filter(
            level='PROVINCE_ORG',
            status='PENDING'
        )
        pending_proposals = [p for p in all_pending if str(province_org.id) in p.participating_entities]

        for proposal in pending_proposals:
            user_vote = FormationVote.objects.filter(
                formation_proposal=proposal,
                voter=request.user
            ).first()
            proposal.user_voted = user_vote is not None
            if user_vote:
                proposal.user_vote_choice = user_vote.get_vote_display()

            union_ids = [int(uid) for uid in proposal.participating_entities]
            proposal.unions = Union.objects.filter(id__in=union_ids)

    # Lider seçimi oylarını al
    leader_votes_data = {}
    if province_org:
        province_org_union_leaders = User.objects.filter(
            led_union__parent_province_org=province_org,
            led_union__is_active=True
        )

        leader_votes = LeaderVote.objects.filter(
            voter__in=province_org_union_leaders,
            voter_level='PROVINCE_ORG'
        ).select_related('voter', 'candidate')

        from collections import Counter
        vote_counts = Counter(vote.candidate for vote in leader_votes)

        # Oy kullanmayan liderler mevcut lidere oy vermiş sayılır
        leader_count = province_org_union_leaders.count()
        votes_cast = leader_votes.count()
        if province_org.leader and votes_cast < leader_count:
            # Mevcut liderin oy sayısını hesapla
            leader_current_votes = vote_counts.get(province_org.leader, 0)
            # Oy kullanmayanları ekle
            remaining_votes = leader_count - votes_cast
            vote_counts[province_org.leader] = leader_current_votes + remaining_votes

        # Eğer hiç oy yoksa, mevcut liderin tüm oyları aldığını göster
        if not vote_counts and province_org.leader:
            vote_counts = {province_org.leader: leader_count}

        leader_votes_data = {
            'votes': leader_votes,
            'vote_counts': dict(vote_counts),
            'total_votes': leader_count,  # Her zaman toplam lider sayısı
            'leader_count': leader_count,
        }

    context = {
        'province_org': province_org,
        'pending_proposals': pending_proposals,
        'leader_votes_data': leader_votes_data,
    }
    return render(request, 'organization/my_province_org.html', context)


@login_required
def propose_province_org(request):
    """İl Örgütü oluşturma önerisi"""
    from .models import ProvinceOrganization

    user_team = request.user.current_team

    if not user_team or not user_team.parent_squad or not user_team.parent_squad.parent_union:
        messages.error(request, 'Önce bir birliğe katılmalısınız.')
        return redirect('organization:my_union')

    user_union = user_team.parent_squad.parent_union

    if user_union.leader != request.user:
        messages.error(request, 'Sadece birlik liderleri il örgütü önerisi oluşturabilir.')
        return redirect('organization:my_union')

    if user_union.parent_province_org:
        messages.error(request, 'Birliğiniz zaten bir il örgütüne bağlı.')
        return redirect('organization:my_province_org')

    if request.method == 'POST':
        province_org_name = request.POST.get('province_org_name')
        leader_id = request.POST.get('leader_id')
        union_ids = request.POST.getlist('union_ids')

        if len(union_ids) < 3:
            messages.error(request, 'En az 3 birlik seçmelisiniz.')
        else:
            # Minimum üye kontrolü
            unions = Union.objects.filter(id__in=union_ids)
            total_members = sum(union.member_count for union in unions)

            if total_members < 375:
                messages.error(request, f'İl örgütü oluşturmak için en az 375 üye gerekli. Toplam: {total_members}')
            else:
                # Öneriyi oluştur
                proposal = OrganizationFormationProposal.objects.create(
                    level='PROVINCE_ORG',
                    proposed_name=province_org_name,
                    proposed_leader_id=leader_id,
                    participating_entities=union_ids
                )
                messages.success(request, 'İl örgütü öneriniz oluşturuldu. Diğer birlik liderlerinin onayı bekleniyor.')
                return redirect('organization:my_union')

    # Aynı ildeki diğer birlikleri listele (il örgütüne bağlı olmayanlar)
    available_unions = Union.objects.filter(
        province=user_union.province,
        parent_province_org__isnull=True,
        is_active=True
    ).exclude(id=user_union.id)

    # Tüm birlikleri lider adayı olarak listele
    all_unions = list(available_unions) + [user_union]
    potential_leaders = User.objects.filter(
        led_squad__parent_union__in=all_unions
    ).distinct()

    context = {
        'user_union': user_union,
        'available_unions': available_unions,
        'potential_leaders': potential_leaders,
    }
    return render(request, 'organization/propose_province_org.html', context)


@login_required
def vote_province_org_formation(request, proposal_id):
    """İl örgütü oluşturma önerisine oy ver"""
    from .models import ProvinceOrganization

    proposal = get_object_or_404(OrganizationFormationProposal, id=proposal_id)
    user_team = request.user.current_team

    if not user_team or not user_team.parent_squad or not user_team.parent_squad.parent_union:
        messages.error(request, 'Bir birliğe dahil olmalısınız.')
        return redirect('organization:my_union')

    user_union = user_team.parent_squad.parent_union

    if user_union.leader != request.user:
        messages.error(request, 'Sadece birlik liderleri oy kullanabilir.')
        return redirect('organization:my_union')

    if str(user_union.id) not in proposal.participating_entities:
        messages.error(request, 'Bu öneriye oy kullanamazsınız.')
        return redirect('organization:my_union')

    if request.method == 'POST':
        vote = request.POST.get('vote')

        FormationVote.objects.update_or_create(
            formation_proposal=proposal,
            voter=request.user,
            defaults={'vote': vote}
        )

        # Tüm birlik liderleri oy verdi mi kontrol et
        votes = FormationVote.objects.filter(formation_proposal=proposal)
        if votes.count() == len(proposal.participating_entities):
            # Tüm oylar APPROVE mu?
            if all(v.vote == 'APPROVE' for v in votes):
                # İl kontrolü - tüm birlikler aynı ilde mi?
                union_ids = [int(uid) for uid in proposal.participating_entities]
                unions = Union.objects.filter(id__in=union_ids)
                provinces = set(union.province for union in unions)

                if len(provinces) > 1:
                    proposal.status = 'REJECTED'
                    proposal.save()
                    messages.error(request, 'İl örgütü oluşturulamadı: Tüm birlikler aynı ilde olmalıdır.')
                    return redirect('organization:my_union')

                # Minimum üye kontrolü
                total_members = sum(union.member_count for union in unions)
                if total_members < 375:
                    proposal.status = 'REJECTED'
                    proposal.save()
                    messages.error(request, f'İl örgütü oluşturulamadı: En az 375 üye gerekli. Toplam: {total_members}')
                    return redirect('organization:my_union')

                # İl örgütünü oluştur
                province_org = ProvinceOrganization.objects.create(
                    name=proposal.proposed_name,
                    province=user_union.province,
                    leader_id=proposal.proposed_leader_id
                )

                # Birlikleri il örgütüne bağla
                Union.objects.filter(id__in=proposal.participating_entities).update(parent_province_org=province_org)

                proposal.status = 'APPROVED'
                proposal.save()

                # Bildirim gönder
                members = User.objects.filter(current_team__parent_squad__parent_union__parent_province_org=province_org)
                notify_formation_approved(province_org, 'PROVINCE_ORG', members)

                messages.success(request, f'{province_org.name} il örgütü oluşturuldu!')
            else:
                proposal.status = 'REJECTED'
                proposal.save()
                messages.info(request, 'İl örgütü önerisi reddedildi.')
        else:
            messages.success(request, 'Oyunuz kaydedildi.')

        return redirect('organization:my_union')

    return redirect('organization:my_union')


@login_required
def vote_province_org_leader(request):
    """İl Örgütü lideri seçimi - Sadece birlik liderleri oy kullanabilir"""
    from .models import ProvinceOrganization

    user_team = request.user.current_team

    if not user_team or not user_team.parent_squad or not user_team.parent_squad.parent_union:
        messages.error(request, 'Önce bir birliğe katılmalısınız.')
        return redirect('organization:my_province_org')

    user_union = user_team.parent_squad.parent_union

    if not user_union.parent_province_org:
        messages.error(request, 'Henüz bir il örgütüne bağlı değilsiniz.')
        return redirect('organization:my_province_org')

    province_org = user_union.parent_province_org

    # Sadece birlik liderleri oy kullanabilir
    if user_union.leader != request.user:
        messages.error(request, 'Sadece birlik liderleri il örgütü lideri oylamasına katılabilir.')
        return redirect('organization:my_province_org')

    if request.method == 'POST':
        candidate_id = request.POST.get('candidate_id')

        if not candidate_id:
            messages.error(request, 'Lütfen bir aday seçin.')
            return redirect('organization:my_province_org')

        candidate = User.objects.get(id=candidate_id)

        # Aday il örgütü üyesi mi kontrol et
        candidate_union = candidate.current_team.parent_squad.parent_union if candidate.current_team and candidate.current_team.parent_squad else None
        if not candidate_union or candidate_union.parent_province_org != province_org:
            messages.error(request, 'Aday il örgütü üyesi olmalıdır.')
            return redirect('organization:my_province_org')

        # Oyu kaydet veya güncelle (PROVINCE_ORG seviyesi)
        LeaderVote.objects.update_or_create(
            voter=request.user,
            voter_level='PROVINCE_ORG',
            defaults={'candidate': candidate}
        )

        # Tüm birlik liderleri oy verdi mi kontrol et
        province_org_union_leaders = User.objects.filter(
            led_union__parent_province_org=province_org,
            led_union__is_active=True
        )

        province_org_votes = LeaderVote.objects.filter(
            voter__in=province_org_union_leaders,
            voter_level='PROVINCE_ORG'
        )

        if province_org_votes.count() == province_org_union_leaders.count():
            candidates = province_org_votes.values_list('candidate', flat=True)
            unique_candidates = set(candidates)

            if len(unique_candidates) == 1:
                new_leader_id = list(unique_candidates)[0]
                new_leader = User.objects.get(id=new_leader_id)
                old_leader = province_org.leader
                province_org.leader = new_leader
                province_org.save()

                # Oyları temizle - yeni lider seçildi
                province_org_votes.delete()

                # Bildirim gönder
                if old_leader != new_leader:
                    notify_leader_change(province_org, new_leader, 'PROVINCE_ORG')

                messages.success(request, f'{new_leader.username} yeni il örgütü lideri oldu!')
            else:
                # Oy birliği sağlanmadı, mevcut lider devam etsin
                # Oyları SİLME - sayfa yenilendiğinde kullanıcılar görebilsin
                messages.info(request, 'Oy birliği sağlanmadı, mevcut lider görevine devam ediyor.')
        else:
            messages.success(request, 'Oyunuz kaydedildi.')

        return redirect('organization:my_province_org')

    return redirect('organization:my_province_org')
@login_required
def organization_chart(request):
    """Organizasyon hiyerarşi grafiği"""
    user_team = request.user.current_team
    squad = None
    union = None
    province_org = None

    if user_team:
        squad = user_team.parent_squad
        if squad:
            union = squad.parent_union
            if union:
                province_org = union.parent_province_org

    context = {
        "user_team": user_team,
        "squad": squad,
        "union": union,
        "province_org": province_org,
    }
    return render(request, "organization/organization_chart.html", context)


@login_required
def create_announcement(request):
    """Lider duyurusu oluştur"""
    from notifications.models import Announcement
    from notifications.utils import notify_announcement
    from organization.models import ProvinceOrganization

    user = request.user
    team = user.current_team

    # Kullanıcının lider olduğu seviyeyi belirle
    is_team_leader = team and team.leader == user
    is_squad_leader = team and team.parent_squad and team.parent_squad.leader == user
    is_union_leader = (team and team.parent_squad and team.parent_squad.parent_union
                      and team.parent_squad.parent_union.leader == user)
    is_province_leader = (team and team.parent_squad and team.parent_squad.parent_union
                         and team.parent_squad.parent_union.parent_province_org
                         and team.parent_squad.parent_union.parent_province_org.leader == user)

    if not any([is_team_leader, is_squad_leader, is_union_leader, is_province_leader]):
        messages.error(request, 'Duyuru oluşturmak için lider olmalısınız.')
        return redirect('organization:my_team')

    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        level = request.POST.get('level')

        # Seviye kontrolü - kullanıcı sadece lider olduğu seviyeye duyuru yapabilir
        entity_id = None
        allowed = False

        if level == 'TEAM' and is_team_leader:
            entity_id = team.id
            allowed = True
        elif level == 'SQUAD' and is_squad_leader:
            entity_id = team.parent_squad.id
            allowed = True
        elif level == 'UNION' and is_union_leader:
            entity_id = team.parent_squad.parent_union.id
            allowed = True
        elif level == 'PROVINCE_ORG' and is_province_leader:
            entity_id = team.parent_squad.parent_union.parent_province_org.id
            allowed = True

        if not allowed:
            messages.error(request, 'Bu seviye için duyuru oluşturma yetkiniz yok.')
            return redirect('organization:my_team')

        # Duyuruyu oluştur
        announcement = Announcement.objects.create(
            title=title,
            content=content,
            created_by=user,
            target_level=level,
            target_entity_id=entity_id
        )

        # İlgili üyelere bildirim gönder
        target_users = []
        if level == 'TEAM':
            target_users = User.objects.filter(current_team_id=entity_id).exclude(id=user.id)
        elif level == 'SQUAD':
            target_users = User.objects.filter(current_team__parent_squad_id=entity_id).exclude(id=user.id)
        elif level == 'UNION':
            target_users = User.objects.filter(current_team__parent_squad__parent_union_id=entity_id).exclude(id=user.id)
        elif level == 'PROVINCE_ORG':
            target_users = User.objects.filter(current_team__parent_squad__parent_union__parent_province_org_id=entity_id).exclude(id=user.id)

        notify_announcement(announcement, target_users)

        # E-posta bildirimi gönder
        from users.emails import send_announcement_email
        for user in target_users:
            send_announcement_email(user, announcement)

        messages.success(request, 'Duyuru başarıyla oluşturuldu.')
        return redirect('organization:view_announcements')

    # Kullanıcının yapabileceği duyuru seviyelerini belirle
    available_levels = []
    if is_team_leader:
        available_levels.append(('TEAM', 'Ekip'))
    if is_squad_leader:
        available_levels.append(('SQUAD', 'Takım'))
    if is_union_leader:
        available_levels.append(('UNION', 'Birlik'))
    if is_province_leader:
        available_levels.append(('PROVINCE_ORG', 'İl Örgütü'))

    context = {
        'available_levels': available_levels,
    }
    return render(request, 'organization/create_announcement.html', context)


@login_required
def view_announcements(request):
    """Duyuruları görüntüle"""
    from notifications.models import Announcement
    from organization.models import ProvinceOrganization

    user = request.user
    team = user.current_team

    announcements = []

    if team:
        # Ekip duyuruları
        team_announcements = Announcement.objects.filter(
            target_level='TEAM',
            target_entity_id=team.id
        )
        announcements.extend(team_announcements)

        # Takım duyuruları
        if team.parent_squad:
            squad_announcements = Announcement.objects.filter(
                target_level='SQUAD',
                target_entity_id=team.parent_squad.id
            )
            announcements.extend(squad_announcements)

            # Birlik duyuruları
            if team.parent_squad.parent_union:
                union_announcements = Announcement.objects.filter(
                    target_level='UNION',
                    target_entity_id=team.parent_squad.parent_union.id
                )
                announcements.extend(union_announcements)

                # İl örgütü duyuruları
                if team.parent_squad.parent_union.parent_province_org:
                    province_announcements = Announcement.objects.filter(
                        target_level='PROVINCE_ORG',
                        target_entity_id=team.parent_squad.parent_union.parent_province_org.id
                    )
                    announcements.extend(province_announcements)

    # Tarihe göre sırala
    announcements = sorted(announcements, key=lambda x: x.created_at, reverse=True)

    context = {
        'announcements': announcements,
    }
    return render(request, 'organization/view_announcements.html', context)

# ========================================
# MANAGEMENT PANELS
# ========================================

@login_required
def manage_team(request):
    """Ekip lideri için yönetim paneli"""
    user_team = request.user.current_team
    
    if not user_team:
        messages.error(request, 'Bir ekibe dahil değilsiniz.')
        return redirect('organization:my_team')
    
    # Sadece lider erişebilir
    if user_team.leader != request.user:
        messages.error(request, 'Sadece ekip lideri bu sayfaya erişebilir.')
        return redirect('organization:my_team')
    
    # Ekip üyeleri
    team_members = User.objects.filter(current_team=user_team).select_related('current_team')
    
    # Ekip istatistikleri
    from doctrine.models import Vote, Discussion, Proposal
    team_votes = Vote.objects.filter(user__current_team=user_team).count()
    team_comments = Discussion.objects.filter(user__current_team=user_team).count()
    team_proposals = Proposal.objects.filter(proposed_by_level='SQUAD', proposed_by_entity_id=user_team.parent_squad_id).count() if user_team.parent_squad else 0
    
    context = {
        'team': user_team,
        'team_members': team_members,
        'team_votes': team_votes,
        'team_comments': team_comments,
        'team_proposals': team_proposals,
    }
    return render(request, 'organization/manage_team.html', context)


@login_required
def manage_squad(request):
    """Takım lideri için yönetim paneli"""
    user_team = request.user.current_team
    
    if not user_team or not user_team.parent_squad:
        messages.error(request, 'Bir takıma dahil değilsiniz.')
        return redirect('organization:my_squad')
    
    squad = user_team.parent_squad
    
    # Sadece lider erişebilir
    if squad.leader != request.user:
        messages.error(request, 'Sadece takım lideri bu sayfaya erişebilir.')
        return redirect('organization:my_squad')
    
    # Takım istatistikleri
    squad_teams = Team.objects.filter(parent_squad=squad)
    squad_members = User.objects.filter(current_team__parent_squad=squad).select_related('current_team')
    
    from doctrine.models import Vote, Discussion, Proposal
    squad_votes = Vote.objects.filter(user__current_team__parent_squad=squad).count()
    squad_comments = Discussion.objects.filter(user__current_team__parent_squad=squad).count()
    squad_proposals = Proposal.objects.filter(proposed_by_level='SQUAD', proposed_by_entity_id=squad.id).count()
    
    context = {
        'squad': squad,
        'squad_teams': squad_teams,
        'squad_members': squad_members,
        'squad_votes': squad_votes,
        'squad_comments': squad_comments,
        'squad_proposals': squad_proposals,
    }
    return render(request, 'organization/manage_squad.html', context)


@login_required
def manage_union(request):
    """Birlik lideri için yönetim paneli"""
    user_team = request.user.current_team
    
    if not user_team or not user_team.parent_squad or not user_team.parent_squad.parent_union:
        messages.error(request, 'Bir birliğe dahil değilsiniz.')
        return redirect('organization:my_union')
    
    union = user_team.parent_squad.parent_union
    
    # Sadece lider erişebilir
    if union.leader != request.user:
        messages.error(request, 'Sadece birlik lideri bu sayfaya erişebilir.')
        return redirect('organization:my_union')
    
    # Birlik istatistikleri
    union_squads = Squad.objects.filter(parent_union=union)
    union_teams = Team.objects.filter(parent_squad__parent_union=union)
    union_members = User.objects.filter(current_team__parent_squad__parent_union=union).select_related('current_team')
    
    from doctrine.models import Vote, Discussion, Proposal
    union_votes = Vote.objects.filter(user__current_team__parent_squad__parent_union=union).count()
    union_comments = Discussion.objects.filter(user__current_team__parent_squad__parent_union=union).count()
    union_proposals = Proposal.objects.filter(proposed_by_level='UNION', proposed_by_entity_id=union.id).count()
    
    context = {
        'union': union,
        'union_squads': union_squads,
        'union_teams': union_teams,
        'union_members': union_members,
        'union_votes': union_votes,
        'union_comments': union_comments,
        'union_proposals': union_proposals,
    }
    return render(request, 'organization/manage_union.html', context)


# ========================================
# MEMBER TRANSFER SYSTEM
# ========================================

@login_required
def request_team_transfer(request):
    """Kullanıcı davet kodu ile ekip değişikliği yapar"""
    if request.method == 'POST':
        invite_code = request.POST.get('invite_code', '').strip()

        if not invite_code:
            messages.error(request, 'Davet kodu girmelisiniz.')
            return redirect('organization:request_team_transfer')

        try:
            invite = TeamInvite.objects.get(code=invite_code, is_used=False)
        except TeamInvite.DoesNotExist:
            messages.error(request, 'Geçersiz veya kullanılmış davet kodu.')
            return redirect('organization:request_team_transfer')

        # Davet kodunun süresinin dolup dolmadığını kontrol et
        from django.utils import timezone
        if invite.expires_at < timezone.now():
            messages.error(request, 'Bu davet kodunun süresi dolmuş.')
            return redirect('organization:request_team_transfer')

        target_team = invite.team

        # Aynı ekipse transfer edilemez
        if request.user.current_team == target_team:
            messages.error(request, 'Zaten bu ekiptesiniz.')
            return redirect('organization:request_team_transfer')

        # Ekip dolu mu kontrol et
        if target_team.member_count >= 15:
            messages.error(request, 'Hedef ekip dolu (15/15).')
            return redirect('organization:request_team_transfer')

        # Transfer işlemi
        old_team = request.user.current_team
        request.user.current_team = target_team
        request.user.save()

        # Davet kodunu kullanılmış olarak işaretle
        invite.is_used = True
        invite.used_by = request.user
        invite.save()

        # Aktivite oluştur
        Activity.objects.create(
            activity_type='team_created',  # En yakın type
            user=request.user,
            description=f'{old_team.display_name if old_team else "Ekipsiz"} ekibinden {target_team.display_name} ekibine transfer oldu',
            related_url=f'/organization/team/'
        )

        messages.success(request, f'Başarıyla {target_team.display_name} ekibine transfer oldunuz!')
        return redirect('organization:my_team')

    context = {
        'current_team': request.user.current_team,
    }
    return render(request, 'organization/request_team_transfer.html', context)


# ============================================
# LİDER ATMA OYLAMA SİSTEMİ
# ============================================

@login_required
def initiate_leader_removal(request):
    """Lider atma oylaması başlat"""
    from .models import LeaderRemovalVote, Team
    from django.utils import timezone

    user_team = request.user.current_team
    if not user_team:
        messages.error(request, 'Bir ekibe üye olmalısınız.')
        return redirect('organization:my_team')

    # Sadece ekip üyeleri başlatabilir (lider hariç)
    if user_team.leader == request.user:
        messages.error(request, 'Lider olarak kendi atma oylamanızı başlatamazsınız.')
        return redirect('organization:team_manage')

    # Zaten aktif bir atma oylaması var mı?
    active_removal = LeaderRemovalVote.objects.filter(
        level='TEAM',
        entity_id=user_team.id,
        status='ACTIVE',
        end_date__gt=timezone.now()
    ).first()

    if active_removal:
        messages.warning(request, 'Zaten aktif bir lider atma oylaması var!')
        return redirect('organization:removal_vote_detail', vote_id=active_removal.id)

    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()

        if not reason:
            messages.error(request, 'Lütfen bir gerekçe yazın.')
            return redirect('organization:initiate_leader_removal')

        if len(reason) < 50:
            messages.error(request, 'Gerekçe en az 50 karakter olmalıdır.')
            return redirect('organization:initiate_leader_removal')

        # Atma oylaması oluştur
        removal_vote = LeaderRemovalVote.objects.create(
            level='TEAM',
            entity_id=user_team.id,
            current_leader=user_team.leader,
            initiated_by=request.user,
            reason=reason
        )

        # Başlatanın oyu otomatik "EVET"
        from .models import RemovalVoteCast
        RemovalVoteCast.objects.create(
            removal_vote=removal_vote,
            voter=request.user,
            vote='YES'
        )
        removal_vote.yes_votes = 1
        removal_vote.save()

        # Bildirim gönder
        from notifications.utils import create_notification
        from users.models import User

        # Tüm ekip üyelerine bildirim
        team_members = User.objects.filter(current_team=user_team).exclude(id=request.user.id)
        for member in team_members:
            create_notification(
                user=member,
                notification_type='leader_removal_started',
                title='Lider Atma Oylaması Başlatıldı',
                message=f'{request.user.username}, {user_team.leader.username} için lider atma oylaması başlattı.',
                related_url=f'/organization/removal-vote/{removal_vote.id}/'
            )

        messages.success(request, 'Lider atma oylaması başlatıldı! Oylama 1 hafta sürecek.')
        return redirect('organization:removal_vote_detail', vote_id=removal_vote.id)

    context = {
        'team': user_team,
    }
    return render(request, 'organization/initiate_leader_removal.html', context)


@login_required
def removal_vote_detail(request, vote_id):
    """Lider atma oylaması detay sayfası"""
    from .models import LeaderRemovalVote, RemovalVoteCast
    from django.utils import timezone

    removal_vote = get_object_or_404(LeaderRemovalVote, id=vote_id)

    # Yetki kontrolü - sadece ilgili ekip/takım/birlik üyeleri görebilir
    user_team = request.user.current_team
    if not user_team or removal_vote.entity_id != user_team.id:
        messages.error(request, 'Bu oylamayı görme yetkiniz yok.')
        return redirect('organization:my_team')

    # Kullanıcının oyu var mı?
    user_vote = RemovalVoteCast.objects.filter(
        removal_vote=removal_vote,
        voter=request.user
    ).first()

    # Oylama bitti mi?
    is_ended = timezone.now() > removal_vote.end_date or removal_vote.status != 'ACTIVE'

    # Toplam oy sayısı ve yüzdeler
    total_votes = removal_vote.yes_votes + removal_vote.no_votes
    total_members = user_team.member_count

    yes_percentage = (removal_vote.yes_votes / total_votes * 100) if total_votes > 0 else 0
    no_percentage = (removal_vote.no_votes / total_votes * 100) if total_votes > 0 else 0

    context = {
        'removal_vote': removal_vote,
        'user_vote': user_vote,
        'is_ended': is_ended,
        'total_votes': total_votes,
        'total_members': total_members,
        'yes_percentage': yes_percentage,
        'no_percentage': no_percentage,
        'team': user_team,
    }
    return render(request, 'organization/removal_vote_detail.html', context)


@login_required
def cast_removal_vote(request, vote_id):
    """Lider atma oylamasında oy kullan"""
    from .models import LeaderRemovalVote, RemovalVoteCast
    from django.utils import timezone

    if request.method != 'POST':
        return redirect('organization:removal_vote_detail', vote_id=vote_id)

    removal_vote = get_object_or_404(LeaderRemovalVote, id=vote_id)

    # Yetki kontrolü
    user_team = request.user.current_team
    if not user_team or removal_vote.entity_id != user_team.id:
        messages.error(request, 'Bu oylamada oy kullanma yetkiniz yok.')
        return redirect('organization:my_team')

    # Lider oy kullanamaz
    if request.user == removal_vote.current_leader:
        messages.error(request, 'Lider olarak kendi atma oylamanızda oy kullanamazsınız.')
        return redirect('organization:removal_vote_detail', vote_id=vote_id)

    # Oylama bitti mi?
    if timezone.now() > removal_vote.end_date or removal_vote.status != 'ACTIVE':
        messages.error(request, 'Bu oylama sona ermiştir.')
        return redirect('organization:removal_vote_detail', vote_id=vote_id)

    # Zaten oy kullandı mı?
    existing_vote = RemovalVoteCast.objects.filter(
        removal_vote=removal_vote,
        voter=request.user
    ).first()

    vote_choice = request.POST.get('vote')
    if vote_choice not in ['YES', 'NO']:
        messages.error(request, 'Geçersiz oy seçimi.')
        return redirect('organization:removal_vote_detail', vote_id=vote_id)

    if existing_vote:
        # Oy değiştirme
        old_vote = existing_vote.vote
        existing_vote.vote = vote_choice
        existing_vote.save()

        # Sayıları güncelle
        if old_vote == 'YES' and vote_choice == 'NO':
            removal_vote.yes_votes -= 1
            removal_vote.no_votes += 1
        elif old_vote == 'NO' and vote_choice == 'YES':
            removal_vote.no_votes -= 1
            removal_vote.yes_votes += 1

        removal_vote.save()
        messages.success(request, 'Oyunuz değiştirildi.')
    else:
        # Yeni oy
        RemovalVoteCast.objects.create(
            removal_vote=removal_vote,
            voter=request.user,
            vote=vote_choice
        )

        if vote_choice == 'YES':
            removal_vote.yes_votes += 1
        else:
            removal_vote.no_votes += 1

        removal_vote.save()
        messages.success(request, 'Oyunuz kaydedildi.')

    return redirect('organization:removal_vote_detail', vote_id=vote_id)
