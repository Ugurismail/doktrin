from django.db import models
from django.conf import settings

class Team(models.Model):
    """Ekip - 3 ile 15 kişi arası"""
    official_name = models.CharField(max_length=100)  # Örn: "Kadıköy 13"
    custom_name = models.CharField(max_length=100, blank=True, null=True)  # Örn: "Boğalar"
    district = models.CharField(max_length=100)  # İlçe
    province = models.CharField(max_length=100)  # İl
    leader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='led_team')
    parent_squad = models.ForeignKey('Squad', on_delete=models.SET_NULL, null=True, blank=True, related_name='teams')
    created_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    @property
    def member_count(self):
        return self.members.count()
    
    @property
    def display_name(self):
        if self.custom_name:
            return f"{self.official_name} - {self.custom_name}"
        return self.official_name
    
    def __str__(self):
        return self.display_name


class Squad(models.Model):
    """Takım - Min 45 kişi, min 3 ekip"""
    name = models.CharField(max_length=100)
    province = models.CharField(max_length=100)  # İl
    leader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='led_squad')
    parent_union = models.ForeignKey('Union', on_delete=models.SET_NULL, null=True, blank=True, related_name='squads')
    created_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    @property
    def member_count(self):
        return sum(team.member_count for team in self.teams.filter(is_active=True))
    
    @property
    def team_count(self):
        return self.teams.filter(is_active=True).count()

    def check_minimum_requirements(self):
        """Minimum gereksinimleri kontrol et ve gerekirse pasif yap"""
        if self.member_count < 45 or self.team_count < 3:
            if self.is_active:
                self.is_active = False
                self.save()
                # Üst birliği de kontrol et
                if self.parent_union:
                    self.parent_union.check_minimum_requirements()
            return False
        return True

    def __str__(self):
        return self.name


class Union(models.Model):
    """Birlik - Min 135 kişi, min 3 takım"""
    name = models.CharField(max_length=100)
    province = models.CharField(max_length=100)  # İl
    leader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='led_union')
    parent_province_org = models.ForeignKey('ProvinceOrganization', on_delete=models.SET_NULL, null=True, blank=True, related_name='unions')
    created_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    @property
    def member_count(self):
        return sum(squad.member_count for squad in self.squads.filter(is_active=True))
    
    @property
    def squad_count(self):
        return self.squads.filter(is_active=True).count()

    def check_minimum_requirements(self):
        """Minimum gereksinimleri kontrol et ve gerekirse pasif yap"""
        if self.member_count < 135 or self.squad_count < 3:
            if self.is_active:
                self.is_active = False
                self.save()
                # Üst il örgütünü de kontrol et
                if self.parent_province_org:
                    self.parent_province_org.check_minimum_requirements()
            return False
        return True

    def __str__(self):
        return self.name


class ProvinceOrganization(models.Model):
    """İl Örgütü - Min 375 kişi, min 3 birlik"""
    name = models.CharField(max_length=100)
    province = models.CharField(max_length=100)  # İl
    leader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='led_province_org')
    created_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    @property
    def member_count(self):
        return sum(union.member_count for union in self.unions.filter(is_active=True))
    
    @property
    def union_count(self):
        return self.unions.filter(is_active=True).count()

    def check_minimum_requirements(self):
        """Minimum gereksinimleri kontrol et ve gerekirse pasif yap"""
        if self.member_count < 375 or self.union_count < 3:
            if self.is_active:
                self.is_active = False
                self.save()
            return False
        return True

    def __str__(self):
        return self.name
    

class LeaderVote(models.Model):
    """Lider oyu - Her zaman aktif"""
    LEVEL_CHOICES = [
        ('TEAM', 'Ekip Lideri'),
        ('SQUAD', 'Takım Lideri'),
        ('UNION', 'Birlik Lideri'),
        ('PROVINCE_ORG', 'İl Örgütü Lideri'),
    ]
    
    voter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='leader_votes_given')
    voter_level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    candidate = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='leader_votes_received')
    voted_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('voter', 'voter_level')
    
    def __str__(self):
        return f"{self.voter.username} -> {self.candidate.username} ({self.voter_level})"


class OrganizationFormationProposal(models.Model):
    """Üst örgüt oluşturma önerisi"""
    LEVEL_CHOICES = [
        ('SQUAD', 'Takım'),
        ('UNION', 'Birlik'),
        ('PROVINCE_ORG', 'İl Örgütü'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Beklemede'),
        ('APPROVED', 'Onaylandı'),
        ('REJECTED', 'Reddedildi'),
    ]
    
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    proposed_name = models.CharField(max_length=100)
    proposed_leader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='formation_proposals')
    participating_entities = models.JSONField()  # [team_ids] ya da [squad_ids]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.proposed_name} ({self.level}) - {self.status}"


class FormationVote(models.Model):
    """Oluşum oyu"""
    VOTE_CHOICES = [
        ('APPROVE', 'Onayla'),
        ('REJECT', 'Reddet'),
    ]
    
    formation_proposal = models.ForeignKey(OrganizationFormationProposal, on_delete=models.CASCADE, related_name='votes')
    voter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='formation_votes')
    vote = models.CharField(max_length=10, choices=VOTE_CHOICES)
    voted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('formation_proposal', 'voter')
    
    def __str__(self):
        return f"{self.voter.username} - {self.vote}"

