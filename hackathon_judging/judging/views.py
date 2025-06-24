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
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.contrib.auth import logout
from collections import defaultdict
import json
from django.core.serializers.json import DjangoJSONEncoder
import uuid
from django.http import HttpResponse

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


def judge_team(request, team_id):
    """Judge a specific team - UPDATED VERSION"""
    if not request.user.is_authenticated:
        return redirect('judge_login')

    judge = get_object_or_404(Judge, user=request.user)
    team = get_object_or_404(Team, id=team_id)

    if Submission.objects.filter(judge=judge, team=team).exists():
        messages.warning(request, f'You have already judged {team.name}.')
        return redirect('judge_dashboard')

    if request.method == 'POST':
        form = TeamScoreForm(request.POST, judge=judge, team=team)
        if form.is_valid():
            with transaction.atomic():
                submission = Submission.objects.create(
                    judge=judge,
                    team=team,
                    comments=form.cleaned_data.get('comments', '')
                )

                # Determine which criteria the judge scored based on form fields
                for key in form.cleaned_data:
                    if key.startswith("score_"):
                        criterion_id = key.split("_")[1]
                        criterion = get_object_or_404(JudgingCriteria, id=criterion_id)
                        score_value = form.cleaned_data.get(key)
                        score_comment = form.cleaned_data.get(f'comment_{criterion_id}', '')

                        if score_value:
                            Score.objects.create(
                                submission=submission,
                                criteria=criterion,
                                score=score_value,
                                comments=score_comment
                            )

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

def custom_logout_view(request):
    """Custom logout view that properly clears session"""
    # Clear the session FIRST
    logout(request)
    
    # Now render the template (user will be anonymous)
    return render(request, 'judging/logout.html')


def admin_results(request):
    """Results dashboard – supplies JSON blobs for Chart.js - FIXED VERSION"""
    if not request.user.is_authenticated:
        return redirect('judge_login')

    # allow staff or judges
    if not (request.user.is_staff or hasattr(request.user, 'judge')):
        messages.error(request, "You don't have permission to view results.")
        return redirect('judge_dashboard')

    # ---------- 1. Final-score queryset -----------------
    teams_with_scores = (
        TeamFinalScore.objects
        .select_related('team')
        .order_by('-final_weighted_score')
    )

    # update rank, if changed
    for idx, tfs in enumerate(teams_with_scores, 1):
        if tfs.rank != idx:
            tfs.rank = idx
            tfs.save(update_fields=['rank'])

    # ---------- 2. Per-criterion averages ---------------
    criteria_qs = JudgingCriteria.objects.all()
    team_crit_avg = defaultdict(dict)          # {team_id:{crit:avg}}

    for crit in criteria_qs:
        for row in (Score.objects
                    .filter(criteria=crit)
                    .values('submission__team')
                    .annotate(avg=Avg('score'))):
            team_id = row['submission__team']
            team_crit_avg[team_id][crit.name] = float(row['avg'])

    # fill in missing criteria with 0
    for t_id in team_crit_avg:
        for crit in criteria_qs:
            team_crit_avg[t_id].setdefault(crit.name, 0)

    # ---------- 3. Pack teams_json - FIXED VERSION ----------------------
    teams_json = []
    for tfs in teams_with_scores:
        # Get scores for this team
        team_scores = team_crit_avg.get(tfs.team.id, {})
        
        # Ensure all criteria are present with fallbacks
        scores_dict = {}
        for crit in criteria_qs:
            scores_dict[crit.name] = team_scores.get(crit.name, 0)
        
        teams_json.append({
            'team': tfs.team.name,                                    # Team name as string
            'final_weighted_score': float(tfs.final_weighted_score),  # Final score
            'rank': tfs.rank,                                        # Add rank - THIS WAS MISSING!
            'scores': scores_dict,                                   # Criteria scores
            'members': getattr(tfs.team, 'members', 'Team Members'), # Add members if available
            'description': getattr(tfs.team, 'description', ''),     # Add description if available
            'presentation_link': getattr(tfs.team, 'presentation_link', ''), # Add presentation link if available
        })

    # ---------- 4. Raw per-judge scores -----------------
    all_scores = list(
        Score.objects.values(
            'criteria__name',          # e.g. "Innovation"
            'submission__team__name',  # e.g. "QBits"
            'submission__judge__id',   # judge id (int)
            'score'                    # 1-10
        )
    )

    # ---------- 5. Context sent to template - ENHANCED -------------
    context = {
        'teams_with_scores': teams_with_scores,
        'total_submissions': Submission.objects.count(),
        'total_judges':      Judge.objects.count(),

        # JSON blobs for JavaScript
        'criteria_labels': json.dumps([c.name for c in criteria_qs]),
        'teams_json':      json.dumps(teams_json,  cls=DjangoJSONEncoder),
        'all_scores_json': json.dumps(all_scores,  cls=DjangoJSONEncoder),
    }
    
    # Debug logging - you can remove this after testing
    print("DEBUG - First team data:", teams_json[0] if teams_json else "No teams")
    print("DEBUG - Criteria labels:", [c.name for c in criteria_qs])
    
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

