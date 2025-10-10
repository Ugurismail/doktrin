from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.conf import settings

@receiver(pre_save, sender=settings.AUTH_USER_MODEL)
def check_organization_minimums(sender, instance, **kwargs):
    """Kullanıcı ekipten ayrıldığında organizasyon minimum kontrollerini yap"""
    if instance.pk:  # Sadece mevcut kullanıcılar için
        try:
            old_user = sender.objects.get(pk=instance.pk)
            old_team = old_user.current_team
            new_team = instance.current_team

            # Ekip değişti ve eski ekip varsa
            if old_team and old_team != new_team:
                # Eski ekibin takımını kontrol et
                if old_team.parent_squad:
                    old_team.parent_squad.check_minimum_requirements()
        except sender.DoesNotExist:
            pass
