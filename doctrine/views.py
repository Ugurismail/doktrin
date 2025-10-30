from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth import get_user_model
from .models import DoctrineArticle, Proposal, Vote, Discussion, DiscussionVote, Activity, ArticleTag, ProposalDraft, Reference, ProposalReference, ArticleReference
from .vote_calculator import calculate_votes_with_multipliers
from notifications.utils import notify_comment_reply
from notifications.models import Notification
from config.rate_limit import rate_limit
import json
import re
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


def doctrine_list(request):
    """Bizlik listesi"""
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

    # Tag filtresi (ilişkili article'a göre)
    if tag_filter:
        active_proposals = active_proposals.filter(related_article__tags__slug=tag_filter)

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

    active_proposals = active_proposals.order_by('-start_date').distinct()
    show_all_proposals = request.GET.get('show_all') == 'true'

    # Arşiv önerileri (pagination)
    archived_all = Proposal.objects.filter(
        status__in=['PASSED', 'REJECTED', 'ARCHIVED']
    )

    # Tag filtresi (ilişkili article'a göre)
    if tag_filter:
        archived_all = archived_all.filter(related_article__tags__slug=tag_filter)

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

    archived_all = archived_all.order_by('-end_date').distinct()

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
        'tag_filter': tag_filter,  # Template için ekle
        'date_from': date_from,
        'date_to': date_to,
        'created_by': created_by,
        'proposal_type_filter': proposal_type_filter,
        'proposal_status_filter': proposal_status_filter,
    }
    return render(request, 'doctrine/doctrine_list.html', context)



