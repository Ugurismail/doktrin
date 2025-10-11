from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import DoctrineArticle, Proposal, Vote, Discussion, DiscussionVote, Activity, ArticleTag, ProposalDraft
from .vote_calculator import calculate_votes_with_multipliers
from notifications.utils import notify_comment_reply
from config.rate_limit import rate_limit


def doctrine_list(request):
    """Doktrin listesi"""
    search_query = request.GET.get('search', '').strip()
    tag_filter = request.GET.get('tag', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    created_by = request.GET.get('created_by', '').strip()

    # Kuruluş ilkeleri
    foundation_laws = DoctrineArticle.objects.filter(
        article_type='FOUNDATION_LAW',
        is_active=True
    ).prefetch_related('tags').select_related('created_by')

    # Etiket filtresi varsa uygula
    if tag_filter:
        foundation_laws = foundation_laws.filter(tags__slug=tag_filter)

    # Tarih filtresi
    if date_from:
        foundation_laws = foundation_laws.filter(created_date__gte=date_from)
    if date_to:
        foundation_laws = foundation_laws.filter(created_date__lte=date_to)

    # Kullanıcı filtresi
    if created_by:
        foundation_laws = foundation_laws.filter(created_by__username__icontains=created_by)

    # Arama varsa filtrele
    if search_query:
        foundation_laws = foundation_laws.filter(
            Q(content__icontains=search_query) |
            Q(justification__icontains=search_query) |
            Q(article_number__icontains=search_query)
        )

    foundation_laws = foundation_laws.order_by('article_number').distinct()

    # Normal yasalar
    normal_laws_all = DoctrineArticle.objects.filter(
        article_type='NORMAL_LAW',
        is_active=True
    ).prefetch_related('tags').select_related('created_by')

    # Etiket filtresi varsa uygula
    if tag_filter:
        normal_laws_all = normal_laws_all.filter(tags__slug=tag_filter)

    # Tarih filtresi
    if date_from:
        normal_laws_all = normal_laws_all.filter(created_date__gte=date_from)
    if date_to:
        normal_laws_all = normal_laws_all.filter(created_date__lte=date_to)

    # Kullanıcı filtresi
    if created_by:
        normal_laws_all = normal_laws_all.filter(created_by__username__icontains=created_by)

    # Arama varsa filtrele
    if search_query:
        normal_laws_all = normal_laws_all.filter(
            Q(content__icontains=search_query) |
            Q(justification__icontains=search_query) |
            Q(article_number__icontains=search_query)
        )

    normal_laws_all = normal_laws_all.order_by('article_number').distinct()

    paginator = Paginator(normal_laws_all, 20)
    page_number = request.GET.get('page', 1)
    normal_laws = paginator.get_page(page_number)

    # Aktif oylamalar
    proposal_type_filter = request.GET.get('proposal_type', '').strip()
    proposal_status_filter = request.GET.get('proposal_status', '').strip()

    active_proposals = Proposal.objects.filter(status='ACTIVE')

    # Öneri türü filtresi
    if proposal_type_filter:
        active_proposals = active_proposals.filter(proposal_type=proposal_type_filter)

    # Tarih filtresi
    if date_from:
        active_proposals = active_proposals.filter(start_date__gte=date_from)
    if date_to:
        active_proposals = active_proposals.filter(start_date__lte=date_to)

    # Arama varsa filtrele
    if search_query:
        active_proposals = active_proposals.filter(
            Q(proposed_content__icontains=search_query) |
            Q(justification__icontains=search_query) |
            Q(proposal_type__icontains=search_query)
        )

    active_proposals = active_proposals.order_by('-start_date')
    show_all_proposals = request.GET.get('show_all') == 'true'

    # Arşiv önerileri (pagination)
    archived_all = Proposal.objects.filter(
        status__in=['PASSED', 'REJECTED', 'ARCHIVED']
    )

    # Durum filtresi
    if proposal_status_filter:
        archived_all = archived_all.filter(status=proposal_status_filter)

    # Öneri türü filtresi
    if proposal_type_filter:
        archived_all = archived_all.filter(proposal_type=proposal_type_filter)

    # Tarih filtresi
    if date_from:
        archived_all = archived_all.filter(start_date__gte=date_from)
    if date_to:
        archived_all = archived_all.filter(start_date__lte=date_to)

    # Arama varsa filtrele
    if search_query:
        archived_all = archived_all.filter(
            Q(proposed_content__icontains=search_query) |
            Q(justification__icontains=search_query) |
            Q(proposal_type__icontains=search_query)
        )

    archived_all = archived_all.order_by('-end_date')

    archive_paginator = Paginator(archived_all, 30)
    archive_page = request.GET.get('archive_page', 1)
    archived_proposals = archive_paginator.get_page(archive_page)

    # Tüm etiketleri al - filtreleme için
    all_tags = ArticleTag.objects.all().order_by('name')
    selected_tag = None
    if tag_filter:
        try:
            selected_tag = ArticleTag.objects.get(slug=tag_filter)
        except ArticleTag.DoesNotExist:
            pass

    context = {
        'foundation_laws': foundation_laws,
        'normal_laws': normal_laws,
        'active_proposals': active_proposals,
        'show_all_proposals': show_all_proposals,
        'archived_proposals': archived_proposals,
        'search_query': search_query,
        'all_tags': all_tags,
        'selected_tag': selected_tag,
        'date_from': date_from,
        'date_to': date_to,
        'created_by': created_by,
        'proposal_type_filter': proposal_type_filter,
        'proposal_status_filter': proposal_status_filter,
    }
    return render(request, 'doctrine/doctrine_list.html', context)



@login_required
@rate_limit(limit=20, period=60, message="Çok fazla yorum gönderiyorsunuz. Lütfen bir dakika bekleyin.")
def proposal_detail(request, proposal_id):
    """Öneri detay ve tartışma"""
    proposal = get_object_or_404(Proposal, id=proposal_id)

    # Pagination için tüm yorumları al (en çok upvote alanlar üstte)
    all_discussions = proposal.discussions.filter(parent_comment__isnull=True).select_related('user').order_by('-upvotes', '-created_at')

    # Pagination: 20 yorum per sayfa
    paginator = Paginator(all_discussions, 20)
    page_number = request.GET.get('page', 1)
    discussions = paginator.get_page(page_number)

    user_vote = None

    try:
        user_vote = Vote.objects.get(proposal=proposal, user=request.user)
    except Vote.DoesNotExist:
        pass

    if request.method == 'POST' and 'comment' in request.POST:
        comment_text = request.POST.get('comment', '').strip()
        parent_id = request.POST.get('parent_comment_id')

        if comment_text:
            new_comment = Discussion.objects.create(
                article=proposal.related_article if proposal.related_article else None,
                proposal=proposal,
                user=request.user,
                comment_text=comment_text,
                parent_comment_id=parent_id if parent_id else None
            )

            # Eğer yanıt ise bildirim gönder
            if parent_id:
                try:
                    parent_comment = Discussion.objects.get(id=parent_id)
                    if parent_comment.user != request.user:  # Kendine yanıt vermediyse
                        notify_comment_reply(new_comment, parent_comment)
                except Discussion.DoesNotExist:
                    pass

            messages.success(request, 'Yorumunuz eklendi!')
            return redirect('doctrine:proposal_detail', proposal_id=proposal_id)

    context = {
        'proposal': proposal,
        'discussions': discussions,
        'user_vote': user_vote,
    }
    return render(request, 'doctrine/proposal_detail.html', context)


@login_required
@rate_limit(limit=30, period=60, message="Çok fazla oy kullanıyorsunuz. Lütfen bir dakika bekleyin.")
def vote_proposal(request, proposal_id):
    """Oy kullanma"""
    from django.utils import timezone

    proposal = get_object_or_404(Proposal, id=proposal_id)

    # Ekip kontrolü - Ekibi olmayanlar oy kullanamaz
    if not request.user.current_team:
        messages.error(request, 'Oy kullanmak için bir ekibe dahil olmalısınız!')
        return redirect('doctrine:proposal_detail', proposal_id=proposal_id)

    if request.method == 'POST':
        vote_choice = request.POST.get('vote_choice')

        if not vote_choice:
            messages.error(request, 'Lütfen bir oy seçeneği seçin!')
            return redirect('doctrine:proposal_detail', proposal_id=proposal_id)

        # Mevcut oyu kontrol et
        try:
            existing_vote = Vote.objects.get(proposal=proposal, user=request.user)

            # 24 saat kontrolü
            if not existing_vote.can_change_vote():
                messages.error(request, 'Oyunuzu değiştirmek için 24 saat beklemelisiniz!')
                return redirect('doctrine:proposal_detail', proposal_id=proposal_id)

            # Oy değiştirilebilir - güncelle
            existing_vote.vote_choice = vote_choice
            existing_vote.last_changed_at = timezone.now()
            existing_vote.save()

        except Vote.DoesNotExist:
            # İlk kez oy kullanıyor
            Vote.objects.create(
                proposal=proposal,
                user=request.user,
                vote_choice=vote_choice
            )

        # Çarpan mekanizması ile oy hesaplama
        try:
            vote_results = calculate_votes_with_multipliers(proposal)
            proposal.vote_yes_count = vote_results['YES']
            proposal.vote_abstain_count = vote_results['ABSTAIN']
            proposal.vote_veto_count = vote_results['VETO']
        except Exception as e:
            print(f"Çarpan hesaplama hatası: {e}")
            # Hata olursa basit sayıma geç
            proposal.vote_yes_count = proposal.votes.filter(vote_choice='YES').count()
            proposal.vote_abstain_count = proposal.votes.filter(vote_choice='ABSTAIN').count()
            proposal.vote_veto_count = proposal.votes.filter(vote_choice='VETO').count()

        proposal.save()  # ÖNEMLİ: Her durumda kaydet
        messages.success(request, 'Oyunuz kaydedildi!')
        return redirect('doctrine:proposal_detail', proposal_id=proposal_id)

    return redirect('doctrine:proposal_detail', proposal_id=proposal_id)

@login_required
@rate_limit(limit=5, period=300, message="Çok fazla öneri oluşturuyorsunuz. Lütfen 5 dakika bekleyin.")
def create_proposal(request):
    """Öneri oluştur - Yetki: Sadece Ekip Liderleri"""
    user_team = request.user.current_team

    if not user_team:
        messages.error(request, 'Öneri oluşturmak için bir ekibe dahil olmalısınız.')
        return redirect('doctrine:doctrine_list')

    # Ekip lideri kontrolü
    if user_team.leader != request.user:
        messages.error(request, 'Öneri oluşturma yetkisi sadece ekip liderlerine aittir.')
        return redirect('doctrine:doctrine_list')

    # Kurucu kontrolü
    is_founder = hasattr(request.user, 'is_founder') and request.user.is_founder

    # Kullanıcının seviyesini belirle
    user_level = None
    if is_founder:
        user_level = 'FOUNDER'
    elif user_team.parent_squad:
        user_level = 'SQUAD'
        if user_team.parent_squad.parent_union:
            user_level = 'UNION'
    else:
        # Ekip seviyesinde - En az 8 kişi olmalı
        if user_team.member_count >= 8:
            user_level = 'TEAM'
        else:
            messages.error(request, f'Öneri oluşturmak için ekibinizde en az 8 kişi olmalı. Şu anki üye sayısı: {user_team.member_count}')
            return redirect('doctrine:doctrine_list')

    if user_level not in ['TEAM', 'SQUAD', 'UNION', 'FOUNDER']:
        messages.error(request, f'Öneri oluşturma yetkiniz yok. Seviyeniz: {user_level}')
        return redirect('doctrine:doctrine_list')
    
    if request.method == 'POST':
        proposal_type = request.POST.get('proposal_type')
        proposed_content = request.POST.get('proposed_content')
        justification = request.POST.get('justification')
        related_article_id = request.POST.get('related_article')
        selected_tags = request.POST.getlist('tags')  # Seçilen etiketler

        # Eski madde içeriğini kaydet (MODIFY ve REMOVE için)
        original_content = None
        if related_article_id and proposal_type in ['MODIFY', 'REMOVE']:
            article = DoctrineArticle.objects.get(id=related_article_id)
            original_content = article.content

            # Yetki kontrolü: İlkeleri sadece Kurucu ve Birlik değiştirebilir/kaldırabilir
            if article.article_type == 'FOUNDATION_LAW':
                if user_level not in ['FOUNDER', 'UNION']:
                    messages.error(request, 'Kuruluş İlkelerini sadece Kurucu ve Birlikler değiştirebilir/kaldırabilir!')
                    return redirect('doctrine:create_proposal')

        # REMOVE için proposed_content boş olabilir, ama justification zorunlu
        if proposal_type == 'REMOVE':
            if not justification:
                messages.error(request, 'Madde kaldırma için gerekçe zorunludur!')
                return redirect('doctrine:create_proposal')
            # REMOVE için proposed_content boş string olsun
            if not proposed_content:
                proposed_content = f"[Madde {article.article_number} kaldırılıyor]"

        # Entity ID'yi belirle
        entity_id = None
        if user_level == 'FOUNDER':
            entity_id = 0  # Kurucular için özel ID
        elif user_level == 'TEAM':
            entity_id = user_team.id  # Ekip ID'si
        elif user_level == 'SQUAD':
            entity_id = user_team.parent_squad.id
        elif user_level == 'UNION':
            entity_id = user_team.parent_squad.parent_union.id

        # Öneriyi oluştur
        proposal = Proposal.objects.create(
            proposal_type=proposal_type,
            related_article_id=related_article_id if related_article_id else None,
            original_article_content=original_content,
            proposed_content=proposed_content,
            justification=justification,
            proposed_by_level=user_level,
            proposed_by_entity_id=entity_id
        )

        # Eğer yeni madde önerisi ise ve etiketler seçildiyse, proposal'a not ekle
        if proposal_type == 'ADD' and selected_tags:
            proposal.proposed_tags = ','.join(selected_tags)  # Etiket ID'lerini virgülle ayırarak sakla
            proposal.save()

        # Bildirim gönder - İlgili seviyedeki tüm üyelere
        from notifications.utils import notify_new_proposal
        from users.models import User

        if user_level == 'FOUNDER':
            target_users = User.objects.filter(is_active=True).exclude(id=request.user.id)
        elif user_level == 'TEAM':
            target_users = User.objects.filter(current_team_id=entity_id).exclude(id=request.user.id)
        elif user_level == 'SQUAD':
            target_users = User.objects.filter(current_team__parent_squad_id=entity_id).exclude(id=request.user.id)
        elif user_level == 'UNION':
            target_users = User.objects.filter(current_team__parent_squad__parent_union_id=entity_id).exclude(id=request.user.id)
        else:
            target_users = []

        notify_new_proposal(proposal, target_users)

        # E-posta bildirimi gönder
        from users.emails import send_new_proposal_email
        for user in target_users:
            send_new_proposal_email(user, proposal)

        # Aktivite oluştur
        Activity.objects.create(
            activity_type='proposal_created',
            user=request.user,
            description=f'{proposal.get_proposal_type_display()} önerisi oluşturdu',
            related_url=f'/doctrine/proposal/{proposal.id}/'
        )

        messages.success(request, 'Öneriniz oluşturuldu ve oylamaya açıldı!')
        return redirect('doctrine:proposal_detail', proposal_id=proposal.id)
    
    # Mevcut maddeleri listele - Takım seviyesinde ilkeleri gösterme
    if user_level == 'SQUAD':
        all_articles = DoctrineArticle.objects.filter(is_active=True, article_type='NORMAL_LAW').order_by('article_number')
    else:
        all_articles = DoctrineArticle.objects.filter(is_active=True).order_by('article_type', 'article_number')

    # Tüm etiketleri al
    all_tags = ArticleTag.objects.all()

    context = {
        'user_level': user_level,
        'all_articles': all_articles,
        'all_tags': all_tags,
    }
    return render(request, 'doctrine/create_proposal.html', context)

@login_required
@rate_limit(limit=30, period=60, message="Çok fazla oy kullanıyorsunuz. Lütfen bir dakika bekleyin.")
def vote_discussion(request, discussion_id):
    """Yoruma oy ver (upvote/downvote)"""
    discussion = get_object_or_404(Discussion, id=discussion_id)

    # Kullanıcı kendi yorumuna oy veremez
    if discussion.user == request.user:
        messages.error(request, 'Kendi yorumunuza oy veremezsiniz!')
        # Proposal üzerindeyse ona, article üzerindeyse ona yönlendir
        if discussion.proposal:
            return redirect('doctrine:proposal_detail', proposal_id=discussion.proposal.id)
        elif discussion.article:
            return redirect('doctrine:article_detail', article_id=discussion.article.id)
        else:
            return redirect('doctrine:doctrine_list')

    if request.method == 'POST':
        vote_type = request.POST.get('vote_type')  # 'UP' veya 'DOWN'

        if vote_type not in ['UP', 'DOWN']:
            messages.error(request, 'Geçersiz oy tipi!')
            if discussion.proposal:
                return redirect('doctrine:proposal_detail', proposal_id=discussion.proposal.id)
            elif discussion.article:
                return redirect('doctrine:article_detail', article_id=discussion.article.id)
            else:
                return redirect('doctrine:doctrine_list')

        # Mevcut oyu kontrol et
        try:
            existing_vote = DiscussionVote.objects.get(discussion=discussion, user=request.user)

            # Aynı oy ise iptal et
            if existing_vote.vote_type == vote_type:
                # Oy sayacını güncelle
                if vote_type == 'UP':
                    discussion.upvotes -= 1
                else:
                    discussion.downvotes -= 1
                existing_vote.delete()
                messages.success(request, 'Oyunuz iptal edildi.')
            else:
                # Farklı oy ise değiştir
                if existing_vote.vote_type == 'UP':
                    discussion.upvotes -= 1
                    discussion.downvotes += 1
                else:
                    discussion.downvotes -= 1
                    discussion.upvotes += 1

                existing_vote.vote_type = vote_type
                existing_vote.save()
                messages.success(request, 'Oyunuz güncellendi.')

        except DiscussionVote.DoesNotExist:
            # Yeni oy
            DiscussionVote.objects.create(
                discussion=discussion,
                user=request.user,
                vote_type=vote_type
            )

            if vote_type == 'UP':
                discussion.upvotes += 1
            else:
                discussion.downvotes += 1

            messages.success(request, 'Oyunuz kaydedildi.')

        discussion.save()

    # Explicit redirect - proposal veya article'a geri dön
    if discussion.proposal:
        return redirect('doctrine:proposal_detail', proposal_id=discussion.proposal.id)
    elif discussion.article:
        return redirect('doctrine:article_detail', article_id=discussion.article.id)
    else:
        return redirect('doctrine:doctrine_list')


@login_required
@rate_limit(limit=20, period=60, message="Çok fazla yorum gönderiyorsunuz. Lütfen bir dakika bekleyin.")
def article_detail(request, article_id):
    """Madde detay ve yorumlar"""
    article = get_object_or_404(DoctrineArticle.objects.prefetch_related('tags', 'versions'), id=article_id)

    # Gerekçe bölümü için:
    # - Kuruluş ilkeleri: article.justification (sadece kurucu düzenleyebilir)
    # - Normal yasalar: Bu maddeyi oluşturan PASSED proposal'ın justification'ı
    justification_text = None
    can_edit_justification = False

    if article.article_type == 'FOUNDATION_LAW':
        justification_text = article.justification
        # Sadece kurucu düzenleyebilir (is_founder kontrolü)
        can_edit_justification = hasattr(request.user, 'is_founder') and request.user.is_founder
    else:
        # Normal yasa için: Maddenin kendi justification alanını kullan
        justification_text = article.justification

    # Gerekçe düzenleme
    if request.method == 'POST' and 'justification' in request.POST and can_edit_justification:
        new_justification = request.POST.get('justification', '').strip()
        article.justification = new_justification
        article.save()
        messages.success(request, 'Gerekçe güncellendi!')
        return redirect('doctrine:article_detail', article_id=article_id)

    # Yorum ekleme
    if request.method == 'POST' and 'comment' in request.POST:
        comment_text = request.POST.get('comment', '').strip()
        parent_id = request.POST.get('parent_comment_id')

        if comment_text:
            new_comment = Discussion.objects.create(
                article=article,
                proposal=None,
                user=request.user,
                comment_text=comment_text,
                parent_comment_id=parent_id if parent_id else None
            )

            # Eğer yanıt ise bildirim gönder
            if parent_id:
                try:
                    parent_comment = Discussion.objects.get(id=parent_id)
                    if parent_comment.user != request.user:  # Kendine yanıt vermediyse
                        notify_comment_reply(new_comment, parent_comment)
                except Discussion.DoesNotExist:
                    pass

            messages.success(request, 'Yorumunuz eklendi!')
            return redirect('doctrine:article_detail', article_id=article_id)

    # Pagination için tüm yorumları al (en çok upvote alanlar üstte)
    all_discussions = article.discussions.filter(parent_comment__isnull=True).select_related('user').order_by('-upvotes', '-created_at')

    # Pagination: 30 yorum per sayfa
    paginator = Paginator(all_discussions, 30)
    page_number = request.GET.get('page', 1)
    discussions = paginator.get_page(page_number)

    # Versiyon geçmişini al ve ara
    version_search = request.GET.get('version_search', '').strip()
    all_versions = article.versions.all().select_related('changed_by_proposal')

    if version_search:
        all_versions = all_versions.filter(
            Q(content__icontains=version_search) |
            Q(justification__icontains=version_search)
        )

    versions = all_versions[:20]  # Son 20 versiyon

    context = {
        'article': article,
        'discussions': discussions,
        'justification_text': justification_text,
        'can_edit_justification': can_edit_justification,
        'versions': versions,
        'version_search': version_search,
    }
    return render(request, 'doctrine/article_detail.html', context)


@login_required
def activity_feed(request):
    """Global aktivite akışı"""
    all_activities = Activity.objects.select_related("user").all()

    # Pagination: 30 aktivite per sayfa
    paginator = Paginator(all_activities, 30)
    page_number = request.GET.get("page", 1)
    activities = paginator.get_page(page_number)

    return render(request, "doctrine/activity_feed.html", {
        "activities": activities
    })

@login_required
def statistics_dashboard(request):
    """İstatistik Dashboard - Sadece admin/kurucu için"""
    # Yetki kontrolü - sadece kurucu veya superuser
    if not (hasattr(request.user, 'is_founder') and request.user.is_founder) and not request.user.is_superuser:
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok.')
        return redirect('doctrine:doctrine_list')
    
    from django.db.models import Count, Q
    from users.models import User
    from datetime import timedelta
    from django.utils import timezone
    
    # Genel İstatistikler
    total_articles = DoctrineArticle.objects.filter(is_active=True).count()
    foundation_laws_count = DoctrineArticle.objects.filter(article_type='FOUNDATION_LAW', is_active=True).count()
    normal_laws_count = DoctrineArticle.objects.filter(article_type='NORMAL_LAW', is_active=True).count()
    
    total_proposals = Proposal.objects.count()
    active_proposals = Proposal.objects.filter(status='ACTIVE').count()
    passed_proposals = Proposal.objects.filter(status='PASSED').count()
    rejected_proposals = Proposal.objects.filter(status='REJECTED').count()
    
    total_users = User.objects.filter(is_active=True).count()
    total_votes = Vote.objects.count()
    total_discussions = Discussion.objects.count()
    
    # En çok oy alan öneriler (son 30 gün)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    top_proposals = Proposal.objects.filter(
        start_date__gte=thirty_days_ago
    ).annotate(
        total_votes=Count('votes')
    ).order_by('-total_votes')[:5]
    
    # En aktif kullanıcılar (oy + yorum sayısı)
    top_users = User.objects.filter(is_active=True).annotate(
        vote_count=Count('votes'),
        discussion_count=Count('discussions')
    ).order_by('-vote_count', '-discussion_count')[:10]
    
    # Oy dağılımı
    yes_votes = Vote.objects.filter(vote_choice='YES').count()
    abstain_votes = Vote.objects.filter(vote_choice='ABSTAIN').count()
    veto_votes = Vote.objects.filter(vote_choice='VETO').count()
    
    # Son aktiviteler
    recent_activities = Activity.objects.all()[:20]
    
    context = {
        'total_articles': total_articles,
        'foundation_laws_count': foundation_laws_count,
        'normal_laws_count': normal_laws_count,
        'total_proposals': total_proposals,
        'active_proposals': active_proposals,
        'passed_proposals': passed_proposals,
        'rejected_proposals': rejected_proposals,
        'total_users': total_users,
        'total_votes': total_votes,
        'total_discussions': total_discussions,
        'top_proposals': top_proposals,
        'top_users': top_users,
        'yes_votes': yes_votes,
        'abstain_votes': abstain_votes,
        'veto_votes': veto_votes,
        'recent_activities': recent_activities,
    }
    
    return render(request, 'doctrine/statistics_dashboard.html', context)

