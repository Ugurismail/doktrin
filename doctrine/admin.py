from django.contrib import admin
from .models import DoctrineArticle, Proposal, Vote, Discussion, ArchivedProposal, ArticleTag, ArticleVersion

@admin.register(DoctrineArticle)
class DoctrineArticleAdmin(admin.ModelAdmin):
    list_display = ['article_number', 'article_type', 'created_by', 'created_date', 'is_active']
    list_filter = ['article_type', 'is_active', 'created_date']
    search_fields = ['content']

@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    list_display = ['proposal_type', 'proposed_by_level', 'status', 'start_date', 'end_date']
    list_filter = ['proposal_type', 'proposed_by_level', 'status', 'start_date']
    search_fields = ['proposed_content']

@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ['user', 'proposal', 'vote_choice', 'voted_at']
    list_filter = ['vote_choice', 'voted_at']

@admin.register(Discussion)
class DiscussionAdmin(admin.ModelAdmin):
    list_display = ['user', 'article', 'proposal', 'created_at']
    list_filter = ['created_at']
    search_fields = ['comment_text']

@admin.register(ArchivedProposal)
class ArchivedProposalAdmin(admin.ModelAdmin):
    list_display = ['proposal', 'article', 'archived_at']
    list_filter = ['archived_at']

@admin.register(ArticleTag)
class ArticleTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'color', 'created_at']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(ArticleVersion)
class ArticleVersionAdmin(admin.ModelAdmin):
    list_display = ['article', 'version_number', 'changed_by_proposal', 'created_at']
    list_filter = ['created_at']