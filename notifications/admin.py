from django.contrib import admin
from .models import Notification, Announcement

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['message']

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_by', 'target_level', 'created_at']
    list_filter = ['target_level', 'created_at']
    search_fields = ['title', 'content']