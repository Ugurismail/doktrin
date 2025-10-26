from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from users.models import User
from doctrine.models import Vote


class Command(BaseCommand):
    help = '60 gün içinde direkt oy vermemiş kullanıcıları siler'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Silmeden önce hangi kullanıcıların silineceğini gösterir',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=60,
            help='Kaç gün inaktif kullanıcılar silinecek (varsayılan: 60)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        days = options['days']

        # 60 gün önceki tarih
        cutoff_date = timezone.now() - timedelta(days=days)

        self.stdout.write(self.style.WARNING(
            f'\n{days} gün önce: {cutoff_date.strftime("%Y-%m-%d %H:%M:%S")}'
        ))

        # Tüm kullanıcıları al
        all_users = User.objects.all()

        users_to_delete = []
        active_users_count = 0
        founder_protected = 0

        for user in all_users:
            # Kurucu üyeleri asla silme
            if user.is_founder:
                founder_protected += 1
                continue

            # Kullanıcının son direkt oyunu bul
            last_direct_vote = Vote.objects.filter(
                user=user,
                voted_at__gte=cutoff_date
            ).order_by('-voted_at').first()

            if last_direct_vote:
                # Son 60 gün içinde direkt oy vermiş
                active_users_count += 1
            else:
                # Son 60 gün içinde direkt oy vermemiş
                users_to_delete.append(user)

        # Sonuçları göster
        self.stdout.write(self.style.SUCCESS(
            f'\n📊 İstatistikler:'
        ))
        self.stdout.write(f'  • Toplam kullanıcı: {all_users.count()}')
        self.stdout.write(f'  • Aktif kullanıcı (son {days} gün içinde oy vermiş): {active_users_count}')
        self.stdout.write(f'  • Kurucu üye (korunuyor): {founder_protected}')
        self.stdout.write(self.style.WARNING(
            f'  • Silinecek inaktif kullanıcı: {len(users_to_delete)}'
        ))

        if users_to_delete:
            self.stdout.write(f'\n📋 Silinecek kullanıcılar:')
            for user in users_to_delete[:20]:  # İlk 20'yi göster
                last_vote = Vote.objects.filter(user=user).order_by('-voted_at').first()
                if last_vote:
                    last_vote_date = last_vote.voted_at.strftime("%Y-%m-%d")
                    self.stdout.write(f'  • {user.username} (son oy: {last_vote_date})')
                else:
                    self.stdout.write(f'  • {user.username} (hiç oy vermemiş)')

            if len(users_to_delete) > 20:
                self.stdout.write(f'  ... ve {len(users_to_delete) - 20} kullanıcı daha')

        # Silme işlemi
        if dry_run:
            self.stdout.write(self.style.SUCCESS(
                f'\n✅ DRY RUN modu - Hiçbir kullanıcı silinmedi'
            ))
            self.stdout.write(
                'Gerçekten silmek için: python manage.py cleanup_inactive_users'
            )
        else:
            if users_to_delete:
                # Onay iste
                confirm = input(
                    f'\n⚠️  {len(users_to_delete)} kullanıcı SİLİNECEK. Devam etmek istiyor musunuz? (yes/no): '
                )

                if confirm.lower() == 'yes':
                    deleted_count = 0
                    for user in users_to_delete:
                        user.delete()
                        deleted_count += 1

                    self.stdout.write(self.style.SUCCESS(
                        f'\n✅ {deleted_count} inaktif kullanıcı başarıyla silindi!'
                    ))
                else:
                    self.stdout.write(self.style.WARNING(
                        '\n❌ İşlem iptal edildi.'
                    ))
            else:
                self.stdout.write(self.style.SUCCESS(
                    f'\n✅ Silinecek inaktif kullanıcı yok!'
                ))
