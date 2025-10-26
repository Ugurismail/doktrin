from django.urls import path
from . import views

app_name = 'doctrine'

urlpatterns = [
    path('', views.doctrine_list, name='doctrine_list'),
    path('article/<int:article_id>/', views.article_detail, name='article_detail'),
    path('proposal/<int:proposal_id>/', views.proposal_detail, name='proposal_detail'),
    path('proposal/<int:proposal_id>/vote/', views.vote_proposal, name='vote_proposal'),
    path('proposal/create/', views.create_proposal, name='create_proposal'),
    path('discussion/<int:discussion_id>/vote/', views.vote_discussion, name='vote_discussion'),
    path('activity/', views.activity_feed, name='activity_feed'),
    path('statistics/', views.statistics_dashboard, name='statistics_dashboard'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('export/text/', views.export_doctrine_text, name='export_doctrine_text'),

    # Taslak İşlemleri
    path('drafts/', views.my_drafts, name='my_drafts'),
    path('drafts/save/', views.save_proposal_draft, name='save_proposal_draft'),
    path('drafts/<int:draft_id>/load/', views.load_proposal_draft, name='load_proposal_draft'),
    path('drafts/<int:draft_id>/delete/', views.delete_draft, name='delete_draft'),

    # Reference API
    path('api/references/create/', views.reference_create, name='reference_create'),
    path('api/references/list/', views.reference_list, name='reference_list'),
    path('api/references/my-references/', views.my_references, name='my_references'),
    path('api/references/<int:ref_id>/', views.reference_detail, name='reference_detail'),
    path('api/references/<int:ref_id>/update/', views.reference_update, name='reference_update'),
    path('api/references/<int:ref_id>/usage/', views.reference_usage, name='reference_usage'),

    # Reference Pages
    path('references/', views.references_list, name='references_list'),
]