# REPLACE the judge_registration view with this:
def judge_registration(request):
    """Register new judges - FIXED VERSION"""
    if request.method == 'POST':
        form = JudgeRegistrationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create user account
                    user = User.objects.create_user(
                        username=form.cleaned_data['email'],
                        email=form.cleaned_data['email'],
                        first_name=form.cleaned_data['first_name'],
                        last_name=form.cleaned_data['last_name'],
                        password='hackathon2025!'  # Default password
                    )
                    
                    # Create judge profile
                    judge = Judge.objects.create(user=user)
                    
                    # Add expertise areas
                    for expertise in form.cleaned_data['expertise_areas']:
                        judge.expertise_areas.add(expertise)
                    
                    # Auto-login the user
                    user = authenticate(username=form.cleaned_data['email'], password='hackathon2025!')
                    if user:
                        auth_login(request, user)
                        messages.success(request, f'Welcome {user.get_full_name()}! Your account has been created. Please change your password.')
                        return redirect('judge_dashboard')
                    else:
                        messages.success(request, 'Judge registered successfully! Please login with your credentials.')
                        return redirect('judge_login')
                        
            except Exception as e:
                messages.error(request, f'Registration failed: {str(e)}')
    else:
        form = JudgeRegistrationForm()
    
    return render(request, 'judging/register.html', {'form': form})

# ADD this custom login view
class JudgeLoginView(LoginView):
    """Custom login view that redirects judges to dashboard"""
    template_name = 'judging/login.html'
    
    def get_success_url(self):
        # Check if user is a judge
        if hasattr(self.request.user, 'judge'):
            return reverse_lazy('judge_dashboard')
        # If admin/staff, go to admin
        elif self.request.user.is_staff:
            return reverse_lazy('admin:index')
        # Otherwise go to registration
        else:
            return reverse_lazy('judge_registration')

def home_redirect(request):
    """Smart redirect based on user type"""
    if not request.user.is_authenticated:
        return redirect('judge_registration')
    
    if hasattr(request.user, 'judge'):
        return redirect('judge_dashboard')
    elif request.user.is_staff:
        return redirect('admin:index')
    else:
        return redirect('judge_registration')



def home_redirect(request):
    """Smart redirect for pre-defined judges system"""
    if not request.user.is_authenticated:
        return redirect('judge_login')
    
    # If user is a judge, go to dashboard
    if hasattr(request.user, 'judge'):
        return redirect('judge_dashboard')
    # If admin/staff, go to admin panel
    elif request.user.is_staff:
        return redirect('admin:index')
    # If authenticated but not a judge, show message and redirect to login
    else:
        messages.warning(request, 'You are not registered as a judge for this hackathon. Please contact the administrator.')
        return redirect('judge_login')

