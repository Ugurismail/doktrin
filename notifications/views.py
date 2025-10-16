from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Notification


@login_required
def notification_list(request):
    """Kullanıcının bildirimlerini listele"""
    from django.core.paginator import Paginator
    from django.utils import timezone
    from datetime import timedelta

    # Sadece okunmamış bildirimleri göster
    show_read = request.GET.get('show_read', 'false') == 'true'

    if show_read:
        # Tüm bildirimleri göster (son 30 gün)
        cutoff_date = timezone.now() - timedelta(days=30)
        all_notifications = Notification.objects.filter(
            user=request.user,
            created_at__gte=cutoff_date
        ).order_by('-created_at')
    else:
        # Sadece okunmamış bildirimleri göster
        all_notifications = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).order_by('-created_at')

    # 30 günden eski okunmuş bildirimleri otomatik temizle
    old_cutoff = timezone.now() - timedelta(days=30)
    Notification.objects.filter(
        user=request.user,
        is_read=True,
        created_at__lt=old_cutoff
    ).delete()

    # Pagination: 50 bildirim per sayfa
    paginator = Paginator(all_notifications, 50)
    page_number = request.GET.get('page', 1)
    notifications = paginator.get_page(page_number)

    # Okunmamış sayısı
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()

    return render(request, 'notifications/notification_list.html', {
        'notifications': notifications,
        'unread_count': unread_count,
        'show_read': show_read
    })


@login_required
def mark_as_read(request, notification_id):
    """Bildirimi okundu olarak işaretle"""
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})

        return redirect(request.META.get('HTTP_REFERER', 'notifications:notification_list'))
    except Notification.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False}, status=404)
        return redirect('notifications:notification_list')


@login_required
def mark_all_as_read(request):
    """Tüm bildirimleri okundu olarak işaretle"""
    if request.method == 'POST':
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})

        return redirect('notifications:notification_list')

    return redirect('notifications:notification_list')


@login_required
def get_unread_count(request):
    """Okunmamış bildirim sayısını getir (AJAX)"""
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})
