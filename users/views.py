from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import User

def home(request):
    """Ana sayfa - Akış (Activity Feed)"""
    from doctrine.models import DoctrineArticle, Proposal, Vote, Activity
    from organization.models import Team, Squad, Union
    from django.core.paginator import Paginator

    # Platform istatistikleri (herkes için)
    stats = {
        'total_users': User.objects.count(),
        'total_teams': Team.objects.count(),
        'total_squads': Squad.objects.count(),
        'total_unions': Union.objects.count(),
        'total_articles': DoctrineArticle.objects.filter(is_active=True).count(),
        'active_proposals': Proposal.objects.filter(status='ACTIVE').count(),
        'total_votes': Vote.objects.count(),
        'passed_proposals': Proposal.objects.filter(status='PASSED').count(),
    }

    # Akış - Son aktiviteler (herkes için)
    all_activities = Activity.objects.select_related('user').order_by('-created_at')

    # Sayfalama
    paginator = Paginator(all_activities, 20)  # Her sayfada 20 aktivite
    page_number = request.GET.get('page', 1)
    activities = paginator.get_page(page_number)

    context = {
        'stats': stats,
        'activities': activities,
    }

    # Giriş yapmış kullanıcılar için ekstra bilgiler
    if request.user.is_authenticated:
        from notifications.models import Notification

        # Kullanıcının oy kullanmadığı aktif öneriler
        user_votes = Vote.objects.filter(user=request.user).values_list('proposal_id', flat=True)
        pending_votes = Proposal.objects.filter(status='ACTIVE').exclude(id__in=user_votes).order_by('-start_date')[:3]

        # Kullanıcı istatistikleri
        user_stats = {
            'total_votes': Vote.objects.filter(user=request.user).count(),
            'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
        }

        context['pending_votes'] = pending_votes
        context['user_stats'] = user_stats

    return render(request, 'users/home.html', context)

def register(request):
    """Kayıt sayfası"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        province = request.POST.get('province')
        district = request.POST.get('district')
        
        # Validasyon
        if password != password2:
            messages.error(request, 'Şifreler eşleşmiyor.')
            return render(request, 'users/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Bu kullanıcı adı zaten kullanılıyor.')
            return render(request, 'users/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Bu email adresi zaten kayıtlı.')
            return render(request, 'users/register.html')
        
        # Kullanıcı oluştur
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            province=province,
            district=district
        )
        
        # Email doğrulama token'ı oluştur ve gönder
        user.generate_verification_token()

        # Email gönder
        from django.core.mail import send_mail
        from django.urls import reverse
        from users.emails import send_welcome_email

        verification_url = request.build_absolute_uri(
            reverse('users:verify_email', args=[user.email_verification_token])
        )

        send_mail(
            subject='Bizlik - Email Doğrulama',
            message=f'Merhaba {user.username},\n\nEmail adresinizi doğrulamak için aşağıdaki linke tıklayın:\n\n{verification_url}\n\nBu link 24 saat geçerlidir.',
            from_email='noreply@doktrin.com',
            recipient_list=[user.email],
            fail_silently=False,
        )

        # Hoş geldiniz e-postası gönder
        send_welcome_email(user)

        messages.success(request, 'Kayıt başarılı! Email adresinize doğrulama linki gönderildi.')
        return redirect('users:login')
    
    return render(request, 'users/register.html')

def login_view(request):
    """Giriş sayfası"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('users:home')
        else:
            messages.error(request, 'Kullanıcı adı veya şifre hatalı.')
    return render(request, 'users/login.html')

def logout_view(request):
    """Çıkış"""
    logout(request)
    return redirect('users:home')

