# admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Avg
from .models import *

@admin.register(JudgeExpertise)
class JudgeExpertiseAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']

@admin.register(JudgingCriteria)
class JudgingCriteriaAdmin(admin.ModelAdmin):
    list_display = ['name', 'weight', 'get_expertise_areas']
    list_filter = ['expertise_areas']
    search_fields = ['name']
    filter_horizontal = ['expertise_areas']
    
    def get_expertise_areas(self, obj):
        return ", ".join([area.name for area in obj.expertise_areas.all()])
    get_expertise_areas.short_description = 'Expertise Areas'

@admin.register(Judge)
class JudgeAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'get_email', 'get_expertise_areas', 'has_submitted', 'created_at']
    list_filter = ['has_submitted', 'expertise_areas', 'created_at']
    search_fields = ['user__first_name', 'user__last_name', 'user__email']
    filter_horizontal = ['expertise_areas']
    readonly_fields = ['unique_token', 'created_at']
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Full Name'
    
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'
    
    def get_expertise_areas(self, obj):
        return ", ".join([area.name for area in obj.expertise_areas.all()])
    get_expertise_areas.short_description = 'Expertise Areas'

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'members', 'get_submission_count', 'get_average_score', 'created_at']
    search_fields = ['name', 'members']
    list_filter = ['created_at']
    readonly_fields = ['created_at']
    
    def get_submission_count(self, obj):
        return obj.submission_set.count()
    get_submission_count.short_description = 'Submissions'
    
    def get_average_score(self, obj):
        try:
            final_score = obj.teamfinalscore
            return f"{final_score.final_weighted_score:.2f}"
        except TeamFinalScore.DoesNotExist:
            return "Not calculated"
    get_average_score.short_description = 'Final Score'

class ScoreInline(admin.TabularInline):
    model = Score
    extra = 0
    readonly_fields = ['criteria', 'score', 'comments']

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ['get_judge_name', 'team', 'submitted_at', 'get_score_count']
    list_filter = ['submitted_at', 'judge__expertise_areas']
    search_fields = ['judge__user__first_name', 'judge__user__last_name', 'team__name']
    readonly_fields = ['submitted_at']
    inlines = [ScoreInline]
    
    def get_judge_name(self, obj):
        return obj.judge.user.get_full_name()
    get_judge_name.short_description = 'Judge'
    
    def get_score_count(self, obj):
        return obj.scores.count()
    get_score_count.short_description = 'Scores Given'

@admin.register(Score)
class ScoreAdmin(admin.ModelAdmin):
    list_display = ['get_team_name', 'get_judge_name', 'criteria', 'score', 'get_submission_date']
    list_filter = ['criteria', 'score', 'submission__submitted_at']
    search_fields = ['submission__team__name', 'submission__judge__user__first_name', 'criteria__name']
    
    def get_team_name(self, obj):
        return obj.submission.team.name
    get_team_name.short_description = 'Team'
    
    def get_judge_name(self, obj):
        return obj.submission.judge.user.get_full_name()
    get_judge_name.short_description = 'Judge'
    
    def get_submission_date(self, obj):
        return obj.submission.submitted_at
    get_submission_date.short_description = 'Submitted'

@admin.register(TeamFinalScore)
class TeamFinalScoreAdmin(admin.ModelAdmin):
    list_display = [
        'team', 'rank', 'final_weighted_score', 
        'quantum_tech_score', 'social_impact_score', 
        'innovation_score', 'presentation_score', 
        'business_viability_score', 'last_updated'
    ]
    list_filter = ['rank', 'last_updated']
    search_fields = ['team__name']
    readonly_fields = ['last_updated']
    ordering = ['rank']
    
    actions = ['recalculate_scores']
    
    def recalculate_scores(self, request, queryset):
        for team_score in queryset:
            team_score.calculate_final_score()
        self.message_user(request, f"Recalculated scores for {queryset.count()} teams.")
    recalculate_scores.short_description = "Recalculate final scores"

# Custom admin site configuration
admin.site.site_header = "Hackathon Judging System"
admin.site.site_title = "Judging Admin"
admin.site.index_title = "Welcome to Hackathon Judging Administration"

# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.judge_dashboard, name='judge_dashboard'),
    path('register/', views.judge_registration, name='judge_registration'),
    path('judge/<int:team_id>/', views.judge_team, name='judge_team'),
    path('admin/results/', views.admin_results, name='admin_results'),
    path('admin/export/', views.export_results, name='export_results'),
]

# settings.py additions
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'judging',  # Your app name
]

# Data fixtures for initial setup
# Create a management command: management/commands/setup_judging.py
from django.core.management.base import BaseCommand
from judging.models import JudgeExpertise, JudgingCriteria

class Command(BaseCommand):
    def handle(self, *args, **options):
        # Create expertise areas
        quantum_expert = JudgeExpertise.objects.get_or_create(
            name="Quantum Technology",
            defaults={'description': "Experts in quantum computing, algorithms, and hardware"}
        )[0]
        
        sustainability_expert = JudgeExpertise.objects.get_or_create(
            name="Sustainability & SDG",
            defaults={'description': "Experts in sustainable development and social impact"}
        )[0]
        
        business_expert = JudgeExpertise.objects.get_or_create(
            name="Business & Innovation",
            defaults={'description': "Experts in business strategy, innovation, and commercialization"}
        )[0]
        
        # Create judging criteria
        quantum_criteria = JudgingCriteria.objects.get_or_create(
            name="Quantum Tech Quality",
            defaults={
                'description': "Technical implementation and quantum computing excellence",
                'weight': 40.00
            })[0]
        quantum_criteria.expertise_areas.add(quantum_expert)
        
        social_criteria = JudgingCriteria.objects.get_or_create(
            name="Social Impact",
            defaults={
                'description': "Alignment with SDGs and potential social benefit",
                'weight': 25.00
            })[0]
        social_criteria.expertise_areas.add(sustainability_expert)
        
        innovation_criteria = JudgingCriteria.objects.get_or_create(
            name="Innovation",
            defaults={
                'description': "Novelty and creative approach to problem-solving",
                'weight': 20.00
            })[0]
        innovation_criteria.expertise_areas.add(quantum_expert, business_expert)
        
        presentation_criteria = JudgingCriteria.objects.get_or_create(
            name="Presentation",
            defaults={
                'description': "Quality of presentation and communication",
                'weight': 10.00
            })[0]
        presentation_criteria.expertise_areas.add(quantum_expert, sustainability_expert, business_expert)
        
        business_criteria = JudgingCriteria.objects.get_or_create(
            name="Business Viability",
            defaults={
                'description': "Commercial potential and scalability",
                'weight': 5.00
            })[0]
        business_criteria.expertise_areas.add(business_expert)
        
        self.stdout.write(self.style.SUCCESS('Successfully set up judging criteria and expertise areas'))