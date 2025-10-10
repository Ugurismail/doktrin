from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import JsonResponse
from .models import Prediction, PredictionFollower, PredictionVerificationVote
from doctrine.models import Activity
from users.models import User


@login_required
def prediction_list(request):
    """Tahmin listesi"""
    from django.utils import timezone
    from notifications.models import Notification

    # Süresi dolmuş tahminleri bul ve güncelle
    expired_predictions = Prediction.objects.filter(status='ACTIVE', deadline__lte=timezone.now())

    for prediction in expired_predictions:
        # Takipçilere bildirim gönder (sadece ilk kez expiring olduğunda)
        followers = PredictionFollower.objects.filter(prediction=prediction).select_related('user')
        for follower in followers:
            if follower.user != prediction.created_by:
                # Zaten bildirim gönderilmiş mi kontrol et
                existing = Notification.objects.filter(
                    user=follower.user,
                    notification_type='MENTION',  # Genel bildirim tipi
                    related_object_id=prediction.id,
                    message__contains='tahmini için artık oy verebilirsiniz'
                ).exists()
                if not existing:
                    Notification.objects.create(
                        user=follower.user,
                        notification_type='MENTION',
                        message=f'"{prediction.title}" tahmini için artık oy verebilirsiniz.',
                        related_object_id=prediction.id
                    )

        # Tahmin sahibine bildirim
        existing = Notification.objects.filter(
            user=prediction.created_by,
            notification_type='MENTION',
            related_object_id=prediction.id,
            message__contains='tahmininiz için oylama başladı'
        ).exists()
        if not existing:
            Notification.objects.create(
                user=prediction.created_by,
                notification_type='MENTION',
                message=f'"{prediction.title}" tahmininiz için oylama başladı.',
                related_object_id=prediction.id
            )

        # Durumu güncelle
        prediction.status = 'EXPIRED'
        prediction.save()

    # Aktif tahminler
    active_predictions = Prediction.objects.filter(status='ACTIVE').select_related('created_by').order_by('-created_at')

    # Süresi dolmuş tahminler
    expired_predictions = Prediction.objects.filter(status='EXPIRED').select_related('created_by').order_by('-deadline')[:10]

    # Doğrulanmış tahminler
    verified_predictions = Prediction.objects.filter(status='VERIFIED').select_related('created_by').order_by('-created_at')[:10]

    context = {
        'active_predictions': active_predictions,
        'expired_predictions': expired_predictions,
        'verified_predictions': verified_predictions,
    }
    return render(request, 'predictions/prediction_list.html', context)


@login_required
def create_prediction(request):
    """Tahmin oluştur"""
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        deadline_str = request.POST.get('deadline')

        # Tarihi parse et
        from django.utils.dateparse import parse_datetime
        from django.utils import timezone
        from datetime import datetime, timedelta

        try:
            # Tarih formatı: YYYY-MM-DDTHH:MM
            deadline = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M')
            deadline = timezone.make_aware(deadline)

            # Validasyon: En az bugünden sonra olmalı
            if deadline <= timezone.now():
                messages.error(request, 'Tahmin tarihi gelecekte olmalıdır.')
                return render(request, 'predictions/create_prediction.html')

            # Validasyon: En fazla 10 yıl sonrası
            max_date = timezone.now() + timedelta(days=365 * 10)
            if deadline > max_date:
                messages.error(request, 'Tahmin tarihi en fazla 10 yıl sonrası olabilir.')
                return render(request, 'predictions/create_prediction.html')

        except (ValueError, TypeError):
            messages.error(request, 'Geçersiz tarih formatı.')
            return render(request, 'predictions/create_prediction.html')

        # Tahmini oluştur
        prediction = Prediction.objects.create(
            created_by=request.user,
            title=title,
            description=description,
            deadline=deadline
        )

        # Aktivite oluştur
        Activity.objects.create(
            activity_type='prediction_created',
            user=request.user,
            description=f'Tahmin oluşturdu: {title[:50]}',
            related_url=f'/predictions/{prediction.id}/'
        )

        messages.success(request, 'Tahmininiz oluşturuldu!')
        return redirect('predictions:prediction_detail', prediction_id=prediction.id)

    return render(request, 'predictions/create_prediction.html')


@login_required
def prediction_detail(request, prediction_id):
    """Tahmin detayı"""
    from django.utils import timezone
    from notifications.models import Notification

    prediction = get_object_or_404(Prediction, id=prediction_id)

    # Süresi dolmuş mu kontrol et ve güncelle
    if prediction.status == 'ACTIVE' and timezone.now() >= prediction.deadline:
        # Takipçilere bildirim gönder
        followers = PredictionFollower.objects.filter(prediction=prediction).select_related('user')
        for follower in followers:
            if follower.user != prediction.created_by:
                # Zaten bildirim gönderilmiş mi kontrol et
                existing = Notification.objects.filter(
                    user=follower.user,
                    notification_type='MENTION',
                    related_object_id=prediction.id,
                    message__contains='tahmini için artık oy verebilirsiniz'
                ).exists()
                if not existing:
                    Notification.objects.create(
                        user=follower.user,
                        notification_type='MENTION',
                        message=f'"{prediction.title}" tahmini için artık oy verebilirsiniz.',
                        related_object_id=prediction.id
                    )

        # Tahmin sahibine bildirim
        existing = Notification.objects.filter(
            user=prediction.created_by,
            notification_type='MENTION',
            related_object_id=prediction.id,
            message__contains='tahmininiz için oylama başladı'
        ).exists()
        if not existing:
            Notification.objects.create(
                user=prediction.created_by,
                notification_type='MENTION',
                message=f'"{prediction.title}" tahmininiz için oylama başladı.',
                related_object_id=prediction.id
            )

        # Durumu güncelle
        prediction.status = 'EXPIRED'
        prediction.save()

    # Kullanıcı takip ediyor mu?
    is_following = PredictionFollower.objects.filter(
        prediction=prediction,
        user=request.user
    ).exists()

    # Kullanıcı oy vermiş mi?
    user_vote = PredictionVerificationVote.objects.filter(
        prediction=prediction,
        user=request.user
    ).first()

    # Takipçiler
    followers = prediction.followers.select_related('user').all()[:20]

    # Oylar
    votes = prediction.verification_votes.select_related('user').all()[:50]

    context = {
        'prediction': prediction,
        'is_following': is_following,
        'user_vote': user_vote,
        'followers': followers,
        'votes': votes,
    }
    return render(request, 'predictions/prediction_detail.html', context)