@login_required
def profile(request):
    """Profil sayfası"""
    from doctrine.models import Vote, Discussion, Proposal
    from organization.models import LeaderVote, FormationVote
    from notifications.models import Notification

    # İstatistikler
    total_votes = Vote.objects.filter(user=request.user).count()
    total_comments = Discussion.objects.filter(user=request.user).count()
    total_proposals_created = Proposal.objects.filter(
        proposed_by_level__in=['SQUAD', 'UNION', 'PROVINCE_ORG']
    ).count()  # Basitleştirilmiş - gerçekte user'a göre filtrelenmeli

    # Oy dağılımı
    yes_votes = Vote.objects.filter(user=request.user, vote_choice='YES').count()
    abstain_votes = Vote.objects.filter(user=request.user, vote_choice='ABSTAIN').count()
    veto_votes = Vote.objects.filter(user=request.user, vote_choice='VETO').count()

    # Son aktiviteler
    recent_votes = Vote.objects.filter(user=request.user).select_related('proposal').order_by('-voted_at')[:5]
    recent_comments = Discussion.objects.filter(user=request.user).select_related('proposal').order_by('-created_at')[:5]

    # Liderlik pozisyonları
    is_team_leader = request.user.current_team and request.user.current_team.leader == request.user
    is_squad_leader = (request.user.current_team and
                      request.user.current_team.parent_squad and
                      request.user.current_team.parent_squad.leader == request.user)
    is_union_leader = (request.user.current_team and
                      request.user.current_team.parent_squad and
                      request.user.current_team.parent_squad.parent_union and
                      request.user.current_team.parent_squad.parent_union.leader == request.user)
    is_province_leader = (request.user.current_team and
                         request.user.current_team.parent_squad and
                         request.user.current_team.parent_squad.parent_union and
                         request.user.current_team.parent_squad.parent_union.parent_province_org and
                         request.user.current_team.parent_squad.parent_union.parent_province_org.leader == request.user)

    # Bildirimler
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()

    context = {
        'total_votes': total_votes,
        'total_comments': total_comments,
        'total_proposals_created': total_proposals_created,
        'yes_votes': yes_votes,
        'abstain_votes': abstain_votes,
        'veto_votes': veto_votes,
        'recent_votes': recent_votes,
        'recent_comments': recent_comments,
        'is_team_leader': is_team_leader,
        'is_squad_leader': is_squad_leader,
        'is_union_leader': is_union_leader,
        'is_province_leader': is_province_leader,
        'unread_notifications': unread_notifications,
    }
    return render(request, 'users/profile.html', context)

def verify_email(request, token):
    """Email doğrulama"""
    try:
        user = User.objects.get(email_verification_token=token)
        if user.token_expires_at and user.token_expires_at > timezone.now():
            user.is_email_verified = True
            user.email_verification_token = None
            user.save()
            messages.success(request, 'Email adresiniz doğrulandı!')
        else:
            messages.error(request, 'Doğrulama linki süresi dolmuş.')
    except User.DoesNotExist:
        messages.error(request, 'Geçersiz doğrulama linki.')
    return redirect('users:login')
@login_required
def user_profile(request, username):
    """Başka bir kullanıcının profil sayfası"""
    from django.contrib.auth import get_user_model
    from doctrine.models import Vote, Discussion
    
    User = get_user_model()
    profile_user = get_object_or_404(User, username=username)
    
    # İstatistikler
    total_votes = Vote.objects.filter(user=profile_user).count()
    total_comments = Discussion.objects.filter(user=profile_user).count()
    
    # Oy dağılımı
    yes_votes = Vote.objects.filter(user=profile_user, vote_choice='YES').count()
    abstain_votes = Vote.objects.filter(user=profile_user, vote_choice='ABSTAIN').count()
    veto_votes = Vote.objects.filter(user=profile_user, vote_choice='VETO').count()
    
    # Son aktiviteler (sadece yorumlar - oylar gizli)
    recent_comments = Discussion.objects.filter(user=profile_user).select_related('proposal', 'article').order_by('-created_at')[:10]
    
    # Organizational info
    team_info = None
    if profile_user.current_team:
        team_info = {
            'team': profile_user.current_team,
            'is_team_leader': profile_user.current_team.leader == profile_user,
            'squad': profile_user.current_team.parent_squad,
            'is_squad_leader': profile_user.current_team.parent_squad and profile_user.current_team.parent_squad.leader == profile_user,
            'union': profile_user.current_team.parent_squad.parent_union if profile_user.current_team.parent_squad else None,
            'is_union_leader': (profile_user.current_team.parent_squad and 
                              profile_user.current_team.parent_squad.parent_union and 
                              profile_user.current_team.parent_squad.parent_union.leader == profile_user),
        }
    
    context = {
        'profile_user': profile_user,
        'total_votes': total_votes,
        'total_comments': total_comments,
        'yes_votes': yes_votes,
        'abstain_votes': abstain_votes,
        'veto_votes': veto_votes,
        'recent_comments': recent_comments,
        'team_info': team_info,
        'is_own_profile': request.user == profile_user,
    }
    
    return render(request, 'users/user_profile.html', context)


