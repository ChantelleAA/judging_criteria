from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import transaction
from django.db.models import Avg
from django.http import JsonResponse
from .models import *
from .forms import *

def judge_registration(request):
    """Register new judges"""
    if request.method == 'POST':
        form = JudgeRegistrationForm(request.POST)
        if form.is_valid():
            # Create user account
            user = User.objects.create_user(
                username=form.cleaned_data['email'],
                email=form.cleaned_data['email'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name']
            )
            
            # Create judge profile
            judge = form.save(commit=False)
            judge.user = user
            judge.save()
            form.save_m2m()  # Save many-to-many relationships
            
            messages.success(request, 'Judge registered successfully! Login credentials sent to email.')
            return redirect('judge_login')
    else:
        form = JudgeRegistrationForm()
    
    return render(request, 'judging/register.html', {'form': form})

@login_required
def judge_dashboard(request):
    """Main dashboard for judges"""
    try:
        judge = request.user.judge
    except Judge.DoesNotExist:
        messages.error(request, 'You are not registered as a judge.')
        return redirect('judge_registration')
    
    teams = Team.objects.all()
    judged_teams = Submission.objects.filter(judge=judge).values_list('team_id', flat=True)
    
    context = {
        'judge': judge,
        'teams': teams,
        'judged_teams': judged_teams,
        'total_teams': teams.count(),
        'completed_judgments': len(judged_teams),
    }
    return render(request, 'judging/dashboard.html', context)

@login_required
def judge_team(request, team_id):
    """Judge a specific team"""
    judge = get_object_or_404(Judge, user=request.user)
    team = get_object_or_404(Team, id=team_id)
    
    # Check if already judged
    if Submission.objects.filter(judge=judge, team=team).exists():
        messages.warning(request, f'You have already judged {team.name}.')
        return redirect('judge_dashboard')
    
    if request.method == 'POST':
        form = TeamScoreForm(request.POST, judge=judge, team=team)
        if form.is_valid():
            with transaction.atomic():
                # Create submission
                submission = Submission.objects.create(
                    judge=judge,
                    team=team,
                    comments=form.cleaned_data.get('comments', '')
                )
                
                # Save individual scores
                judge_expertise = judge.expertise_areas.all()
                criteria = JudgingCriteria.objects.filter(
                    expertise_areas__in=judge_expertise
                ).distinct()
                
                for criterion in criteria:
                    score_value = form.cleaned_data.get(f'score_{criterion.id}')
                    score_comment = form.cleaned_data.get(f'comment_{criterion.id}', '')
                    
                    if score_value:
                        Score.objects.create(
                            submission=submission,
                            criteria=criterion,
                            score=score_value,
                            comments=score_comment
                        )
                
                # Update final scores
                update_team_final_scores(team)
                
            messages.success(request, f'Successfully submitted judgment for {team.name}!')
            return redirect('judge_dashboard')
    else:
        form = TeamScoreForm(judge=judge, team=team)
    
    context = {
        'form': form,
        'team': team,
        'judge': judge,
    }
    return render(request, 'judging/judge_team.html', context)

def update_team_final_scores(team):
    """Update calculated scores for a team"""
    final_score, created = TeamFinalScore.objects.get_or_create(team=team)
    
    # Calculate average scores for each criteria
    criteria_scores = {}
    for criteria in JudgingCriteria.objects.all():
        avg_score = Score.objects.filter(
            submission__team=team, 
            criteria=criteria
        ).aggregate(avg=Avg('score'))['avg'] or 0
        criteria_scores[criteria.name.lower().replace(' ', '_')] = avg_score
    
    # Map to model fields (adjust based on your criteria names)
    final_score.quantum_tech_score = criteria_scores.get('quantum_tech_quality', 0)
    final_score.social_impact_score = criteria_scores.get('social_impact', 0)
    final_score.innovation_score = criteria_scores.get('innovation', 0)
    final_score.presentation_score = criteria_scores.get('presentation', 0)
    final_score.business_viability_score = criteria_scores.get('business_viability', 0)
    
    final_score.calculate_final_score()

def admin_results(request):
    """Admin view for results and rankings"""
    teams_with_scores = TeamFinalScore.objects.select_related('team').order_by('-final_weighted_score')
    
    # Update rankings
    for i, team_score in enumerate(teams_with_scores, 1):
        team_score.rank = i
        team_score.save()
    
    context = {
        'teams_with_scores': teams_with_scores,
        'total_submissions': Submission.objects.count(),
        'total_judges': Judge.objects.count(),
    }
    return render(request, 'judging/admin_results.html', context)

def export_results(request):
    """Export results as JSON"""
    results = []
    for team_score in TeamFinalScore.objects.select_related('team').order_by('rank'):
        results.append({
            'rank': team_score.rank,
            'team_name': team_score.team.name,
            'quantum_tech_score': float(team_score.quantum_tech_score),
            'social_impact_score': float(team_score.social_impact_score),
            'innovation_score': float(team_score.innovation_score),
            'presentation_score': float(team_score.presentation_score),
            'business_viability_score': float(team_score.business_viability_score),
            'final_weighted_score': float(team_score.final_weighted_score),
        })
    
    return JsonResponse({'results': results}, indent=2)