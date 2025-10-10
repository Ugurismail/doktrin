from django import template
from django.utils import timezone

register = template.Library()


@register.filter
def activity_icon(activity_type):
    """Aktivite tipine göre emoji döndür"""
    icons = {
        'proposal_created': '📋',
        'proposal_passed': '✅',
        'proposal_rejected': '❌',
        'comment_added': '💬',
        'vote_cast': '🗳️',
        'leader_changed': '👑',
        'organization_formed': '🏛️',
        'team_created': '👥',
        'prediction_created': '📋',
    }
    return icons.get(activity_type, '📌')


@register.filter
def activity_color(activity_type):
    """Aktivite tipine göre renk döndür"""
    colors = {
        'proposal_created': 'var(--pastel-blue)',
        'proposal_passed': 'var(--pastel-mint)',
        'proposal_rejected': 'var(--pastel-coral)',
        'comment_added': 'var(--pastel-lavender)',
        'vote_cast': 'var(--pastel-blue)',
        'leader_changed': 'var(--pastel-peach)',
        'organization_formed': 'var(--pastel-sage)',
        'team_created': 'var(--pastel-blue)',
        'prediction_created': '#E9D5FF',
    }
    return colors.get(activity_type, '#f0f0f0')
