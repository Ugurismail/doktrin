from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('users.urls')),
    path('doctrine/', include('doctrine.urls')),
    path('organization/', include('organization.urls')),
    path('notifications/', include('notifications.urls')),
    path('predictions/', include('predictions.urls')),
]