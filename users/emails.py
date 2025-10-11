"""
Email Utility Functions
Doktrin platformu için email gönderme fonksiyonları
"""

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings


def send_welcome_email(user):
    """Hoş geldiniz e-postası gönder"""
    subject = 'Doktrin Platformuna Hoş Geldiniz!'

    html_message = render_to_string('emails/welcome.html', {
        'user': user,
        'site_url': settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000',
    })

    send_mail(
        subject=subject,
        message='',  # Plain text version (boş bırakılabilir)
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_team_invite_email(user, team, invite_code, expiry_date):
    """Ekip davet kodu e-postası gönder"""
    subject = f'{team.display_name} - Davet Kodu Oluşturuldu'

    html_message = render_to_string('emails/team_invite.html', {
        'user': user,
        'team': team,
        'invite_code': invite_code,
        'expiry_date': expiry_date,
        'site_url': settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000',
    })

    send_mail(
        subject=subject,
        message='',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_new_proposal_email(user, proposal):
    """Yeni öneri bildirimi e-postası gönder"""
    subject = '🗳️ Yeni Oylama Başladı - Doktrin'

    html_message = render_to_string('emails/new_proposal.html', {
        'user': user,
        'proposal': proposal,
        'site_url': settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000',
    })

    send_mail(
        subject=subject,
        message='',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_announcement_email(user, announcement):
    """Duyuru e-postası gönder"""
    subject = f'📢 Yeni Duyuru: {announcement.title}'

    html_message = render_to_string('emails/announcement.html', {
        'user': user,
        'announcement': announcement,
        'site_url': settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000',
    })

    send_mail(
        subject=subject,
        message='',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_bulk_emails(users, subject, template_name, context):
    """
    Toplu e-posta gönder

    Args:
        users: User queryset veya listesi
        subject: E-posta konusu
        template_name: Email template dosya adı (emails/ klasöründe)
        context: Template context dictionary
    """
    site_url = settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000'

    for user in users:
        if not user.email:
            continue

        context['user'] = user
        context['site_url'] = site_url

        html_message = render_to_string(f'emails/{template_name}', context)

        send_mail(
            subject=subject,
            message='',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=True,  # Toplu gönderimde hata varsa devam et
        )
