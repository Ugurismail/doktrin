from django.core.management.base import BaseCommand
from django.utils import timezone
from doctrine.models import Proposal, ArchivedProposal, Discussion
from doctrine.vote_calculator import finalize_proposal_result

class Command(BaseCommand):
    help = 'Süresi dolan önerileri arşivle'

    def handle(self, *args, **kwargs):
        now = timezone.now()
        
        # Süresi dolmuş aktif önerileri bul
        expired_proposals = Proposal.objects.filter(
            status='ACTIVE',
            end_date__lte=now
        )
        
        archived_count = 0
        
        for proposal in expired_proposals:
            # Sonucu hesapla ve durumu güncelle
            result = finalize_proposal_result(proposal)
            
            # Tartışmaları kaydet
            discussions = Discussion.objects.filter(proposal=proposal).values(
                'user__username', 'comment_text', 'created_at'
            )
            discussions_list = list(discussions)
            
            # Arşive kaydet
            ArchivedProposal.objects.create(
                proposal=proposal,
                article=proposal.related_article,
                archived_discussions=discussions_list,
                final_vote_result=result
            )
            
            archived_count += 1
            self.stdout.write(
                self.style.SUCCESS(f'Arşivlendi: {proposal.id} - {proposal.get_proposal_type_display()}')
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Toplam {archived_count} öneri arşivlendi.')
        )