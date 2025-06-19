# judging/urls.py - SIMPLIFIED FOR PRE-DEFINED JUDGES
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Home redirect
    path('', views.home_redirect, name='home'),
    
    # Judge-specific URLs
    path('dashboard/', views.judge_dashboard, name='judge_dashboard'),
    path('judge/<int:team_id>/', views.judge_team, name='judge_team'),
    
    # Admin URLs
    path('results/', views.admin_results, name='admin_results'),
    path('admin/export/', views.export_results, name='export_results'),
    
    # Authentication URLs
    path('login/', views.JudgeLoginView.as_view(), name='judge_login'),
    # FIXED: Use custom logout template
    path('logout/', auth_views.LogoutView.as_view(
        template_name='judging/logout.html',
        next_page='judge_login',
        http_method_names=['get', 'post']
    ), name='logout'),
    
    # Password change (for judges to update their passwords)
    path('password-change/', 
         auth_views.PasswordChangeView.as_view(
             template_name='judging/password_change.html',
             success_url='/dashboard/'
         ), 
         name='password_change'),
]