@login_required
def user_guide(request):
    """Kullanım Kılavuzu - Tüm sistem özellikleri"""
    return render(request, 'users/user_guide.html')


@login_required
def vote_statistics(request):
    """Kullanıcının detaylı oy istatistikleri"""
    from doctrine.models import Vote, Proposal
    from django.db.models import Count, Q
    from django.core.paginator import Paginator

    # Tüm oylar (sayfalama ile)
    all_votes = Vote.objects.filter(user=request.user).select_related(
        'proposal', 'proposal__related_article'
    ).order_by('-voted_at')

    # Sayfalama
    paginator = Paginator(all_votes, 20)
    page_number = request.GET.get('page', 1)
    votes = paginator.get_page(page_number)

    # Genel istatistikler
    total_votes = Vote.objects.filter(user=request.user).count()
    yes_votes = Vote.objects.filter(user=request.user, vote_choice='YES').count()
    abstain_votes = Vote.objects.filter(user=request.user, vote_choice='ABSTAIN').count()
    veto_votes = Vote.objects.filter(user=request.user, vote_choice='VETO').count()

    # Yüzdeler
    yes_percentage = (yes_votes / total_votes * 100) if total_votes > 0 else 0
    abstain_percentage = (abstain_votes / total_votes * 100) if total_votes > 0 else 0
    veto_percentage = (veto_votes / total_votes * 100) if total_votes > 0 else 0

    # Kabul/red oranları (kullanıcının oy verdiği önerilerden)
    voted_proposals = Proposal.objects.filter(
        id__in=Vote.objects.filter(user=request.user).values_list('proposal_id', flat=True)
    )
    passed_proposals = voted_proposals.filter(status='PASSED').count()
    rejected_proposals = voted_proposals.filter(status='REJECTED').count()

    # Başarı oranı (kullanıcının YES dediği önerilerden kaçı geçti?)
    user_yes_proposals = voted_proposals.filter(
        id__in=Vote.objects.filter(user=request.user, vote_choice='YES').values_list('proposal_id', flat=True)
    )
    success_rate = 0
    if user_yes_proposals.count() > 0:
        successful_yes = user_yes_proposals.filter(status='PASSED').count()
        success_rate = (successful_yes / user_yes_proposals.count()) * 100

    # Delegasyon bilgisi
    delegators_count = request.user.delegated_voters.count()
    current_delegate = request.user.vote_delegate

    # Aktif oylamalar (henüz oy kullanılmamış)
    user_vote_ids = Vote.objects.filter(user=request.user).values_list('proposal_id', flat=True)
    pending_votes = Proposal.objects.filter(status='ACTIVE').exclude(id__in=user_vote_ids).count()

    context = {
        'votes': votes,
        'total_votes': total_votes,
        'yes_votes': yes_votes,
        'abstain_votes': abstain_votes,
        'veto_votes': veto_votes,
        'yes_percentage': yes_percentage,
        'abstain_percentage': abstain_percentage,
        'veto_percentage': veto_percentage,
        'passed_proposals': passed_proposals,
        'rejected_proposals': rejected_proposals,
        'success_rate': success_rate,
        'delegators_count': delegators_count,
        'current_delegate': current_delegate,
        'pending_votes': pending_votes,
    }

    return render(request, 'users/vote_statistics.html', context)