@login_required
def toggle_follow(request, prediction_id):
    """Tahmini takip et/bırak"""
    prediction = get_object_or_404(Prediction, id=prediction_id)

    follower = PredictionFollower.objects.filter(
        prediction=prediction,
        user=request.user
    ).first()

    if follower:
        follower.delete()
        messages.success(request, 'Tahmin takipten çıkarıldı.')
    else:
        PredictionFollower.objects.create(
            prediction=prediction,
            user=request.user
        )
        messages.success(request, 'Tahmin takip ediliyor.')

    return redirect('predictions:prediction_detail', prediction_id=prediction.id)


@login_required
def vote_prediction(request, prediction_id):
    """Tahmin doğrulama oyu ver"""
    prediction = get_object_or_404(Prediction, id=prediction_id)

    # Kendi tahminine oy veremez
    if prediction.created_by == request.user:
        messages.error(request, 'Kendi tahmininize oy veremezsiniz!')
        return redirect('predictions:prediction_detail', prediction_id=prediction.id)

    # Sadece süresi dolmuş tahminlere oy verilebilir
    if prediction.status != 'EXPIRED':
        messages.error(request, 'Bu tahminin süresi henüz dolmadı.')
        return redirect('predictions:prediction_detail', prediction_id=prediction.id)

    if request.method == 'POST':
        vote_choice = request.POST.get('vote')  # 'CORRECT' or 'INCORRECT'

        # Validasyon: oy seçilmiş mi?
        if not vote_choice:
            messages.error(request, 'Lütfen bir seçenek seçin!')
            return redirect('predictions:prediction_detail', prediction_id=prediction.id)

        # Oy ver veya güncelle (herkes oy verebilir)
        vote, created = PredictionVerificationVote.objects.update_or_create(
            prediction=prediction,
            user=request.user,
            defaults={'vote': vote_choice}
        )

        # Oylamayı kontrol et - 3/4 kontrolü için
        from users.models import User
        total_users = User.objects.count()
        required_voters = int(total_users * 0.75)  # Sitenin %75'i oy vermeli

        # Oy sayısını kontrol et ve %75'e ulaştıysa puanla
        if prediction.total_votes >= required_voters:
            if prediction.yes_percentage >= 75:
                # Tahmin tuttu! Puan ver
                prediction.is_correct = True
                prediction.status = 'VERIFIED'
                prediction.save()

                # Tahmin sahibine puan ver
                creator = prediction.created_by
                creator.foresight_score += 1
                creator.save()

                messages.success(request, 'Tahmin doğrulandı! Puan verildi.')
            elif prediction.vote_no_count / prediction.total_votes >= 0.75:
                # Tahmin tutmadı
                prediction.is_correct = False
                prediction.status = 'VERIFIED'
                prediction.save()

                messages.info(request, 'Tahmin doğrulandı: Tutmadı.')
        else:
            messages.success(request, 'Oyunuz kaydedildi.')

        return redirect('predictions:prediction_detail', prediction_id=prediction.id)

    return redirect('predictions:prediction_detail', prediction_id=prediction.id)


@login_required
def check_expired_predictions(request):
    """Süresi dolmuş tahminleri kontrol et ve bildirim gönder (AJAX)"""
    from django.utils import timezone
    from notifications.models import Notification

    # Süresi dolmuş tahminleri bul
    expired_predictions = Prediction.objects.filter(status='ACTIVE', deadline__lte=timezone.now())

    for prediction in expired_predictions:
        # Takipçilere bildirim gönder
        followers = PredictionFollower.objects.filter(prediction=prediction).select_related('user')
        for follower in followers:
            if follower.user != prediction.created_by:
                # Zaten bildirim gönderilmiş mi kontrol et
                existing = Notification.objects.filter(
                    user=follower.user,
                    notification_type='MENTION',
                    related_object_id=prediction.id,
                    message__contains='tahmini için artık oy verebilirsiniz'
                ).exists()
                if not existing:
                    Notification.objects.create(
                        user=follower.user,
                        notification_type='MENTION',
                        message=f'"{prediction.title}" tahmini için artık oy verebilirsiniz.',
                        related_object_id=prediction.id
                    )

        # Tahmin sahibine bildirim
        existing = Notification.objects.filter(
            user=prediction.created_by,
            notification_type='MENTION',
            related_object_id=prediction.id,
            message__contains='tahmininiz için oylama başladı'
        ).exists()
        if not existing:
            Notification.objects.create(
                user=prediction.created_by,
                notification_type='MENTION',
                message=f'"{prediction.title}" tahmininiz için oylama başladı.',
                related_object_id=prediction.id
            )

        # Durumu güncelle
        prediction.status = 'EXPIRED'
        prediction.save()

    return JsonResponse({'success': True, 'expired_count': len(expired_predictions)})
