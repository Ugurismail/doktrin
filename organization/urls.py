from django.urls import path
from . import views
from . import message_views

app_name = 'organization'

urlpatterns = [
    path('team/', views.my_team, name='my_team'),
    path('team/create/', views.create_team, name='create_team'),
    path('team/join/', views.join_team, name='join_team'),
    path('team/invite/', views.create_invite, name='create_invite'),
    path('squad/', views.my_squad, name='my_squad'),
    path('union/', views.my_union, name='my_union'),
    path('squad/propose/', views.propose_squad, name='propose_squad'),
    path('squad/vote/<int:proposal_id>/', views.vote_squad_formation, name='vote_squad_formation'),
    path('union/propose/', views.propose_union, name='propose_union'),
    path('union/vote/<int:proposal_id>/', views.vote_union_formation, name='vote_union_formation'),
    path('team/leader/vote/', views.vote_team_leader, name='vote_team_leader'),
    path('squad/leader/vote/', views.vote_squad_leader, name='vote_squad_leader'),
    path('union/leader/vote/', views.vote_union_leader, name='vote_union_leader'),
    path('province-org/', views.my_province_org, name='my_province_org'),
    path('province-org/propose/', views.propose_province_org, name='propose_province_org'),
    path('province-org/vote/<int:proposal_id>/', views.vote_province_org_formation, name='vote_province_org_formation'),
    path('province-org/leader/vote/', views.vote_province_org_leader, name='vote_province_org_leader'),
    path('chart/', views.organization_chart, name='organization_chart'),
    path('announcement/create/', views.create_announcement, name='create_announcement'),
    path('announcement/', views.view_announcements, name='view_announcements'),
    # Management Panels
    path('team/manage/', views.manage_team, name='manage_team'),
    path('squad/manage/', views.manage_squad, name='manage_squad'),
    path('union/manage/', views.manage_union, name='manage_union'),
    # Member Transfer
    path('transfer/', views.request_team_transfer, name='request_team_transfer'),
    # Messages
    path('messages/inbox/', message_views.message_inbox, name='message_inbox'),
    path('messages/sent/', message_views.message_sent, name='message_sent'),
    path('messages/compose/', message_views.message_compose, name='message_compose'),
    path('messages/<int:message_id>/', message_views.message_detail, name='message_detail'),
    path('messages/unread-count/', message_views.get_unread_message_count, name='get_unread_message_count'),
]