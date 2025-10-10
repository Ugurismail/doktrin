from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid
from datetime import datetime, timedelta

class User(AbstractUser):
    email = models.EmailField(unique=True)
    province = models.CharField(max_length=100)  # İl
    district = models.CharField(max_length=100)  # İlçe
    is_email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True, null=True)
    token_expires_at = models.DateTimeField(blank=True, null=True)
    current_team = models.ForeignKey('organization.Team', on_delete=models.SET_NULL, null=True, blank=True, related_name='members')
    joined_date = models.DateTimeField(auto_now_add=True)

    # Kurucu flag
    is_founder = models.BooleanField(default=False)

    # Öngörülülük puanı
    foresight_score = models.IntegerField(default=0)
    
    def generate_verification_token(self):
        self.email_verification_token = str(uuid.uuid4())
        self.token_expires_at = datetime.now() + timedelta(hours=24)
        self.save()
    
    def __str__(self):
        return self.username
    
class InviteCode(models.Model):
    code = models.CharField(max_length=50, unique=True)
    team = models.ForeignKey('organization.Team', on_delete=models.CASCADE, related_name='invite_codes')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_invites')
    is_used = models.BooleanField(default=False)
    used_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='used_invites')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    def __str__(self):
        return f"{self.code} - {self.team.official_name}"