@login_required
@rate_limit(limit=20, period=60, methods=['POST'], message="Çok fazla yorum gönderiyorsunuz. Lütfen bir dakika bekleyin.")
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
    effective_vote = None
    vote_source = None  # 'own', 'delegate', 'leader'

    try:
        user_vote = Vote.objects.get(proposal=proposal, user=request.user)
        effective_vote = user_vote
        vote_source = 'own'
    except Vote.DoesNotExist:
        # Kendi oyu yok, etkili oyu bul
        effective_vote = request.user.get_effective_vote_for(proposal)
        if effective_vote:
            if request.user.vote_delegate and effective_vote.user == request.user.vote_delegate:
                vote_source = 'delegate'
            else:
                vote_source = 'leader'

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

            # @mention tespiti ve bildirim
            # @username pattern'i bul
            mentions = re.findall(r'@(\w+)', comment_text)

            if mentions:
                # Tekrar edenleri kaldır
                unique_mentions = set(mentions)

                for username in unique_mentions:
                    # Kendine mention yapmadıysa ve kullanıcı varsa
                    if username.lower() != request.user.username.lower():
                        try:
                            mentioned_user = User.objects.get(username__iexact=username)

                            # Bildirim gönder
                            Notification.objects.create(
                                user=mentioned_user,
                                notification_type='MENTION',
                                message=f'{request.user.username} sizi bir tartışmada etiketledi: "{comment_text[:80]}..."',
                                related_object_id=proposal.id if proposal else None
                            )
                        except User.DoesNotExist:
                            pass  # Kullanıcı bulunamadı, geç

            messages.success(request, 'Yorumunuz eklendi!')
            return redirect('doctrine:proposal_detail', proposal_id=proposal_id)

    # Öneriyle ilişkili kaynakları al
    proposal_references = ProposalReference.objects.filter(proposal=proposal).select_related('reference')

    # Oy dağılımı breakdown'unu al
    from .vote_calculator import get_vote_breakdown
    vote_breakdown = get_vote_breakdown(proposal)

    context = {
        'proposal': proposal,
        'discussions': discussions,
        'user_vote': user_vote,
        'effective_vote': effective_vote,
        'vote_source': vote_source,
        'proposal_references': proposal_references,
        'vote_breakdown': vote_breakdown,
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

            # Oy değiştirme kontrolü (öneri aktif mi?)
            if not existing_vote.can_change_vote():
                messages.error(request, 'Oylama süresi dolduğu için oyunuzu değiştiremezsiniz!')
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
            logger.error(f"Çarpan hesaplama hatası (Proposal {proposal.id}): {e}", exc_info=True)
            # Hata olursa basit sayıma geç
            proposal.vote_yes_count = proposal.votes.filter(vote_choice='YES').count()
            proposal.vote_abstain_count = proposal.votes.filter(vote_choice='ABSTAIN').count()
            proposal.vote_veto_count = proposal.votes.filter(vote_choice='VETO').count()

        proposal.save()  # ÖNEMLİ: Her durumda kaydet
        messages.success(request, 'Oyunuz kaydedildi!')
        return redirect('doctrine:proposal_detail', proposal_id=proposal_id)

    return redirect('doctrine:proposal_detail', proposal_id=proposal_id)

@login_required
@rate_limit(limit=50, period=300, message="Çok fazla öneri oluşturuyorsunuz. Lütfen 5 dakika bekleyin.")
def create_proposal(request):
    """Öneri oluştur - Yetki: Sadece Ekip Liderleri"""
    user_team = request.user.current_team

    # Kurucu kontrolü (en başta)
    is_founder = hasattr(request.user, 'is_founder') and request.user.is_founder

    if not user_team and not is_founder:
        messages.error(request, 'Öneri oluşturmak için bir ekibe dahil olmalısınız.')
        return redirect('doctrine:doctrine_list')

    # Ekip lideri kontrolü (kurucu hariç)
    if not is_founder and user_team and user_team.leader != request.user:
        messages.error(request, 'Öneri oluşturma yetkisi sadece ekip liderlerine aittir.')
        return redirect('doctrine:doctrine_list')

    # Kullanıcının seviyesini belirle
    user_level = None
    if is_founder:
        user_level = 'FOUNDER'
    elif user_team and user_team.parent_squad:
        # Birlik lideri mi kontrol et
        if user_team.parent_squad.parent_union and user_team.parent_squad.parent_union.leader == request.user:
            user_level = 'UNION'
        # Takım lideri mi kontrol et
        elif user_team.parent_squad.leader == request.user:
            user_level = 'SQUAD'
        else:
            # Birlik veya takıma üye ama lider değil
            messages.error(request, 'Öneri oluşturma yetkisi sadece ekip liderlerine aittir.')
            return redirect('doctrine:doctrine_list')
    elif user_team:
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
        proposed_article_type = request.POST.get('proposed_article_type', 'NORMAL_LAW')
        selected_tags = request.POST.getlist('tags')  # Seçilen etiketler

        # İlke ekleme yetkisi kontrolü
        if proposal_type == 'ADD' and proposed_article_type == 'FOUNDATION_LAW':
            if user_level not in ['FOUNDER', 'UNION']:
                messages.error(request, 'Kuruluş İlkesi ekleyebilmek için Kurucu veya Birlik lideri olmalısınız!')
                return redirect('doctrine:create_proposal')

        # Eski madde içeriğini kaydet (MODIFY ve REMOVE için)
        original_content = None
        if related_article_id and proposal_type in ['MODIFY', 'REMOVE']:
            article = DoctrineArticle.objects.get(id=related_article_id)
            original_content = article.content

            # Aktif öneri kontrolü
            active_proposals = Proposal.objects.filter(
                related_article_id=related_article_id,
                status='ACTIVE',
                proposal_type__in=['MODIFY', 'REMOVE']
            )

            if active_proposals.exists():
                existing_proposal = active_proposals.first()
                messages.warning(
                    request,
                    f'Bu maddeyle ilgili zaten aktif bir değişim önerisi var! '
                    f'Yeni öneri açmak yerine, mevcut öneriye yorum yapabilirsiniz. '
                    f'<a href="/doctrine/proposal/{existing_proposal.id}/">Mevcut öneriyi görüntüle</a>'
                )
                return redirect('doctrine:create_proposal')

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
            proposed_article_type=proposed_article_type,
            proposed_by_level=user_level,
            proposed_by_entity_id=entity_id,
            created_by=request.user  # Kullanıcıyı kaydet
        )

        # Eğer yeni madde önerisi ise ve etiketler seçildiyse, proposal'a not ekle
        if proposal_type == 'ADD' and selected_tags:
            proposal.proposed_tags = ','.join(selected_tags)  # Etiket ID'lerini virgülle ayırarak sakla
            proposal.save()

        # Kaynakları kaydet
        selected_references_json = request.POST.get('selected_references', '[]')
        try:
            selected_references = json.loads(selected_references_json)
            for ref_data in selected_references:
                ref_id = ref_data.get('id')
                page_number = ref_data.get('page_number', '')
                if ref_id:
                    try:
                        reference = Reference.objects.get(id=ref_id)
                        ProposalReference.objects.create(
                            proposal=proposal,
                            reference=reference,
                            page_number=page_number
                        )
                    except Reference.DoesNotExist:
                        pass  # Kaynak bulunamadı, devam et
        except json.JSONDecodeError:
            pass  # JSON parse hatası, devam et

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

        # E-posta bildirimi gönder (arka planda)
        import threading
        from users.emails import send_new_proposal_email

        def send_emails_in_background():
            for user in target_users:
                try:
                    send_new_proposal_email(user, proposal)
                except Exception as e:
                    logger.error(f"E-posta gönderme hatası (User {user.id}, Proposal {proposal.id}): {e}", exc_info=True)

        # E-posta gönderimini arka planda başlat
        email_thread = threading.Thread(target=send_emails_in_background)
        email_thread.daemon = True
        email_thread.start()

        # Aktivite oluştur
        Activity.objects.create(
            activity_type='proposal_created',
            user=request.user,
            description=f'{proposal.get_proposal_type_display()} önerisi oluşturdu',
            related_url=f'/doctrine/proposal/{proposal.id}/'
        )

        # Eğer taslaktan oluşturulduysa taslağı sil
        draft_id_from_post = request.GET.get('draft_id')
        if draft_id_from_post:
            try:
                draft_to_delete = ProposalDraft.objects.get(id=draft_id_from_post, user=request.user)
                draft_to_delete.delete()
            except ProposalDraft.DoesNotExist:
                pass

        messages.success(request, 'Öneriniz oluşturuldu ve oylamaya açıldı!')
        return redirect('doctrine:proposal_detail', proposal_id=proposal.id)
    
    # Taslak yükleme - draft_id varsa taslağı al
    draft = None
    draft_id = request.GET.get('draft_id')
    if draft_id:
        try:
            draft = ProposalDraft.objects.get(id=draft_id, user=request.user)
        except ProposalDraft.DoesNotExist:
            messages.error(request, 'Taslak bulunamadı')

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
        'draft': draft,  # Taslağı context'e ekle
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

    if request.method != 'POST':
        # GET request - hata, sadece POST kabul edilir
        messages.error(request, 'Geçersiz istek.')
        if discussion.proposal:
            return redirect('doctrine:proposal_detail', proposal_id=discussion.proposal.id)
        elif discussion.article:
            return redirect('doctrine:article_detail', article_id=discussion.article.id)
        else:
            return redirect('doctrine:doctrine_list')

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
@rate_limit(limit=20, period=60, methods=['POST'], message="Çok fazla yorum gönderiyorsunuz. Lütfen bir dakika bekleyin.")
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

            # @mention tespiti ve bildirim
            # @username pattern'i bul
            mentions = re.findall(r'@(\w+)', comment_text)

            if mentions:
                # Tekrar edenleri kaldır
                unique_mentions = set(mentions)

                for username in unique_mentions:
                    # Kendine mention yapmadıysa ve kullanıcı varsa
                    if username.lower() != request.user.username.lower():
                        try:
                            mentioned_user = User.objects.get(username__iexact=username)

                            # Bildirim gönder
                            Notification.objects.create(
                                user=mentioned_user,
                                notification_type='MENTION',
                                message=f'{request.user.username} sizi bir tartışmada etiketledi: "{comment_text[:80]}..."',
                                related_object_id=article.id
                            )
                        except User.DoesNotExist:
                            pass  # Kullanıcı bulunamadı, geç

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
    """Bizlik'i metin formatında export et"""
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
        return redirect(f'/doctrine/proposal/create/?draft_id={draft.id}')
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
    from django.core.paginator import Paginator
    from .models import Reference, ProposalReference, ArticleReference
    from django.db.models import Count, Q

    # Arama parametresi
    search_query = request.GET.get('search', '').strip()

    all_references = Reference.objects.annotate(
        usage_count=Count('proposal_usages', distinct=True) + Count('article_usages', distinct=True)
    )

    # Arama varsa filtrele
    if search_query:
        all_references = all_references.filter(
            Q(author__icontains=search_query) |
            Q(title__icontains=search_query) |
            Q(publisher__icontains=search_query)
        )

    all_references = all_references.order_by('-created_at')

    # Sayfalama: 15 kaynak per sayfa
    paginator = Paginator(all_references, 15)
    page_number = request.GET.get('page', 1)
    references = paginator.get_page(page_number)

    return render(request, 'doctrine/references_list.html', {
        'references': references,
        'search_query': search_query,
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


def reference_detail(request, ref_id):
    """Tek bir kaynağın detaylarını döndür (AJAX)"""
    from django.http import JsonResponse
    from .models import Reference

    try:
        reference = Reference.objects.get(id=ref_id)

        return JsonResponse({
            'success': True,
            'reference': {
                'id': reference.id,
                'reference_type': reference.reference_type,
                'author': reference.author,
                'title': reference.title,
                'year': reference.year,
                'publisher': reference.publisher or '',
                'city': reference.city or '',
                'url': reference.url or '',
                'notes': reference.notes or '',
            }
        })

    except Reference.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Kaynak bulunamadı'}, status=404)


def reference_update(request, ref_id):
    """Kaynağı güncelle (AJAX POST)"""
    from django.http import JsonResponse
    from .models import Reference
    import json

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Sadece POST istekleri kabul edilir'}, status=405)

    try:
        reference = Reference.objects.get(id=ref_id)

        # JSON verisini parse et
        data = json.loads(request.body)

        # Kaynağı güncelle
        reference.reference_type = data.get('reference_type', reference.reference_type)
        reference.author = data.get('author', reference.author)
        reference.title = data.get('title', reference.title)
        reference.year = data.get('year', reference.year)
        reference.publisher = data.get('publisher', '')
        reference.city = data.get('city', '')
        reference.url = data.get('url', '')
        reference.notes = data.get('notes', '')

        reference.save()

        return JsonResponse({
            'success': True,
            'message': 'Kaynak başarıyla güncellendi',
            'reference': {
                'id': reference.id,
                'author': reference.author,
                'title': reference.title,
                'year': reference.year,
            }
        })

    except Reference.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Kaynak bulunamadı'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def get_mention_suggestions(request):
    """@mention için kullanıcı önerileri (autocomplete)"""
    from django.http import JsonResponse

    query = request.GET.get('q', '').strip()

    if len(query) < 1:
        return JsonResponse({'suggestions': []})

    # Önce ekip üyeleri, sonra tüm kullanıcılar
    suggestions = []

    # Ekip üyeleri (öncelikli)
    if request.user.current_team:
        team_members = User.objects.filter(
            current_team=request.user.current_team
        ).filter(
            username__istartswith=query
        ).exclude(
            id=request.user.id
        ).values('username', 'id')[:5]

        for member in team_members:
            suggestions.append({
                'username': member['username'],
                'id': member['id'],
                'type': 'team'
            })

    # Diğer kullanıcılar (eğer yeterli sonuç yoksa)
    if len(suggestions) < 5:
        other_users = User.objects.filter(
            username__istartswith=query
        ).exclude(
            id=request.user.id
        ).exclude(
            id__in=[s['id'] for s in suggestions]
        ).values('username', 'id')[:5 - len(suggestions)]

        for user in other_users:
            suggestions.append({
                'username': user['username'],
                'id': user['id'],
                'type': 'other'
            })

    return JsonResponse({'suggestions': suggestions})
