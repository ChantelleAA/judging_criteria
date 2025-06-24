"""
URL configuration for hackathon_judging project.
"""
from django.contrib import admin
from django.urls import path, include
from judging import views  

urlpatterns = [
    # Put custom admin URLs BEFORE the main admin/ path
    path('admin/generate-links/', views.generate_judge_links, name='generate_judge_links'),
    
    # Main admin (this catches all admin/ URLs, so it must come after custom ones)
    path('admin/', admin.site.urls),
    
    # Anonymous judge URLs:
    path('judge/<uuid:judge_token>/', views.judge_dashboard_anonymous, name='judge_dashboard_anonymous'),
    path('judge/<uuid:judge_token>/team/<int:team_id>/', views.judge_team_anonymous, name='judge_team_anonymous'),
    path('results/<str:admin_token>/', views.admin_results_anonymous, name='admin_results_anonymous'),
    path('public-judge/', views.public_judge_access, name='public_judge_access'),
    path('public-judge/team/<int:team_id>/', views.public_judge_team, name='public_judge_team'),
    
    # Your existing app URLs:
    path('', include('judging.urls')),
]