def leaderboard(request):
    """En aktif üyeler ve liderler tablosu"""
    from users.models import User
    from django.db.models import Count, Q
    
    # En aktif kullanıcılar (oy + yorum)
    top_contributors = User.objects.filter(is_active=True).annotate(
        vote_count=Count('votes'),
        comment_count=Count('discussions')
    ).order_by('-vote_count', '-comment_count')[:50]
    
    # Liderler
    team_leaders = User.objects.filter(
        is_active=True,
        led_team__isnull=False
    ).distinct().annotate(
        vote_count=Count('votes'),
        comment_count=Count('discussions')
    ).order_by('-vote_count')[:20]
    
    squad_leaders = User.objects.filter(
        is_active=True,
        led_squad__isnull=False
    ).distinct().annotate(
        vote_count=Count('votes')
    ).order_by('-vote_count')[:15]
    
    union_leaders = User.objects.filter(
        is_active=True,
        led_union__isnull=False
    ).distinct().annotate(
        vote_count=Count('votes')
    ).order_by('-vote_count')[:10]
    
    context = {
        'top_contributors': top_contributors,
        'team_leaders': team_leaders,
        'squad_leaders': squad_leaders,
        'union_leaders': union_leaders,
    }
    
    return render(request, 'doctrine/leaderboard.html', context)