@login_required
def vote_delegation(request):
    """Oy delegasyonu ayarları"""
    if request.method == 'POST':
        delegate_id = request.POST.get('delegate_id')

        if delegate_id == 'none':
            # Delegasyonu kaldır
            request.user.vote_delegate = None
            request.user.save()
            messages.success(request, 'Oy delegasyonu kaldırıldı. Artık kendi oyunuzu kullanacaksınız veya ekip liderinizin oyuyla birlikte oy kullanacaksınız.')
        elif delegate_id:
            try:
                delegate = User.objects.get(id=delegate_id)

                # Kendi kendine delege olamaz
                if delegate == request.user:
                    messages.error(request, 'Kendi kendinize delege olamazsınız!')
                    return redirect('users:vote_delegation')

                # Sonsuz döngü kontrolü
                if request.user in delegate.get_delegation_chain():
                    messages.error(request, 'Bu delegasyon sonsuz döngü oluşturur!')
                    return redirect('users:vote_delegation')

                request.user.vote_delegate = delegate
                request.user.save()
                messages.success(request, f'Oylarınız {delegate.username} kullanıcısına devredildi!')

            except User.DoesNotExist:
                messages.error(request, 'Kullanıcı bulunamadı!')

        return redirect('users:vote_delegation')

    # Ekip üyeleri (delege olabilir)
    potential_delegates = []
    if request.user.current_team:
        potential_delegates = request.user.current_team.members.exclude(id=request.user.id)

    # Bana delege eden kullanıcılar
    delegators = request.user.delegated_voters.all()

    # Delegasyon zinciri
    delegation_chain = request.user.get_delegation_chain()

    # Ekip lideri
    team_leader = None
    if request.user.current_team and request.user.current_team.leader:
        team_leader = request.user.current_team.leader

    context = {
        'current_delegate': request.user.vote_delegate,
        'potential_delegates': potential_delegates,
        'delegators': delegators,
        'delegation_chain': delegation_chain,
        'team_leader': team_leader,
    }

    return render(request, 'users/vote_delegation.html', context)


@login_required
def delegate_votes(request):
    """Delegenin oy kullanma geçmişini göster"""
    from doctrine.models import Vote, Proposal
    from django.core.paginator import Paginator

    # Kullanıcının bir delegesi var mı kontrol et
    if not request.user.vote_delegate:
        messages.warning(request, 'Henüz bir delege belirlemediniz.')
        return redirect('users:vote_delegation')

    delegate = request.user.vote_delegate

    # Delegenin tüm oyları
    all_votes = Vote.objects.filter(user=delegate).select_related(
        'proposal', 'proposal__related_article'
    ).order_by('-voted_at')

    # Sayfalama
    paginator = Paginator(all_votes, 20)
    page_number = request.GET.get('page', 1)
    votes = paginator.get_page(page_number)

    # İstatistikler
    total_votes = Vote.objects.filter(user=delegate).count()
    yes_votes = Vote.objects.filter(user=delegate, vote_choice='YES').count()
    abstain_votes = Vote.objects.filter(user=delegate, vote_choice='ABSTAIN').count()
    veto_votes = Vote.objects.filter(user=delegate, vote_choice='VETO').count()

    # Yüzdeler
    yes_percentage = (yes_votes / total_votes * 100) if total_votes > 0 else 0
    abstain_percentage = (abstain_votes / total_votes * 100) if total_votes > 0 else 0
    veto_percentage = (veto_votes / total_votes * 100) if total_votes > 0 else 0

    # Kullanıcının kendi oyları ile karşılaştırma
    user_votes = Vote.objects.filter(user=request.user).count()

    # Aktif oylamalar (delege henüz oy kullanmamış)
    delegate_vote_ids = Vote.objects.filter(user=delegate).values_list('proposal_id', flat=True)
    pending_votes = Proposal.objects.filter(status='ACTIVE').exclude(id__in=delegate_vote_ids).count()

    context = {
        'delegate': delegate,
        'votes': votes,
        'total_votes': total_votes,
        'yes_votes': yes_votes,
        'abstain_votes': abstain_votes,
        'veto_votes': veto_votes,
        'yes_percentage': yes_percentage,
        'abstain_percentage': abstain_percentage,
        'veto_percentage': veto_percentage,
        'user_votes': user_votes,
        'pending_votes': pending_votes,
    }

    return render(request, 'users/delegate_votes.html', context)
