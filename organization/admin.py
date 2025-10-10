from django.contrib import admin
from .models import Team, Squad, Union, ProvinceOrganization, LeaderVote, OrganizationFormationProposal, FormationVote

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['official_name', 'custom_name', 'district', 'province', 'leader', 'member_count', 'is_active']
    list_filter = ['province', 'district', 'is_active']
    search_fields = ['official_name', 'custom_name']

@admin.register(Squad)
class SquadAdmin(admin.ModelAdmin):
    list_display = ['name', 'province', 'leader', 'member_count', 'team_count', 'is_active']
    list_filter = ['province', 'is_active']
    search_fields = ['name']

@admin.register(Union)
class UnionAdmin(admin.ModelAdmin):
    list_display = ['name', 'province', 'leader', 'member_count', 'squad_count', 'is_active']
    list_filter = ['province', 'is_active']
    search_fields = ['name']

@admin.register(ProvinceOrganization)
class ProvinceOrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'province', 'leader', 'member_count', 'union_count', 'is_active']
    list_filter = ['province', 'is_active']
    search_fields = ['name']

@admin.register(LeaderVote)
class LeaderVoteAdmin(admin.ModelAdmin):
    list_display = ['voter', 'voter_level', 'candidate', 'voted_at']
    list_filter = ['voter_level', 'voted_at']

@admin.register(OrganizationFormationProposal)
class OrganizationFormationProposalAdmin(admin.ModelAdmin):
    list_display = ['proposed_name', 'level', 'proposed_leader', 'status', 'created_at']
    list_filter = ['level', 'status', 'created_at']

@admin.register(FormationVote)
class FormationVoteAdmin(admin.ModelAdmin):
    list_display = ['formation_proposal', 'voter', 'vote', 'voted_at']
    list_filter = ['vote', 'voted_at']