# ========================================
# EXPORT & BACKUP
# ========================================

@login_required
def export_doctrine_text(request):
    """Doktrin'i metin formatında export et"""
    from django.http import HttpResponse
    from datetime import datetime

    # Kuruluş ilkeleri
    foundation_laws = DoctrineArticle.objects.filter(
        article_type='FOUNDATION_LAW',
        is_active=True
    ).order_by('article_number')

    # Normal yasalar
    normal_laws = DoctrineArticle.objects.filter(
        article_type='NORMAL_LAW',
        is_active=True
    ).order_by('article_number')

    # Metin içeriği oluştur
    content = []
    content.append("=" * 80)
    content.append("DOKTRİN".center(80))
    content.append("=" * 80)
    content.append(f"\nOluşturulma Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")
    content.append("=" * 80)
    
    # Kuruluş İlkeleri
    content.append("\n\nKURULUŞ İLKELERİ")
    content.append("-" * 80)
    for article in foundation_laws:
        content.append(f"\nİLKE {article.article_number}")
        content.append("-" * 40)
        content.append(article.content)
        if article.justification:
            content.append(f"\nGerekçe: {article.justification}")
        content.append("")

    # Normal Yasalar
    content.append("\n\nYASALAR")
    content.append("-" * 80)
    for article in normal_laws:
        content.append(f"\nYASA {article.article_number}")
        content.append("-" * 40)
        content.append(article.content)
        if article.justification:
            content.append(f"\nGerekçe: {article.justification}")
        # Etiketler
        if article.tags.exists():
            tags = ", ".join([tag.name for tag in article.tags.all()])
            content.append(f"\nEtiketler: {tags}")
        content.append("")

    content.append("\n" + "=" * 80)
    content.append(f"Toplam: {foundation_laws.count()} Kuruluş İlkesi, {normal_laws.count()} Yasa")
    content.append("=" * 80)

    # Response oluştur
    response = HttpResponse("\n".join(content), content_type='text/plain; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="doktrin_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt"'

    return response


@login_required
def save_proposal_draft(request):
    """Öneri taslağı kaydet (AJAX)"""
    import json
    from django.http import JsonResponse

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            draft_id = data.get('draft_id')
            proposal_type = data.get('proposal_type')
            related_article_id = data.get('related_article_id')
            proposed_content = data.get('proposed_content', '')
            justification = data.get('justification', '')
            proposed_tags = data.get('proposed_tags', '')
            draft_title = data.get('draft_title', '')

            if draft_id:
                # Mevcut taslağı güncelle
                draft = get_object_or_404(ProposalDraft, id=draft_id, user=request.user)
                draft.proposal_type = proposal_type
                draft.related_article_id = related_article_id
                draft.proposed_content = proposed_content
                draft.justification = justification
                draft.proposed_tags = proposed_tags
                draft.draft_title = draft_title
                draft.save()
                return JsonResponse({'success': True, 'draft_id': draft.id, 'message': 'Taslak güncellendi'})
            else:
                # Yeni taslak oluştur
                draft = ProposalDraft.objects.create(
                    user=request.user,
                    proposal_type=proposal_type,
                    related_article_id=related_article_id,
                    proposed_content=proposed_content,
                    justification=justification,
                    proposed_tags=proposed_tags,
                    draft_title=draft_title
                )
                return JsonResponse({'success': True, 'draft_id': draft.id, 'message': 'Taslak kaydedildi'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


@login_required
def load_proposal_draft(request, draft_id):
    """Taslağı yükle ve öneri formuna doldur"""
    draft = get_object_or_404(ProposalDraft, id=draft_id, user=request.user)

    # Öneri türüne göre doğru forma yönlendir
    if draft.proposal_type == 'NEW_ARTICLE':
        return redirect(f'/doctrine/propose/new/?draft_id={draft.id}')
    elif draft.proposal_type == 'AMEND_ARTICLE' and draft.related_article:
        return redirect(f'/doctrine/article/{draft.related_article.id}/propose/modify/?draft_id={draft.id}')
    elif draft.proposal_type == 'REPEAL_ARTICLE' and draft.related_article:
        return redirect(f'/doctrine/article/{draft.related_article.id}/propose/remove/?draft_id={draft.id}')
    elif draft.proposal_type == 'RENAME_ARTICLE' and draft.related_article:
        return redirect(f'/doctrine/article/{draft.related_article.id}/propose/rename/?draft_id={draft.id}')
    else:
        messages.error(request, 'Taslak yüklenemedi')
        return redirect('doctrine:my_drafts')


@login_required
def my_drafts(request):
    """Kullanıcının taslakları"""
    drafts = ProposalDraft.objects.filter(user=request.user).select_related('related_article')

    return render(request, 'doctrine/my_drafts.html', {
        'drafts': drafts
    })


@login_required
def delete_draft(request, draft_id):
    """Taslak sil"""
    draft = get_object_or_404(ProposalDraft, id=draft_id, user=request.user)
    draft.delete()
    messages.success(request, 'Taslak silindi')
    return redirect('doctrine:my_drafts')

# ========================================
# REFERENCE API ENDPOINTS
# ========================================

@login_required
def reference_create(request):
    """Yeni kaynak oluştur (AJAX)"""
    import json
    from django.http import JsonResponse
    from .models import Reference
    
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            
            reference = Reference.objects.create(
                created_by=request.user,
                reference_type=data.get("reference_type", "BOOK"),
                author=data["author"],
                title=data["title"],
                year=int(data["year"]),
                publisher=data.get("publisher", ""),
                city=data.get("city", ""),
                url=data.get("url", ""),
                notes=data.get("notes", "")
            )
            
            return JsonResponse({
                "success": True,
                "reference": {
                    "id": reference.id,
                    "author": reference.author,
                    "title": reference.title,
                    "year": reference.year,
                    "publisher": reference.publisher,
                    "url": reference.url,
                    "page_number": data.get("page_number", "")
                }
            })
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)
    
    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)


@login_required
def reference_list(request):
    """Tüm kaynakları listele (AJAX)"""
    from django.http import JsonResponse
    from .models import Reference
    
    references = Reference.objects.all().order_by("-created_at")[:100]
    
    data = {
        "references": [
            {
                "id": ref.id,
                "author": ref.author,
                "title": ref.title,
                "year": ref.year,
                "reference_type": ref.get_reference_type_display(),
                "publisher": ref.publisher,
                "url": ref.url,
                "created_by": ref.created_by.username,
            }
            for ref in references
        ]
    }
    
    return JsonResponse(data)


@login_required
def my_references(request):
    """Kullanıcının kendi kaynakları (AJAX)"""
    from django.http import JsonResponse
    from .models import Reference
    
    references = Reference.objects.filter(created_by=request.user).order_by("-created_at")
    
    data = {
        "references": [
            {
                "id": ref.id,
                "author": ref.author,
                "title": ref.title,
                "year": ref.year,
                "reference_type": ref.get_reference_type_display(),
                "publisher": ref.publisher,
                "url": ref.url,
            }
            for ref in references
        ]
    }
    
    return JsonResponse(data)



@login_required
def references_list(request):
    """Tüm kaynakları listele - Global kaynaklar sayfası"""
    from django.http import JsonResponse
    from .models import Reference, ProposalReference, ArticleReference
    from django.db.models import Count, Q
    
    references = Reference.objects.annotate(
        usage_count=Count('proposal_usages', distinct=True) + Count('article_usages', distinct=True)
    ).order_by('-created_at')
    
    return render(request, 'doctrine/references_list.html', {
        'references': references
    })


@login_required
def reference_usage(request, ref_id):
    """Kaynağın kullanım yerlerini döndür (AJAX)"""
    from django.http import JsonResponse
    from .models import Reference, ProposalReference, ArticleReference
    
    try:
        reference = Reference.objects.get(id=ref_id)
        
        # Proposal kullanımları
        proposal_usages = ProposalReference.objects.filter(reference=reference).select_related('proposal')
        proposals = [
            {
                'id': pu.proposal.id,
                'proposal_type': pu.proposal.get_proposal_type_display(),
                'proposed_by_level': pu.proposal.get_proposed_by_level_display(),
            }
            for pu in proposal_usages
        ]
        
        # Article kullanımları
        article_usages = ArticleReference.objects.filter(reference=reference).select_related('article')
        articles = [
            {
                'id': au.article.id,
                'article_number': au.article.article_number,
                'article_type': au.article.get_article_type_display(),
            }
            for au in article_usages
        ]
        
        return JsonResponse({
            'success': True,
            'usage_count': len(proposals) + len(articles),
            'proposals': proposals,
            'articles': articles
        })
        
    except Reference.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Kaynak bulunamadı'}, status=404)
