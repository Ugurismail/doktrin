from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class Prediction(models.Model):
    """Tahmin - Gelecek hakkında öngörü"""
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='predictions')
    title = models.CharField(max_length=300)
    description = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    deadline = models.DateTimeField()  # Tahmin bitiş tarihi (manuel seçilir)

    # Durum
    STATUS_CHOICES = [
        ('ACTIVE', 'Aktif'),
        ('EXPIRED', 'Süresi Doldu'),
        ('VERIFIED', 'Doğrulandı'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')

    # Sonuç
    is_correct = models.BooleanField(null=True, blank=True)  # Tahmin tuttu mu?

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.created_by.username}"

    @property
    def is_expired(self):
        return timezone.now() >= self.deadline and self.status == 'ACTIVE'

    @property
    def verification_deadline(self):
        """Doğrulama süresi - deadline'dan 3 gün sonra"""
        return self.deadline + timedelta(days=3)

    @property
    def can_be_verified(self):
        """Doğrulama süresi dolmamışsa True"""
        return self.status == 'EXPIRED' and timezone.now() < self.verification_deadline

    @property
    def follower_count(self):
        return self.followers.count()

    @property
    def vote_yes_count(self):
        return self.verification_votes.filter(vote='CORRECT').count()

    @property
    def vote_no_count(self):
        return self.verification_votes.filter(vote='INCORRECT').count()

    @property
    def total_votes(self):
        return self.verification_votes.count()

    @property
    def yes_percentage(self):
        if self.total_votes == 0:
            return 0
        return (self.vote_yes_count / self.total_votes) * 100

    @property
    def result(self):
        """Tahmin sonucu - en çok oy alan kazanır"""
        if self.status != 'VERIFIED':
            return None

        # Basit çoğunluk - şimdilik en çok oy alan kazanır
        if self.vote_yes_count > self.vote_no_count:
            return 'CORRECT'
        elif self.vote_no_count > self.vote_yes_count:
            return 'INCORRECT'
        else:
            return 'TIE'  # Eşitlik durumu

    @property
    def predictability_score(self):
        """Öngörülebilirlik puanı - kullanıcının doğru tahmin skoru"""
        if self.status != 'VERIFIED' or not self.is_correct:
            return None

        # Doğru tahmin ettiyse +1 puan
        if self.is_correct:
            return 1
        else:
            return -1


class PredictionFollower(models.Model):
    """Tahmin takipçisi"""
    prediction = models.ForeignKey(Prediction, on_delete=models.CASCADE, related_name='followers')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='followed_predictions')
    followed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('prediction', 'user')

    def __str__(self):
        return f"{self.user.username} -> {self.prediction.title}"


class PredictionVerificationVote(models.Model):
    """Tahmin doğrulama oyu"""
    VOTE_CHOICES = [
        ('CORRECT', 'Tuttu'),
        ('INCORRECT', 'Tutmadı'),
    ]

    prediction = models.ForeignKey(Prediction, on_delete=models.CASCADE, related_name='verification_votes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='prediction_votes')
    vote = models.CharField(max_length=10, choices=VOTE_CHOICES)
    voted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('prediction', 'user')

    def __str__(self):
        return f"{self.user.username} - {self.get_vote_display()}"