def judge_dashboard(request):
    """Main dashboard for pre-defined judges"""
    if not request.user.is_authenticated:
        return redirect('judge_login')
    
    try:
        judge = request.user.judge
    except Judge.DoesNotExist:
        messages.error(request, 'You are not registered as a judge for this hackathon. Please contact the administrator if you believe this is an error.')
        return redirect('judge_login')
    
    teams = Team.objects.all()
    judged_teams = Submission.objects.filter(judge=judge).values_list('team_id', flat=True)
    
    context = {
        'judge': judge,
        'teams': teams,
        'judged_teams': judged_teams,
        'total_teams': teams.count(),
        'completed_judgments': len(judged_teams),
        'remaining_teams': teams.count() - len(judged_teams)
    }
    return render(request, 'judging/dashboard.html', context)
class JudgeLoginView(LoginView):
    """Custom login view for pre-defined judges"""
    template_name = 'judging/login.html'
    
    def get_success_url(self):
        # Check if user is a judge
        if hasattr(self.request.user, 'judge'):
            return reverse_lazy('judge_dashboard')
        # If admin/staff, go to admin
        elif self.request.user.is_staff:
            return reverse_lazy('admin:index')
        # Otherwise show error and stay on login
        else:
            messages.error(self.request, 'You are not registered as a judge. Please contact the administrator.')
            return reverse_lazy('judge_login')
        

def judge_dashboard_anonymous(request, judge_token):
    """Anonymous judge dashboard using unique token"""
    try:
        judge = get_object_or_404(Judge, unique_token=judge_token)
    except:
        messages.error(request, 'Invalid or expired judge link. Please contact the administrator.')
        return render(request, 'judging/invalid_link.html')
    
    teams = Team.objects.all()
    judged_teams = Submission.objects.filter(judge=judge).values_list('team_id', flat=True)
    
    # Store judge in session for form submissions
    request.session['judge_id'] = judge.id
    request.session['judge_name'] = judge.user.get_full_name()
    
    context = {
        'judge': judge,
        'teams': teams,
        'judged_teams': judged_teams,
        'total_teams': teams.count(),
        'completed_judgments': len(judged_teams),
        'remaining_teams': teams.count() - len(judged_teams),
        'is_anonymous': True,
        'judge_token': judge_token,
    }
    return render(request, 'judging/dashboard.html', context)

def judge_team_anonymous(request, judge_token, team_id):
    """Anonymous team judging using unique token"""
    try:
        judge = get_object_or_404(Judge, unique_token=judge_token)
        team = get_object_or_404(Team, id=team_id)
    except:
        messages.error(request, 'Invalid link. Please contact the administrator.')
        return redirect('home_anonymous')

    if Submission.objects.filter(judge=judge, team=team).exists():
        messages.warning(request, f'You have already judged {team.name}.')
        return redirect('judge_dashboard_anonymous', judge_token=judge_token)

    if request.method == 'POST':
        form = TeamScoreForm(request.POST, judge=judge, team=team)
        if form.is_valid():
            with transaction.atomic():
                submission = Submission.objects.create(
                    judge=judge,
                    team=team,
                    comments=form.cleaned_data.get('comments', '')
                )

                # Save scores
                for key in form.cleaned_data:
                    if key.startswith("score_"):
                        criterion_id = key.split("_")[1]
                        criterion = get_object_or_404(JudgingCriteria, id=criterion_id)
                        score_value = form.cleaned_data.get(key)
                        score_comment = form.cleaned_data.get(f'comment_{criterion_id}', '')

                        if score_value:
                            Score.objects.create(
                                submission=submission,
                                criteria=criterion,
                                score=score_value,
                                comments=score_comment
                            )

                update_team_final_scores(team)
                messages.success(request, f'Successfully submitted judgment for {team.name}!')
                return redirect('judge_dashboard_anonymous', judge_token=judge_token)
    else:
        form = TeamScoreForm(judge=judge, team=team)

    context = {
        'form': form,
        'team': team,
        'judge': judge,
        'judge_token': judge_token,
        'is_anonymous': True,
    }
    return render(request, 'judging/judge_team.html', context)

