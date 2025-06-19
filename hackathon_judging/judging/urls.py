from django.urls import path
from . import views

urlpatterns = [
    path('', views.judge_dashboard, name='judge_dashboard'),
    path('register/', views.judge_registration, name='judge_registration'),
    path('judge/<int:team_id>/', views.judge_team, name='judge_team'),
    path('admin/results/', views.admin_results, name='admin_results'),
    path('admin/export/', views.export_results, name='export_results'),
]