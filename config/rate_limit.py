"""
Basit rate limiting decorator
Spam önleme için kullanıcı başına istek limitleri
"""
from functools import wraps
from django.core.cache import cache
from django.contrib import messages
from django.shortcuts import redirect
from django.http import HttpResponse
import hashlib


def rate_limit(limit=5, period=60, message="Çok fazla istek gönderdiniz. Lütfen bekleyin.", methods=None):
    """
    Rate limiting decorator

    Args:
        limit: İzin verilen maksimum istek sayısı
        period: Zaman periyodu (saniye)
        message: Limit aşıldığında gösterilecek mesaj
        methods: Rate limit uygulanacak HTTP metodları (None = tüm metodlar, ['POST'] = sadece POST)

    Örnek:
        @rate_limit(limit=3, period=60)  # Dakikada 3 istek (tüm metodlar)
        @rate_limit(limit=20, period=60, methods=['POST'])  # Dakikada 20 POST isteği
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            # Eğer methods parametresi verilmişse ve mevcut method listede yoksa, rate limit uygulama
            if methods is not None and request.method not in methods:
                return view_func(request, *args, **kwargs)

            # Kullanıcı veya IP bazlı anahtar oluştur
            if request.user.is_authenticated:
                identifier = f"user_{request.user.id}"
            else:
                identifier = f"ip_{request.META.get('REMOTE_ADDR', 'unknown')}"

            # View adını ekle
            view_name = view_func.__name__
            cache_key = f"ratelimit_{view_name}_{identifier}"

            # Mevcut istek sayısını kontrol et
            current_count = cache.get(cache_key, 0)

            if current_count >= limit:
                # Limit aşıldı
                if request.method == 'POST':
                    messages.error(request, message)
                    referer = request.META.get('HTTP_REFERER', '/')
                    return redirect(referer)
                else:
                    return HttpResponse(
                        f"<h1>429 Too Many Requests</h1><p>{message}</p>",
                        status=429
                    )

            # İstek sayısını artır
            cache.set(cache_key, current_count + 1, period)

            # View'i çalıştır
            return view_func(request, *args, **kwargs)

        return wrapped_view
    return decorator


def get_rate_limit_key(user_or_ip, action):
    """Rate limit anahtarı oluştur"""
    return f"rate_limit:{action}:{user_or_ip}"
