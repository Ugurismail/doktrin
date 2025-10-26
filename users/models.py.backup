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

    # Oy delegasyonu - Bu kullanıcı oylarını kime devretmiş?
    vote_delegate = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='delegated_voters',
        help_text='Oylarını devrettiği kullanıcı. Boşsa ekip liderinin oyuyla birlikte oy kullanır.'
    )
    
    def generate_verification_token(self):
        self.email_verification_token = str(uuid.uuid4())
        self.token_expires_at = datetime.now() + timedelta(hours=24)
        self.save()

    def get_effective_vote_for(self, proposal):
        """
        Bir öneri için bu kullanıcının etkili oyunu döndürür.

        Öncelik sırası:
        1. Kullanıcının kendi oyu varsa, onu döndür
        2. Yoksa ve delege varsa, delegenin oyunu döndür
        3. Yoksa ve ekip lideri varsa, liderin oyunu döndür
        4. Hiçbiri yoksa None döndür
        """
        from doctrine.models import Vote

        # 1. Kendi oyu var mı?
        own_vote = Vote.objects.filter(proposal=proposal, user=self).first()
        if own_vote:
            return own_vote

        # 2. Delege var mı ve onun oyu var mı?
        if self.vote_delegate:
            delegate_vote = Vote.objects.filter(proposal=proposal, user=self.vote_delegate).first()
            if delegate_vote:
                return delegate_vote

        # 3. Ekip lideri var mı ve onun oyu var mı?
        if self.current_team and self.current_team.leader and self.current_team.leader != self:
            leader_vote = Vote.objects.filter(proposal=proposal, user=self.current_team.leader).first()
            if leader_vote:
                return leader_vote

        return None

    def get_delegation_chain(self):
        """Delegasyon zincirini döndürür (sonsuz döngü kontrolü ile)"""
        chain = []
        current = self.vote_delegate
        visited = {self.id}

        while current and current.id not in visited:
            chain.append(current)
            visited.add(current.id)
            current = current.vote_delegate

        return chain

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