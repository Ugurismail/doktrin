from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('user/<str:username>/', views.user_profile, name='user_profile'),
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('guide/', views.user_guide, name='user_guide'),
    path('vote-delegation/', views.vote_delegation, name='vote_delegation'),
    path('vote-statistics/', views.vote_statistics, name='vote_statistics'),
    path('delegate-votes/', views.delegate_votes, name='delegate_votes'),
]