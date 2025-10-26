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

    def get_leader_vote_weight(self):
        """
        Kullanıcının lider konumuna göre oy ağırlığını hesaplar.

        Kurallar:
        - Normal üye: 1 oy
        - Takım lideri: 2 oy (ekip lideri olmasa bile)
        - Birlik lideri: 3 oy (alt seviye lider olmasa bile)
        - İl lideri: 4 oy
        """
        weight = 1  # Base weight

        # İl lideri kontrolü
        from organization.models import ProvinceOrganization
        if ProvinceOrganization.objects.filter(leader=self, is_active=True).exists():
            return 4

        # Birlik lideri kontrolü
        from organization.models import Union
        if Union.objects.filter(leader=self, is_active=True).exists():
            return 3

        # Takım lideri kontrolü
        from organization.models import Squad
        if Squad.objects.filter(leader=self, is_active=True).exists():
            return 2

        # Ekip lideri veya normal üye: 1
        return weight

    def get_effective_vote_for(self, proposal):
        """
        Bir öneri için bu kullanıcının etkili oyunu döndürür.

        YENİ SİSTEM:
        Öncelik sırası:
        1. Kendi direkt oyu
        2. Delegesi varsa onun oyu
        3. Ekip lideri oyu (otomatik)
        4. Takım lideri oyu (otomatik)
        5. Birlik lideri oyu (otomatik)

        Returns: dict {
            'choice': 'YES'|'ABSTAIN'|'VETO',
            'source': 'direct'|'delegate'|'team_leader'|'squad_leader'|'union_leader',
            'weight': int (lider ağırlığı)
        } veya None
        """
        from doctrine.models import Vote

        # 1. Kendi direkt oyu var mı?
        own_vote = Vote.objects.filter(proposal=proposal, user=self).first()
        if own_vote:
            return {
                'choice': own_vote.vote_choice,
                'source': 'direct',
                'weight': self.get_leader_vote_weight()
            }

        # 2. Delege sistemi (önceki gibi çalışıyor)
        if self.vote_delegate:
            # Delegenin etkili oyunu al (recursive)
            delegate_effective = self.vote_delegate.get_effective_vote_for(proposal)
            if delegate_effective:
                return {
                    'choice': delegate_effective['choice'],
                    'source': 'delegate',
                    'weight': self.get_leader_vote_weight()  # Kendi ağırlığı
                }

        # 3. Ekip lideri oyu (otomatik)
        if self.current_team and self.current_team.leader and self.current_team.leader != self:
            leader_vote = Vote.objects.filter(
                proposal=proposal,
                user=self.current_team.leader
            ).first()
            if leader_vote:
                return {
                    'choice': leader_vote.vote_choice,
                    'source': 'team_leader',
                    'weight': self.get_leader_vote_weight()
                }

        # 4. Takım lideri oyu (otomatik)
        if self.current_team and self.current_team.parent_squad:
            squad = self.current_team.parent_squad
            if squad.leader:
                leader_vote = Vote.objects.filter(
                    proposal=proposal,
                    user=squad.leader
                ).first()
                if leader_vote:
                    return {
                        'choice': leader_vote.vote_choice,
                        'source': 'squad_leader',
                        'weight': self.get_leader_vote_weight()
                    }

        # 5. Birlik lideri oyu (otomatik)
        if self.current_team and self.current_team.parent_squad:
            squad = self.current_team.parent_squad
            if squad.parent_union and squad.parent_union.leader:
                leader_vote = Vote.objects.filter(
                    proposal=proposal,
                    user=squad.parent_union.leader
                ).first()
                if leader_vote:
                    return {
                        'choice': leader_vote.vote_choice,
                        'source': 'union_leader',
                        'weight': self.get_leader_vote_weight()
                    }

        # Hiç oy yok
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