def admin_results_anonymous(request, admin_token=None):
    """Anonymous admin results - accessible to all judges or specific admin token"""
    # Check if it's a valid admin token or any judge token
    valid_access = False
    judge_name = "Administrator"
    
    if admin_token:
        if admin_token == "all-judges":
            # Master link for all judges
            valid_access = True
            judge_name = "All Judges View"
        else:
            # Check if it's a valid judge token
            try:
                judge = Judge.objects.get(unique_token=admin_token)
                valid_access = True
                judge_name = f"{judge.user.get_full_name()} (Results View)"
            except Judge.DoesNotExist:
                pass
    
    if not valid_access:
        messages.error(request, 'Invalid results link. Please contact the administrator.')
        return render(request, 'judging/invalid_link.html')

    # Same results logic as your existing admin_results function
    teams_with_scores = (
        TeamFinalScore.objects
        .select_related('team')
        .order_by('-final_weighted_score')
    )

    # Update ranks
    for idx, tfs in enumerate(teams_with_scores, 1):
        if tfs.rank != idx:
            tfs.rank = idx
            tfs.save(update_fields=['rank'])

    # Per-criterion averages
    criteria_qs = JudgingCriteria.objects.all()
    team_crit_avg = defaultdict(dict)

    for crit in criteria_qs:
        for row in (Score.objects
                    .filter(criteria=crit)
                    .values('submission__team')
                    .annotate(avg=Avg('score'))):
            team_id = row['submission__team']
            team_crit_avg[team_id][crit.name] = float(row['avg'])

    for t_id in team_crit_avg:
        for crit in criteria_qs:
            team_crit_avg[t_id].setdefault(crit.name, 0)

    # Pack teams_json
    teams_json = []
    for tfs in teams_with_scores:
        team_scores = team_crit_avg.get(tfs.team.id, {})
        scores_dict = {}
        for crit in criteria_qs:
            scores_dict[crit.name] = team_scores.get(crit.name, 0)
        
        teams_json.append({
            'team': tfs.team.name,
            'final_weighted_score': float(tfs.final_weighted_score),
            'rank': tfs.rank,
            'scores': scores_dict,
            'members': getattr(tfs.team, 'members', 'Team Members'),
            'description': getattr(tfs.team, 'description', ''),
            'presentation_link': getattr(tfs.team, 'presentation_link', ''),
        })

    # Raw scores
    all_scores = list(
        Score.objects.values(
            'criteria__name',
            'submission__team__name',
            'submission__judge__id',
            'score'
        )
    )

    context = {
        'teams_with_scores': teams_with_scores,
        'total_submissions': Submission.objects.count(),
        'total_judges': Judge.objects.count(),
        'criteria_labels': json.dumps([c.name for c in criteria_qs]),
        'teams_json': json.dumps(teams_json, cls=DjangoJSONEncoder),
        'all_scores_json': json.dumps(all_scores, cls=DjangoJSONEncoder),
        'is_anonymous': True,
        'viewer_name': judge_name,
    }
    
    return render(request, 'judging/admin_results.html', context)

def generate_judge_links(request):
    """Admin utility to generate and display all judge links"""
    if not request.user.is_staff:
        return redirect('admin:index')
    
    judges = Judge.objects.all()
    
    # Generate master results link
    master_results_url = request.build_absolute_uri(f'/results/all-judges/')
    
    judge_links = []
    for judge in judges:
        judge_links.append({
            'judge': judge,
            'dashboard_url': request.build_absolute_uri(f'/judge/{judge.unique_token}/'),
            'results_url': request.build_absolute_uri(f'/results/{judge.unique_token}/'),
        })
    
    context = {
        'judge_links': judge_links,
        'master_results_url': master_results_url,
    }
    
    return render(request, 'judging/judge_links.html', context)

def home_anonymous(request):
    """Simple home page for anonymous users"""
    return render(request, 'judging/home_anonymous.html')
