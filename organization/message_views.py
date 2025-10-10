from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from notifications.models import LeaderMessage, Notification
from users.models import User
from .models import Team, Squad, Union, ProvinceOrganization


def is_leader(user):
    """Kullanıcının herhangi bir seviyede lider olup olmadığını kontrol et"""
    if not user.current_team:
        return False

    team = user.current_team

    # Ekip lideri mi?
    if team.leader == user:
        return True

    # Takım lideri mi?
    if team.parent_squad and team.parent_squad.leader == user:
        return True

    # Birlik lideri mi?
    if team.parent_squad and team.parent_squad.parent_union:
        if team.parent_squad.parent_union.leader == user:
            return True

    # İl örgütü lideri mi?
    if (team.parent_squad and team.parent_squad.parent_union and
        team.parent_squad.parent_union.parent_province_org):
        if team.parent_squad.parent_union.parent_province_org.leader == user:
            return True

    return False


def get_available_recipients(user):
    """Kullanıcının mesaj gönderebileceği liderleri getir (yatay ve dikey)"""
    if not user.current_team:
        return []

    team = user.current_team
    recipients = set()

    # Kullanıcının lider olduğu seviyeyi belirle
    is_team_leader = team.leader == user
    is_squad_leader = team.parent_squad and team.parent_squad.leader == user
    is_union_leader = (team.parent_squad and team.parent_squad.parent_union and
                       team.parent_squad.parent_union.leader == user)
    is_province_leader = (team.parent_squad and team.parent_squad.parent_union and
                          team.parent_squad.parent_union.parent_province_org and
                          team.parent_squad.parent_union.parent_province_org.leader == user)

    # Ekip lideri ise
    if is_team_leader:
        # Aynı takımdaki diğer ekip liderleri (yatay)
        if team.parent_squad:
            squad_teams = Team.objects.filter(parent_squad=team.parent_squad, is_active=True).exclude(id=team.id)
            for t in squad_teams:
                if t.leader:
                    recipients.add(t.leader)

            # Takım lideri (dikey - yukarı)
            if team.parent_squad.leader:
                recipients.add(team.parent_squad.leader)

    # Takım lideri ise
    if is_squad_leader:
        squad = team.parent_squad

        # Aynı takımdaki ekip liderleri (dikey - aşağı)
        squad_teams = Team.objects.filter(parent_squad=squad, is_active=True)
        for t in squad_teams:
            if t.leader and t.leader != user:
                recipients.add(t.leader)

        # Aynı birlikteki diğer takım liderleri (yatay)
        if squad.parent_union:
            union_squads = Squad.objects.filter(parent_union=squad.parent_union, is_active=True).exclude(id=squad.id)
            for s in union_squads:
                if s.leader:
                    recipients.add(s.leader)

            # Birlik lideri (dikey - yukarı)
            if squad.parent_union.leader:
                recipients.add(squad.parent_union.leader)

    # Birlik lideri ise
    if is_union_leader:
        union = team.parent_squad.parent_union

        # Aynı birlikteki takım liderleri (dikey - aşağı)
        union_squads = Squad.objects.filter(parent_union=union, is_active=True)
        for s in union_squads:
            if s.leader and s.leader != user:
                recipients.add(s.leader)

        # Aynı il örgütündeki diğer birlik liderleri (yatay)
        if union.parent_province_org:
            province_unions = Union.objects.filter(
                parent_province_org=union.parent_province_org,
                is_active=True
            ).exclude(id=union.id)
            for u in province_unions:
                if u.leader:
                    recipients.add(u.leader)

            # İl örgütü lideri (dikey - yukarı)
            if union.parent_province_org.leader:
                recipients.add(union.parent_province_org.leader)

    # İl örgütü lideri ise
    if is_province_leader:
        province_org = team.parent_squad.parent_union.parent_province_org

        # Aynı il örgütündeki birlik liderleri (dikey - aşağı)
        province_unions = Union.objects.filter(parent_province_org=province_org, is_active=True)
        for u in province_unions:
            if u.leader and u.leader != user:
                recipients.add(u.leader)

    return list(recipients)


@login_required
def message_inbox(request):
    """Gelen kutusu - conversation bazlı"""
    if not is_leader(request.user):
        messages.error(request, 'Mesajlaşma sistemi sadece liderler içindir.')
        return redirect('organization:my_team')

    # Tüm mesajları al (gelen + giden)
    all_messages = LeaderMessage.objects.filter(
        Q(recipient=request.user) | Q(sender=request.user)
    ).select_related('sender', 'recipient').order_by('-created_at')

    # Kişilere göre grupla
    conversations = {}
    for msg in all_messages:
        other_person = msg.sender if msg.recipient == request.user else msg.recipient

        if other_person.id not in conversations:
            # Bu kişiyle son mesaj
            conversations[other_person.id] = {
                'other_person': other_person,
                'last_message': msg,
                'unread_count': 0,
            }

        # Okunmamış sayısını güncelle (sadece gelen mesajlar)
        if msg.recipient == request.user and not msg.is_read:
            conversations[other_person.id]['unread_count'] += 1

    # Liste haline getir ve tarihe göre sırala
    conversation_list = sorted(
        conversations.values(),
        key=lambda x: x['last_message'].created_at,
        reverse=True
    )

    total_unread = sum(c['unread_count'] for c in conversation_list)

    context = {
        'conversations': conversation_list,
        'unread_count': total_unread,
        'active_tab': 'inbox',
    }
    return render(request, 'organization/messages/inbox.html', context)


