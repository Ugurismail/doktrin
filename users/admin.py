from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, InviteCode

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'province', 'district', 'is_email_verified', 'current_team']
    list_filter = ['is_email_verified', 'province', 'district']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Ek Bilgiler', {'fields': ('province', 'district', 'is_email_verified', 'email_verification_token', 'token_expires_at', 'current_team')}),
    )

@admin.register(InviteCode)
class InviteCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'team', 'created_by', 'is_used', 'used_by', 'created_at']
    list_filter = ['is_used', 'created_at']
    search_fields = ['code']