from django.urls import path
from . import views

app_name = 'predictions'

urlpatterns = [
    path('', views.prediction_list, name='prediction_list'),
    path('create/', views.create_prediction, name='create_prediction'),
    path('<int:prediction_id>/', views.prediction_detail, name='prediction_detail'),
    path('<int:prediction_id>/follow/', views.toggle_follow, name='toggle_follow'),
    path('<int:prediction_id>/vote/', views.vote_prediction, name='vote_prediction'),
    path('check-expired/', views.check_expired_predictions, name='check_expired'),
]
