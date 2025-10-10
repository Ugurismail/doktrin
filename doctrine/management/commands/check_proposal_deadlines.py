from django.core.management.base import BaseCommand
from django.utils import timezone
from doctrine.models import Proposal, DoctrineArticle, Activity, ArticleVersion
from notifications.utils import notify_proposal_result
from notifications.models import Notification
from users.models import User


class Command(BaseCommand):
    help = 'Süresi dolmuş önerileri kontrol eder ve sonuçlandırır'

    def handle(self, *args, **options):
        now = timezone.now()

        # Süresi dolmuş aktif önerileri bul
        expired_proposals = Proposal.objects.filter(
            status='ACTIVE',
            end_date__lt=now
        )

        count = 0
        for proposal in expired_proposals:
            # Oyları hesapla
            total_votes = proposal.vote_yes_count + proposal.vote_abstain_count + proposal.vote_veto_count

            if total_votes == 0:
                # Hiç oy yoksa arşivle
                proposal.status = 'ARCHIVED'
                proposal.save()
                self.stdout.write(f'Öneri #{proposal.id} arşivlendi (oy yok)')
                continue

            # ŞİMDİLİK TEST İÇİN: Basit çoğunluk (yes > no + abstain)
            # SONRA: Veto %15, kabul %50 sistemi olacak
            if proposal.vote_yes_count > proposal.vote_veto_count + proposal.vote_abstain_count:
                proposal.status = 'PASSED'
                proposal.save()

                # Öneri kabul edildiyse, ilgili maddeyi güncelle veya yeni madde oluştur
                if proposal.proposal_type == 'MODIFY' and proposal.related_article:
                    # Mevcut maddeyi güncelle
                    article = proposal.related_article

                    # Versiyon oluştur (eski içeriği kaydet)
                    last_version = article.versions.first()
                    next_version_number = (last_version.version_number + 1) if last_version else 1

                    ArticleVersion.objects.create(
                        article=article,
                        version_number=next_version_number,
                        content=article.content,  # Eski içerik
                        justification=article.justification,
                        changed_by_proposal=proposal
                    )

                    # Maddeyi güncelle
                    article.content = proposal.proposed_content
                    if proposal.justification:
                        article.justification = proposal.justification
                    article.save()
                    self.stdout.write(f'  → Madde #{article.id} güncellendi (v{next_version_number} oluşturuldu)')
                elif proposal.proposal_type == 'ADD':
                    # Yeni madde ekle (her zaman NORMAL_LAW)
                    last_law = DoctrineArticle.objects.filter(article_type='NORMAL_LAW').order_by('-article_number').first()
                    next_number = (last_law.article_number + 1) if last_law else 1

                    new_article = DoctrineArticle.objects.create(
                        article_number=next_number,
                        article_type='NORMAL_LAW',
                        content=proposal.proposed_content,
                        justification=proposal.justification,
                        created_by=None  # Proposal ile oluşturulan maddeler için
                    )

                    # Etiketleri ekle (eğer varsa)
                    if proposal.proposed_tags:
                        from doctrine.models import ArticleTag
                        tag_ids = proposal.proposed_tags.split(',')
                        for tag_id in tag_ids:
                            try:
                                tag = ArticleTag.objects.get(id=int(tag_id))
                                new_article.tags.add(tag)
                                self.stdout.write(f'    → Etiket eklendi: {tag.name}')
                            except (ArticleTag.DoesNotExist, ValueError):
                                pass

                    self.stdout.write(f'  → Yeni madde oluşturuldu: Yasa {new_article.article_number}')

                elif proposal.proposal_type == 'REMOVE' and proposal.related_article:
                    # Maddeyi kaldır (is_active = False)
                    article = proposal.related_article

                    # Versiyon oluştur (son hali kaydet)
                    last_version = article.versions.first()
                    next_version_number = (last_version.version_number + 1) if last_version else 1

                    ArticleVersion.objects.create(
                        article=article,
                        version_number=next_version_number,
                        content=article.content,
                        justification=f"[KALDIRILDI] {proposal.justification}",
                        changed_by_proposal=proposal
                    )

                    # Maddeyi pasif yap (silme, sadece gizle)
                    article.is_active = False
                    article.save()
                    self.stdout.write(f'  → Madde #{article.id} ({article.get_article_type_display()} {article.article_number}) kaldırıldı')

                # TÜM ÜYELERe detaylı bildirim gönder
                all_users = User.objects.filter(is_active=True)

                # Bildirim mesajını oluştur
                if proposal.proposal_type == 'MODIFY' and proposal.related_article:
                    # Eski içeriği al (original_article_content varsa onu, yoksa mevcut article.content'i)
                    old_content = proposal.original_article_content or proposal.related_article.content
                    notification_msg = f'Madde {proposal.related_article.article_number} değiştirildi! "{old_content[:50]}..." → "{proposal.proposed_content[:50]}..." ✅'
                elif proposal.proposal_type == 'ADD':
                    notification_msg = f'Yeni madde eklendi: "{proposal.proposed_content[:80]}..." ✅'
                elif proposal.proposal_type == 'REMOVE' and proposal.related_article:
                    notification_msg = f'{proposal.related_article.get_article_type_display()} {proposal.related_article.article_number} kaldırıldı! 🗑️'
                else:
                    notification_msg = f'"{proposal.get_proposal_type_display()}" önerisi KABUL edildi! Doktrin güncellendi. ✅'

                for user in all_users:
                    Notification.objects.create(
                        user=user,
                        notification_type='PROPOSAL_RESULT',
                        message=notification_msg,
                        related_object_id=proposal.id
                    )

                # Aktivite oluştur
                Activity.objects.create(
                    activity_type='PROPOSAL_PASSED',
                    user=None,  # Sistem aktivitesi
                    description=f'"{proposal.get_proposal_type_display()}" önerisi KABUL edildi.',
                    related_url=f'/doctrine/proposal/{proposal.id}/'
                )

                self.stdout.write(f'Öneri #{proposal.id} kabul edildi')
                count += 1
            else:
                proposal.status = 'REJECTED'
                proposal.save()

                # TÜM ÜYELERe bildirim gönder
                all_users = User.objects.filter(is_active=True)
                for user in all_users:
                    Notification.objects.create(
                        user=user,
                        notification_type='PROPOSAL_RESULT',
                        message=f'"{proposal.get_proposal_type_display()}" önerisi REDDEDİLDİ. ❌',
                        related_object_id=proposal.id
                    )

                # Aktivite oluştur
                Activity.objects.create(
                    activity_type='PROPOSAL_REJECTED',
                    user=None,  # Sistem aktivitesi
                    description=f'"{proposal.get_proposal_type_display()}" önerisi REDDEDİLDİ.',
                    related_url=f'/doctrine/proposal/{proposal.id}/'
                )

                self.stdout.write(f'Öneri #{proposal.id} reddedildi (yetersiz oy)')
                count += 1

        self.stdout.write(
            self.style.SUCCESS(f'{count} adet öneri sonuçlandırıldı')
        )
