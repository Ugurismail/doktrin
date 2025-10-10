from django.db import models
from django.conf import settings

class Notification(models.Model):
    """Bildirim"""
    NOTIFICATION_TYPE_CHOICES = [
        ('NEW_PROPOSAL', 'Yeni Öneri'),
        ('PROPOSAL_PASSED', 'Öneri Kabul Edildi'),
        ('PROPOSAL_REJECTED', 'Öneri Reddedildi'),
        ('PROPOSAL_RESULT', 'Öneri Sonuçlandı'),
        ('COMMENT_REPLY', 'Yoruma Yanıt'),
        ('LEADER_CHANGE', 'Lider Değişikliği'),
        ('FORMATION_PROPOSAL', 'Örgüt Oluşturma Önerisi'),
        ('FORMATION_APPROVED', 'Örgüt Oluşturuldu'),
        ('ANNOUNCEMENT', 'Duyuru'),
        ('MENTION', 'Bahsedildin'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES)
    message = models.TextField()
    related_object_id = models.IntegerField(null=True, blank=True)  # Proposal ID, Announcement ID, etc.
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_notification_type_display()}"


class Announcement(models.Model):
    """Duyuru"""
    TARGET_LEVEL_CHOICES = [
        ('TEAM', 'Ekip'),
        ('SQUAD', 'Takım'),
        ('UNION', 'Birlik'),
        ('PROVINCE_ORG', 'İl Örgütü'),
        ('ALL', 'Tüm Üyeler'),
    ]

    title = models.CharField(max_length=200)
    content = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='announcements')
    target_level = models.CharField(max_length=20, choices=TARGET_LEVEL_CHOICES)
    target_entity_id = models.IntegerField(null=True, blank=True)  # Team/Squad/Union ID
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.get_target_level_display()}"


class LeaderMessage(models.Model):
    """Liderler arası mesajlaşma"""
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages')
    subject = models.CharField(max_length=200)
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.sender.username} → {self.recipient.username}: {self.subject}"