@login_required
def message_sent(request):
    """Gönderilen kutusu"""
    if not is_leader(request.user):
        messages.error(request, 'Mesajlaşma sistemi sadece liderler içindir.')
        return redirect('organization:my_team')

    sent_messages = LeaderMessage.objects.filter(sender=request.user)

    context = {
        'messages': sent_messages,
        'active_tab': 'sent',
    }
    return render(request, 'organization/messages/sent.html', context)


@login_required
def message_compose(request):
    """Mesaj oluştur"""
    if not is_leader(request.user):
        messages.error(request, 'Mesajlaşma sistemi sadece liderler içindir.')
        return redirect('organization:my_team')

    available_recipients = get_available_recipients(request.user)

    # Yanıtlanan mesajı kontrol et
    reply_to_id = request.GET.get('reply_to')
    reply_to_message = None
    preselected_recipient = None
    preselected_subject = None

    if reply_to_id:
        try:
            reply_to_message = LeaderMessage.objects.get(id=reply_to_id, recipient=request.user)
            preselected_recipient = reply_to_message.sender
            # Re: ekle (eğer yoksa)
            if not reply_to_message.subject.startswith('Re: '):
                preselected_subject = f'Re: {reply_to_message.subject}'
            else:
                preselected_subject = reply_to_message.subject
        except LeaderMessage.DoesNotExist:
            pass

    if request.method == 'POST':
        recipient_id = request.POST.get('recipient_id')
        subject = request.POST.get('subject')
        content = request.POST.get('content')

        if not recipient_id or not subject or not content:
            messages.error(request, 'Tüm alanları doldurun.')
        else:
            recipient = get_object_or_404(User, id=recipient_id)

            # Alıcının available_recipients listesinde olup olmadığını kontrol et
            if recipient not in available_recipients:
                messages.error(request, 'Bu kullanıcıya mesaj gönderemezsiniz.')
            else:
                # Mesajı oluştur
                message = LeaderMessage.objects.create(
                    sender=request.user,
                    recipient=recipient,
                    subject=subject,
                    content=content
                )

                messages.success(request, 'Mesajınız gönderildi.')
                return redirect('organization:message_sent')

    context = {
        'available_recipients': available_recipients,
        'active_tab': 'compose',
        'reply_to_message': reply_to_message,
        'preselected_recipient': preselected_recipient,
        'preselected_subject': preselected_subject,
    }
    return render(request, 'organization/messages/compose.html', context)


@login_required
def message_detail(request, message_id):
    """Mesaj detayı ve inline yanıt"""
    if not is_leader(request.user):
        messages.error(request, 'Mesajlaşma sistemi sadece liderler içindir.')
        return redirect('organization:my_team')

    message = get_object_or_404(LeaderMessage, id=message_id)

    # Kullanıcı bu mesajın alıcısı veya göndericisi mi?
    if message.sender != request.user and message.recipient != request.user:
        messages.error(request, 'Bu mesajı görüntüleme yetkiniz yok.')
        return redirect('organization:message_inbox')

    # Karşılıklı mesajlaşma geçmişini al (thread)
    other_person = message.recipient if message.sender == request.user else message.sender

    # POST: Yeni mesaj gönder
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            # Son mesajın konusunu kullan (Re: ekle)
            last_msg = LeaderMessage.objects.filter(
                Q(sender=request.user, recipient=other_person) |
                Q(sender=other_person, recipient=request.user)
            ).order_by('-created_at').first()

            subject = last_msg.subject if last_msg else 'Mesaj'
            if not subject.startswith('Re: '):
                subject = f'Re: {subject}'

            # Yeni mesaj oluştur
            new_message = LeaderMessage.objects.create(
                sender=request.user,
                recipient=other_person,
                subject=subject,
                content=content
            )

            messages.success(request, 'Mesajınız gönderildi.')
            return redirect('organization:message_detail', message_id=new_message.id)

    # Bu conversation'daki tüm okunmamış mesajları okundu işaretle
    LeaderMessage.objects.filter(
        sender=other_person,
        recipient=request.user,
        is_read=False
    ).update(is_read=True)

    conversation = LeaderMessage.objects.filter(
        Q(sender=request.user, recipient=other_person) |
        Q(sender=other_person, recipient=request.user)
    ).order_by('created_at')

    context = {
        'message': message,
        'is_sender': message.sender == request.user,
        'conversation': conversation,
        'other_person': other_person,
    }
    return render(request, 'organization/messages/detail.html', context)


@login_required
def get_unread_message_count(request):
    """Okunmamış mesaj sayısını döndür"""
    count = LeaderMessage.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({'count': count})
