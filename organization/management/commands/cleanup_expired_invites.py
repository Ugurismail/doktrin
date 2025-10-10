from django.core.management.base import BaseCommand
from django.utils import timezone
from users.models import InviteCode


class Command(BaseCommand):
    help = 'Süresi dolmuş davet kodlarını temizler'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Silmeden önce kaç kod silineceğini göster',
        )

    def handle(self, *args, **options):
        now = timezone.now()

        # Süresi dolmuş ve kullanılmamış davet kodları
        expired_invites = InviteCode.objects.filter(
            expires_at__lt=now,
            is_used=False
        )

        count = expired_invites.count()

        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING(f'{count} adet süresi dolmuş davet kodu bulundu (silme işlemi yapılmadı)')
            )

            # İlk 10 tanesini göster
            for invite in expired_invites[:10]:
                self.stdout.write(
                    f'  - {invite.code} (Ekip: {invite.team.display_name}, '
                    f'Dolma tarihi: {invite.expires_at.strftime("%d.%m.%Y %H:%M")})'
                )

            if count > 10:
                self.stdout.write(f'  ... ve {count - 10} tane daha')
        else:
            deleted_count = expired_invites.delete()[0]
            self.stdout.write(
                self.style.SUCCESS(f'{deleted_count} adet süresi dolmuş davet kodu temizlendi')
            )
