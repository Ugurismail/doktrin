from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Notification


@login_required
def notification_list(request):
    """Kullanıcının bildirimlerini listele"""
    from django.core.paginator import Paginator

    all_notifications = Notification.objects.filter(user=request.user).order_by('-created_at')

    # Pagination: 50 bildirim per sayfa
    paginator = Paginator(all_notifications, 50)
    page_number = request.GET.get('page', 1)
    notifications = paginator.get_page(page_number)

    return render(request, 'notifications/notification_list.html', {
        'notifications': notifications
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
