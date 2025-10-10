from django.core.management.base import BaseCommand
from django.conf import settings
import os
import json
from datetime import datetime
from doctrine.models import DoctrineArticle, Proposal, Vote, Discussion, ArticleTag, ArticleVersion
from users.models import User
from organization.models import Team, Squad, Union, ProvinceOrganization


class Command(BaseCommand):
    help = 'Veritabanı yedeği oluşturur (JSON formatında)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            help='Yedek dosyasının kaydedileceği klasör (varsayılan: backups/)',
        )

    def handle(self, *args, **options):
        output_dir = options.get('output') or 'backups'

        # Klasör yoksa oluştur
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'doktrin_backup_{timestamp}.json'
        filepath = os.path.join(output_dir, filename)

        self.stdout.write('Yedekleme başlıyor...')

        backup_data = {
            'backup_date': timestamp,
            'doctrine_articles': [],
            'article_tags': [],
            'article_versions': [],
            'proposals': [],
            'votes': [],
            'discussions': [],
            'users': [],
            'teams': [],
            'squads': [],
            'unions': [],
            'province_orgs': [],
        }

        # Doctrine Articles
        for article in DoctrineArticle.objects.all():
            backup_data['doctrine_articles'].append({
                'id': article.id,
                'article_number': article.article_number,
                'article_type': article.article_type,
                'content': article.content,
                'justification': article.justification,
                'is_active': article.is_active,
                'created_date': str(article.created_date),
                'tags': [tag.id for tag in article.tags.all()],
            })
        self.stdout.write(f'  ✓ {len(backup_data["doctrine_articles"])} madde yedeklendi')

        # Article Tags
        for tag in ArticleTag.objects.all():
            backup_data['article_tags'].append({
                'id': tag.id,
                'name': tag.name,
                'slug': tag.slug,
                'color': tag.color,
                'description': tag.description,
            })
        self.stdout.write(f'  ✓ {len(backup_data["article_tags"])} etiket yedeklendi')

        # Article Versions
        for version in ArticleVersion.objects.all():
            backup_data['article_versions'].append({
                'id': version.id,
                'article_id': version.article_id,
                'version_number': version.version_number,
                'content': version.content,
                'justification': version.justification,
                'created_at': str(version.created_at),
            })
        self.stdout.write(f'  ✓ {len(backup_data["article_versions"])} versiyon yedeklendi')

        # Proposals
        for proposal in Proposal.objects.all():
            backup_data['proposals'].append({
                'id': proposal.id,
                'proposal_type': proposal.proposal_type,
                'proposed_content': proposal.proposed_content,
                'justification': proposal.justification,
                'status': proposal.status,
                'proposed_by_level': proposal.proposed_by_level,
                'start_date': str(proposal.start_date),
                'end_date': str(proposal.end_date),
                'vote_yes_count': proposal.vote_yes_count,
                'vote_abstain_count': proposal.vote_abstain_count,
                'vote_veto_count': proposal.vote_veto_count,
            })
        self.stdout.write(f'  ✓ {len(backup_data["proposals"])} öneri yedeklendi')

        # Votes
        backup_data['votes'] = Vote.objects.count()
        self.stdout.write(f'  ✓ {backup_data["votes"]} oy sayısı kaydedildi')

        # Discussions
        backup_data['discussions'] = Discussion.objects.count()
        self.stdout.write(f'  ✓ {backup_data["discussions"]} yorum sayısı kaydedildi')

        # Users (sadece sayı ve temel bilgiler)
        for user in User.objects.all():
            backup_data['users'].append({
                'id': user.id,
                'username': user.username,
                'province': user.province,
                'district': user.district,
                'is_active': user.is_active,
                'foresight_score': user.foresight_score,
            })
        self.stdout.write(f'  ✓ {len(backup_data["users"])} kullanıcı yedeklendi')

        # Organization
        backup_data['teams'] = Team.objects.count()
        backup_data['squads'] = Squad.objects.count()
        backup_data['unions'] = Union.objects.count()
        backup_data['province_orgs'] = ProvinceOrganization.objects.count()
        self.stdout.write(f'  ✓ Organizasyon yapısı kaydedildi')

        # JSON dosyasına yaz
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)

        file_size = os.path.getsize(filepath) / 1024  # KB
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Yedekleme tamamlandı!\n'
                f'📁 Dosya: {filepath}\n'
                f'📊 Boyut: {file_size:.2f} KB\n'
                f'📅 Tarih: {datetime.now().strftime("%d.%m.%Y %H:%M:%S")}'
            )
        )
