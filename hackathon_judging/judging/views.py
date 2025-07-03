from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import transaction
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
from django.db.models import Avg, Count, Sum, Q
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required

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
            'team': tfs.team.name,                                    
            'final_weighted_score': float(tfs.final_weighted_score), 
            'rank': tfs.rank,                                        
            'scores': scores_dict,                                  
            'members': getattr(tfs.team, 'members', 'Team Members'), 
            'description': getattr(tfs.team, 'description', ''),    
            'presentation_link': getattr(tfs.team, 'presentation_link', ''), 
        })

  
    all_scores = list(
        Score.objects.values(
            'criteria__name',         
            'submission__team__name',  # e.g. "QBits"
            'submission__judge__id',   # judge id (int)
            'score'                
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

# def judge_team_anonymous(request, judge_token, team_id):
#     """Anonymous team judging using unique token"""
#     try:
#         judge = get_object_or_404(Judge, unique_token=judge_token)
#         team = get_object_or_404(Team, id=team_id)
#     except:
#         messages.error(request, 'Invalid link. Please contact the administrator.')
#         return redirect('home_anonymous')

#     if Submission.objects.filter(judge=judge, team=team).exists():
#         messages.warning(request, f'You have already judged {team.name}.')
#         return redirect('judge_dashboard_anonymous', judge_token=judge_token)

#     if request.method == 'POST':
#         form = TeamScoreForm(request.POST, judge=judge, team=team)
#         if form.is_valid():
#             with transaction.atomic():
#                 submission = Submission.objects.create(
#                     judge=judge,
#                     team=team,
#                     comments=form.cleaned_data.get('comments', '')
#                 )

#                 # Save scores
#                 for key in form.cleaned_data:
#                     if key.startswith("score_"):
#                         criterion_id = key.split("_")[1]
#                         criterion = get_object_or_404(JudgingCriteria, id=criterion_id)
#                         score_value = form.cleaned_data.get(key)
#                         score_comment = form.cleaned_data.get(f'comment_{criterion_id}', '')

#                         if score_value:
#                             Score.objects.create(
#                                 submission=submission,
#                                 criteria=criterion,
#                                 score=score_value,
#                                 comments=score_comment
#                             )

#                 update_team_final_scores(team)
#                 messages.success(request, f'Successfully submitted judgment for {team.name}!')
#                 return redirect('judge_dashboard_anonymous', judge_token=judge_token)
#     else:
#         form = TeamScoreForm(judge=judge, team=team)

#     context = {
#         'form': form,
#         'team': team,
#         'judge': judge,
#         'judge_token': judge_token,
#         'is_anonymous': True,
#     }
#     return render(request, 'judging/judge_team.html', context)

def judge_team_anonymous(request, judge_token, team_id):
    """Anonymous team judging with role-based criteria - FIXED VERSION"""
    try:
        judge = get_object_or_404(Judge, unique_token=judge_token)
        team = get_object_or_404(Team, id=team_id)
    except:
        messages.error(request, 'Invalid link. Please contact the administrator.')
        return redirect('home_anonymous')

    # Check if already judged
    if Submission.objects.filter(judge=judge, team=team).exists():
        messages.warning(request, f'You have already judged {team.name}.')
        return redirect('judge_dashboard_anonymous', judge_token=judge_token)

    if request.method == 'POST':
        # Debug: Print POST data
        print(f"DEBUG: POST data received: {request.POST}")
        
        # Use the correct form based on your template
        # Since your template shows hardcoded criteria names, let's handle them directly
        try:
            with transaction.atomic():
                # Extract scores from the hardcoded form fields in your template
                quantum_relevance = request.POST.get('quantum_relevance')
                quantum_quality = request.POST.get('quantum_quality') 
                social_impact = request.POST.get('social_impact')
                presentation = request.POST.get('presentation')
                
                # Validate all required scores are present
                if not all([quantum_relevance, quantum_quality, social_impact, presentation]):
                    messages.error(request, 'Please fill in all score fields.')
                    context = {
                        'team': team,
                        'judge': judge,
                        'judge_token': judge_token,
                        'is_anonymous': True,
                    }
                    return render(request, 'judging/judge_team.html', context)
                
                # Create submission
                submission = Submission.objects.create(
                    judge=judge,
                    team=team,
                    comments=request.POST.get('comments', '')
                )
                
                print(f"DEBUG: Created submission with ID: {submission.id}")

                # Create scores for each criteria based on your hardcoded criteria
                # You'll need to map these to your actual JudgingCriteria objects
                criteria_mapping = {
                    'quantum_relevance': 'Quantum Computing Relevance',
                    'quantum_quality': 'Quantum Computing Quality', 
                    'social_impact': 'Social Impact Based on the SDGs',
                    'presentation': 'Presentation and Originality'
                }
                
                for field_name, criteria_name in criteria_mapping.items():
                    score_value = request.POST.get(field_name)
                    comment_value = request.POST.get(f'comment_{field_name}', '')
                    
                    if score_value:
                        try:
                            # Get or create the criteria (adjust this based on your actual criteria setup)
                            criteria = JudgingCriteria.objects.get(name=criteria_name)
                            
                            Score.objects.create(
                                submission=submission,
                                criteria=criteria,
                                score=int(score_value),
                                comments=comment_value
                            )
                            print(f"DEBUG: Created score for {criteria_name}: {score_value}")
                            
                        except JudgingCriteria.DoesNotExist:
                            print(f"WARNING: Criteria '{criteria_name}' not found")
                            continue
                        except ValueError:
                            print(f"ERROR: Invalid score value for {criteria_name}: {score_value}")
                            continue

                # Update team final scores
                update_team_final_scores(team)
                
                print(f"DEBUG: Successfully processed judgment for team {team.name}")
                messages.success(request, f'Successfully submitted judgment for {team.name}!')
                
                # CRITICAL: Make sure this redirect happens and is the last statement
                return redirect('judge_dashboard_anonymous', judge_token=judge_token)
                
        except Exception as e:
            print(f"ERROR: Exception during submission: {str(e)}")
            messages.error(request, f'Error submitting judgment: {str(e)}')
            # Fall through to render the form again

    # GET request or form error - show the form
    context = {
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
        'public_judge_url': request.build_absolute_uri('/public-judge/'),
    }
    
    return render(request, 'judging/judge_links.html', context)

def home_anonymous(request):
    """Simple home page for anonymous users"""
    return render(request, 'judging/home_anonymous.html')


def judge_dashboard_anonymous(request, judge_token):
    """Anonymous judge dashboard with role-based criteria"""
    try:
        judge = get_object_or_404(Judge, unique_token=judge_token)
    except:
        messages.error(request, 'Invalid or expired judge link. Please contact the administrator.')
        return render(request, 'judging/invalid_link.html')
    
    teams = Team.objects.all()
    judged_teams = Submission.objects.filter(judge=judge).values_list('team_id', flat=True)
    
    # Get criteria this judge can evaluate
    allowed_criteria = judge.get_allowed_criteria()
    
    context = {
        'judge': judge,
        'teams': teams,
        'judged_teams': judged_teams,
        'total_teams': teams.count(),
        'completed_judgments': len(judged_teams),
        'remaining_teams': teams.count() - len(judged_teams),
        'is_anonymous': True,
        'judge_token': judge_token,
        'allowed_criteria': allowed_criteria,
        'judge_type': judge.judge_type,
    }
    return render(request, 'judging/dashboard.html', context)


def get_client_ip(request):
    """Get the client's IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def public_judge_team(request, team_id):
    """
    Handle public judging - CORRECT CRITERIA MAPPING
    """
    team = get_object_or_404(Team, id=team_id)
    voter_ip = get_client_ip(request)
    
    # Check if this IP has already voted for this team
    existing_vote = PublicJudgment.objects.filter(team=team, voter_ip=voter_ip).first()
    
    if existing_vote:
        messages.info(request, f'You have already voted for {team.name}. Thank you for your participation!')
        return redirect('public_judge_access')
    
    if request.method == 'POST':
        try:
            # Extract scores using EXACT field names from your template
            quantum_relevance = request.POST.get('quantum_relevance')          # 35%
            quantum_quality = request.POST.get('quantum_quality')              # 25%  
            social_impact = request.POST.get('social_impact')                  # 25%
            presentation = request.POST.get('presentation')                    # 15%
            
            # Check if all required fields are present
            if not all([quantum_relevance, quantum_quality, social_impact, presentation]):
                messages.error(request, 'Please fill in all scoring criteria.')
                return render(request, 'judging/public_judge_team.html', {'team': team})
            
            # Convert to floats and validate
            quantum_relevance = float(quantum_relevance)
            quantum_quality = float(quantum_quality)
            social_impact = float(social_impact)
            presentation = float(presentation)
            
            # Validate scores are in range
            scores = [quantum_relevance, quantum_quality, social_impact, presentation]
            if not all(1 <= score <= 5 for score in scores):
                messages.error(request, 'All scores must be between 1 and 5.')
                return render(request, 'judging/public_judge_team.html', {'team': team})
            
            # Create the public judgment with CORRECT mapping
            # NOTE: We need to map the NEW criteria to the existing PublicJudgment fields
            public_judgment = PublicJudgment.objects.create(
                team=team,
                # Map NEW criteria to existing model fields:
                quantum_tech_quality=quantum_quality,      # "Quantum Computing Quality" (25%)
                social_impact=social_impact,               # "Social Impact Based on the SDGs" (25%)
                innovation=quantum_relevance,              # "Quantum Computing Relevance" (35%) -> use innovation field
                presentation=presentation,                 # "Presentation and Originality" (15%)
                business_viability=3,                      # Not used in new criteria, set default
                
                # Comments mapping
                comments=request.POST.get('comments', '').strip(),
                comment_quantum_tech=request.POST.get('comment_quantum_quality', '').strip(),
                comment_social_impact=request.POST.get('comment_social_impact', '').strip(),
                comment_innovation=request.POST.get('comment_quantum_relevance', '').strip(),  # Map relevance comment to innovation
                comment_presentation=request.POST.get('comment_presentation', '').strip(),
                comment_business_viability='',  # Not used
                
                # Tracking fields
                voter_ip=voter_ip,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                voter_email=request.POST.get('voter_email', '').strip(),
                voter_name=request.POST.get('voter_name', '').strip()
            )
            
            # Calculate and show the score
            weighted_score = public_judgment.weighted_score
            
            print(f"DEBUG: Created public judgment with weighted score: {weighted_score}")
            print(f"DEBUG: Scores - Relevance: {quantum_relevance}, Quality: {quantum_quality}, Impact: {social_impact}, Presentation: {presentation}")
            
            # Success message with score rounded to 2 decimal places
            messages.success(
                request, 
                f'✅ Thank you for judging {team.name}! Your vote has been recorded. '
                f'Your weighted score: {weighted_score:.2f}/5.0'
            )
            
            # Redirect back to dashboard to continue judging
            return redirect('public_judge_access')
            
        except (ValueError, TypeError) as e:
            print(f"DEBUG: Error converting scores: {e}")
            messages.error(request, 'Please fill in all required fields with valid scores (1-5).')
            return render(request, 'judging/public_judge_team.html', {'team': team})
            
        except IntegrityError as e:
            print(f"DEBUG: Duplicate vote attempt: {e}")
            messages.warning(request, f'You have already voted for {team.name}. Thank you!')
            return redirect('public_judge_access')
            
        except Exception as e:
            print(f"DEBUG: Unexpected error: {e}")
            messages.error(request, f'An error occurred while submitting your vote: {str(e)}')
            return render(request, 'judging/public_judge_team.html', {'team': team})
    
    # GET request - show the judging form
    context = {
        'team': team,
    }
    return render(request, 'judging/public_judge_team.html', context)

def public_judge_access(request):
    """
    Public judge dashboard showing teams and progress
    """
    teams = Team.objects.all().order_by('name')
    voter_ip = get_client_ip(request)
    
    # Get teams this IP has already judged
    judged_teams = PublicJudgment.objects.filter(voter_ip=voter_ip).values_list('team_id', flat=True)
    
    # Debug: Print what we found
    print(f"DEBUG: Found {len(judged_teams)} votes for IP {voter_ip}")
    print(f"DEBUG: Judged teams: {list(judged_teams)}")
    
    # Calculate statistics
    total_teams = teams.count()
    completed_judgments = len(judged_teams)
    remaining_teams = total_teams - completed_judgments
    
    context = {
        'teams': teams,
        'judged_teams': list(judged_teams),
        'total_teams': total_teams,
        'completed_judgments': completed_judgments,
        'remaining_teams': remaining_teams,
    }
    return render(request, 'judging/public_judge_access.html', context)

def public_voting_results(request):
    """
    Display public voting results - accessible to everyone
    """
    # Get all teams with public judgments
    teams_with_public_votes = Team.objects.filter(
        publicjudgment__isnull=False
    ).distinct().annotate(
        # Count public votes
        public_vote_count=Count('publicjudgment'),
        
        # Average scores for each criteria - FIXED COLUMN NAMES
        avg_quantum_tech=Avg('publicjudgment__quantum_tech_quality'),
        avg_social_impact=Avg('publicjudgment__social_impact'), 
        avg_innovation=Avg('publicjudgment__innovation'),
        avg_presentation=Avg('publicjudgment__presentation'),
        avg_business_viability=Avg('publicjudgment__business_viability'),
    ).order_by('-public_vote_count')
    
    # Calculate weighted scores for each team
    teams_data = []
    for team in teams_with_public_votes:
        if team.avg_quantum_tech is not None:  # Only include teams with votes
            weighted_score = (
                (team.avg_quantum_tech or 0) * 0.40 +
                (team.avg_social_impact or 0) * 0.25 +
                (team.avg_innovation or 0) * 0.20 +
                (team.avg_presentation or 0) * 0.10 +
                (team.avg_business_viability or 0) * 0.05
            )
            
            teams_data.append({
                'team': team,
                'public_vote_count': team.public_vote_count,
                'avg_quantum_tech': round(team.avg_quantum_tech, 2) if team.avg_quantum_tech else 0,
                'avg_social_impact': round(team.avg_social_impact, 2) if team.avg_social_impact else 0,
                'avg_innovation': round(team.avg_innovation, 2) if team.avg_innovation else 0,
                'avg_presentation': round(team.avg_presentation, 2) if team.avg_presentation else 0,
                'avg_business_viability': round(team.avg_business_viability, 2) if team.avg_business_viability else 0,
                'weighted_score': round(weighted_score, 2),
            })
    
    # Sort by weighted score (highest first)
    teams_data.sort(key=lambda x: x['weighted_score'], reverse=True)
    
    # Add rankings
    for i, team_data in enumerate(teams_data, 1):
        team_data['rank'] = i
    
    # Get total public votes cast
    total_public_votes = PublicJudgment.objects.count()
    
    # Statistics for charts
    vote_distribution = []
    for team_data in teams_data:
        vote_distribution.append({
            'team_name': team_data['team'].name,
            'vote_count': team_data['public_vote_count'],
            'weighted_score': team_data['weighted_score']
        })
    
    context = {
        'teams_data': teams_data,
        'total_teams': len(teams_data),
        'total_public_votes': total_public_votes,
        'vote_distribution_json': json.dumps(vote_distribution),
        'page_title': 'Public Voting Results',
    }
    
    return render(request, 'judging/public_results.html', context)


@staff_member_required
def admin_public_voting_results(request):
    """
    Admin view for public voting results with detailed analytics
    """
    # Get all public judgments for detailed analysis
    public_judgments = PublicJudgment.objects.select_related('team').all()
    
    # Get teams with detailed public voting stats - FIXED COLUMN NAMES
    teams_with_public_votes = Team.objects.filter(
        publicjudgment__isnull=False
    ).distinct().annotate(
        public_vote_count=Count('publicjudgment'),
        avg_quantum_tech=Avg('publicjudgment__quantum_tech_quality'),
        avg_social_impact=Avg('publicjudgment__social_impact'), 
        avg_innovation=Avg('publicjudgment__innovation'),
        avg_presentation=Avg('publicjudgment__presentation'),
        avg_business_viability=Avg('publicjudgment__business_viability'),
    ).order_by('-public_vote_count')
    
    # Calculate detailed statistics
    teams_data = []
    for team in teams_with_public_votes:
        if team.avg_quantum_tech is not None:
            weighted_score = (
                (team.avg_quantum_tech or 0) * 0.40 +
                (team.avg_social_impact or 0) * 0.25 +
                (team.avg_innovation or 0) * 0.20 +
                (team.avg_presentation or 0) * 0.10 +
                (team.avg_business_viability or 0) * 0.05
            )
            
            # Get individual votes for this team for detailed analysis
            team_votes = PublicJudgment.objects.filter(team=team)
            
            teams_data.append({
                'team': team,
                'public_vote_count': team.public_vote_count,
                'avg_quantum_tech': round(team.avg_quantum_tech, 2) if team.avg_quantum_tech else 0,
                'avg_social_impact': round(team.avg_social_impact, 2) if team.avg_social_impact else 0,
                'avg_innovation': round(team.avg_innovation, 2) if team.avg_innovation else 0,
                'avg_presentation': round(team.avg_presentation, 2) if team.avg_presentation else 0,
                'avg_business_viability': round(team.avg_business_viability, 2) if team.avg_business_viability else 0,
                'weighted_score': round(weighted_score, 2),
                'votes': team_votes,
            })
    
    # Sort by weighted score
    teams_data.sort(key=lambda x: x['weighted_score'], reverse=True)
    
    # Add rankings
    for i, team_data in enumerate(teams_data, 1):
        team_data['rank'] = i
    
    # Additional admin statistics
    total_public_votes = PublicJudgment.objects.count()
    teams_without_votes = Team.objects.filter(publicjudgment__isnull=True).count()
    
    # Voting patterns analysis - FIXED COLUMN NAMES
    criteria_averages = {
        'quantum_tech': PublicJudgment.objects.aggregate(avg=Avg('quantum_tech_quality'))['avg'],
        'social_impact': PublicJudgment.objects.aggregate(avg=Avg('social_impact'))['avg'],
        'innovation': PublicJudgment.objects.aggregate(avg=Avg('innovation'))['avg'],
        'presentation': PublicJudgment.objects.aggregate(avg=Avg('presentation'))['avg'],
        'business_viability': PublicJudgment.objects.aggregate(avg=Avg('business_viability'))['avg'],
    }
    
    context = {
        'teams_data': teams_data,
        'total_teams': len(teams_data),
        'total_public_votes': total_public_votes,
        'teams_without_votes': teams_without_votes,
        'criteria_averages': criteria_averages,
        'public_judgments': public_judgments,
        'page_title': 'Admin: Public Voting Results',
        'is_admin_view': True,
    }
    
    return render(request, 'judging/admin_public_results.html', context)


def judge_team_anonymous(request, judge_token, team_id):
    """Anonymous team judging with CORRECT NEW criteria mapping"""
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
        try:
            # Extract scores using EXACT field names from template
            quantum_relevance = request.POST.get('quantum_relevance')
            quantum_quality = request.POST.get('quantum_quality')
            social_impact = request.POST.get('social_impact')
            presentation = request.POST.get('presentation')
            
            # Validate all scores present
            if not all([quantum_relevance, quantum_quality, social_impact, presentation]):
                messages.error(request, 'Please fill in all score fields.')
                context = {
                    'team': team,
                    'judge': judge,
                    'judge_token': judge_token,
                    'is_anonymous': True,
                }
                return render(request, 'judging/judge_team.html', context)
            
            # Convert and validate as floats
            scores = {
                'quantum_relevance': float(quantum_relevance),
                'quantum_quality': float(quantum_quality),
                'social_impact': float(social_impact),
                'presentation': float(presentation)
            }
            
            for field, score in scores.items():
                if not (1 <= score <= 5):
                    messages.error(request, f'All scores must be between 1 and 5.')
                    context = {
                        'team': team,
                        'judge': judge,
                        'judge_token': judge_token,
                        'is_anonymous': True,
                    }
                    return render(request, 'judging/judge_team.html', context)
            
            with transaction.atomic():
                submission = Submission.objects.create(
                    judge=judge,
                    team=team,
                    comments=request.POST.get('comments', '')
                )

                # Map template fields to CORRECT database criteria names
                criteria_mapping = {
                    'quantum_relevance': 'Quantum Computing Relevance',        # 35%
                    'quantum_quality': 'Quantum Computing Quality',            # 25%
                    'social_impact': 'Social Impact Based on the SDGs',        # 25%
                    'presentation': 'Presentation and Originality'             # 15%
                }
                
                scores_created = 0
                for field_name, criteria_name in criteria_mapping.items():
                    try:
                        criteria = JudgingCriteria.objects.get(name=criteria_name)
                        score_value = scores[field_name]
                        comment_value = request.POST.get(f'comment_{field_name}', '')
                        
                        Score.objects.create(
                            submission=submission,
                            criteria=criteria,
                            score=score_value,
                            comments=comment_value
                        )
                        scores_created += 1
                        print(f"DEBUG: Created score for {criteria_name}: {score_value}")
                        
                    except JudgingCriteria.DoesNotExist:
                        print(f"ERROR: Criteria '{criteria_name}' not found")
                        available = list(JudgingCriteria.objects.values_list('name', flat=True))
                        print(f"Available criteria: {available}")
                        continue

                if scores_created > 0:
                    update_team_final_scores(team)
                    messages.success(request, f'Successfully submitted judgment for {team.name}!')
                    return redirect('judge_dashboard_anonymous', judge_token=judge_token)
                else:
                    messages.error(request, 'No scores were saved. Please contact administrator.')
                    
        except Exception as e:
            print(f"ERROR: {e}")
            messages.error(request, f'Error submitting judgment: {str(e)}')

    context = {
        'team': team,
        'judge': judge,
        'judge_token': judge_token,
        'is_anonymous': True,
    }
    return render(request, 'judging/judge_team.html', context)


def update_team_final_scores(team):
    """Update team scores with CORRECT NEW criteria mapping"""
    final_score, created = TeamFinalScore.objects.get_or_create(team=team)
    
    # Calculate average scores for each criteria
    criteria_scores = {}
    for criteria in JudgingCriteria.objects.all():
        avg_score = Score.objects.filter(
            submission__team=team, 
            criteria=criteria
        ).aggregate(avg=Avg('score'))['avg'] or 0
        criteria_scores[criteria.name] = avg_score
    
    # Map CORRECT NEW criteria to existing model fields
    final_score.quantum_tech_score = criteria_scores.get('Quantum Computing Quality', 0)        # 25%
    final_score.social_impact_score = criteria_scores.get('Social Impact Based on the SDGs', 0) # 25%
    final_score.innovation_score = criteria_scores.get('Quantum Computing Relevance', 0)        # 35% -> use innovation field
    final_score.presentation_score = criteria_scores.get('Presentation and Originality', 0)     # 15%
    final_score.business_viability_score = 0  # Not used in new criteria
    
    final_score.calculate_final_score()


def calculate_final_score(self):
    """Calculate weighted final score using CORRECT NEW criteria weights"""
    # Map to NEW weights:
    # innovation_score = Quantum Computing Relevance (35%)
    # quantum_tech_score = Quantum Computing Quality (25%)  
    # social_impact_score = Social Impact Based on the SDGs (25%)
    # presentation_score = Presentation and Originality (15%)
    
    self.final_weighted_score = (
        (self.innovation_score * 0.35) +        # Quantum Computing Relevance 35%
        (self.quantum_tech_score * 0.25) +      # Quantum Computing Quality 25%
        (self.social_impact_score * 0.25) +     # Social Impact Based on the SDGs 25%
        (self.presentation_score * 0.15)        # Presentation and Originality 15%
        # business_viability_score * 0.00 (not used)
    )
    self.save()
    return self.final_weighted_score

def update_team_final_scores(team):
    """Update calculated scores for a team - FIXED FOR NEW CRITERIA"""
    print(f"🔄 DEBUG: Updating final scores for team {team.name}")
    
    final_score, created = TeamFinalScore.objects.get_or_create(team=team)
    if created:
        print(f"✅ DEBUG: Created new TeamFinalScore for {team.name}")
    else:
        print(f"🔄 DEBUG: Updating existing TeamFinalScore for {team.name}")
    
    # Calculate average scores for each NEW criteria
    criteria_scores = {}
    for criteria in JudgingCriteria.objects.all():
        avg_score = Score.objects.filter(
            submission__team=team, 
            criteria=criteria
        ).aggregate(avg=Avg('score'))['avg'] or 0
        criteria_scores[criteria.name] = avg_score
        print(f"📊 DEBUG: {criteria.name}: avg={avg_score:.2f}")
    
    # Map NEW criteria names to model fields
    final_score.quantum_tech_score = criteria_scores.get('Quantum Computing Quality', 0)
    final_score.social_impact_score = criteria_scores.get('Social Impact Based on the SDGs', 0)
    final_score.innovation_score = criteria_scores.get('Quantum Computing Relevance', 0)  # Map relevance to innovation field
    final_score.presentation_score = criteria_scores.get('Presentation and Originality', 0)
    final_score.business_viability_score = 0  # Not used in new criteria
    
    # Calculate and save final weighted score
    old_score = final_score.final_weighted_score
    final_score.calculate_final_score()
    
    print(f"📊 DEBUG: Final weighted score: {old_score} → {final_score.final_weighted_score}")
    print(f"✅ DEBUG: Updated final scores for {team.name}")

# Update these functions in your views.py

def public_voting_results(request):
    """Display public voting results with proper rounding"""
    teams_with_public_votes = Team.objects.filter(
        publicjudgment__isnull=False
    ).distinct().annotate(
        public_vote_count=Count('publicjudgment'),
        avg_quantum_tech=Avg('publicjudgment__quantum_tech_quality'),
        avg_social_impact=Avg('publicjudgment__social_impact'), 
        avg_innovation=Avg('publicjudgment__innovation'),
        avg_presentation=Avg('publicjudgment__presentation'),
        avg_business_viability=Avg('publicjudgment__business_viability'),
    ).order_by('-public_vote_count')
    
    teams_data = []
    for team in teams_with_public_votes:
        if team.avg_quantum_tech is not None:
            # Calculate weighted score using float precision
            weighted_score = (
                (team.avg_innovation or 0) * 0.35 +           # Quantum Computing Relevance 35%
                (team.avg_quantum_tech or 0) * 0.25 +         # Quantum Computing Quality 25%
                (team.avg_social_impact or 0) * 0.25 +        # Social Impact Based on SDGs 25%
                (team.avg_presentation or 0) * 0.15           # Presentation and Originality 15%
            )
            
            teams_data.append({
                'team': team,
                'public_vote_count': team.public_vote_count,
                # Round to 2 decimal places for display
                'avg_quantum_relevance': round(team.avg_innovation, 2) if team.avg_innovation else 0,
                'avg_quantum_quality': round(team.avg_quantum_tech, 2) if team.avg_quantum_tech else 0,
                'avg_social_impact': round(team.avg_social_impact, 2) if team.avg_social_impact else 0,
                'avg_presentation': round(team.avg_presentation, 2) if team.avg_presentation else 0,
                'weighted_score': round(weighted_score, 2),
            })
    
    # Sort by weighted score (highest first)
    teams_data.sort(key=lambda x: x['weighted_score'], reverse=True)
    
    # Add rankings
    for i, team_data in enumerate(teams_data, 1):
        team_data['rank'] = i
    
    total_public_votes = PublicJudgment.objects.count()
    
    vote_distribution = []
    for team_data in teams_data:
        vote_distribution.append({
            'team_name': team_data['team'].name,
            'vote_count': team_data['public_vote_count'],
            'weighted_score': team_data['weighted_score']
        })
    
    context = {
        'teams_data': teams_data,
        'total_teams': len(teams_data),
        'total_public_votes': total_public_votes,
        'vote_distribution_json': json.dumps(vote_distribution),
        'page_title': 'Public Voting Results',
    }
    
    return render(request, 'judging/public_results.html', context)



def judge_team(request, team_id):
    """Judge a specific team - AUTHENTICATED VERSION WITH NEW CRITERIA"""
    if not request.user.is_authenticated:
        return redirect('judge_login')

    judge = get_object_or_404(Judge, user=request.user)
    team = get_object_or_404(Team, id=team_id)

    if Submission.objects.filter(judge=judge, team=team).exists():
        messages.warning(request, f'You have already judged {team.name}.')
        return redirect('judge_dashboard')

    # Get criteria this judge can evaluate
    allowed_criteria = judge.get_allowed_criteria()

    if request.method == 'POST':
        try:
            with transaction.atomic():
                submission = Submission.objects.create(
                    judge=judge,
                    team=team,
                    comments=request.POST.get('comments', '')
                )

                # Handle NEW criteria with template field names
                criteria_mapping = {
                    'quantum_relevance': 'Quantum Computing Relevance',
                    'quantum_quality': 'Quantum Computing Quality',
                    'social_impact': 'Social Impact Based on the SDGs',
                    'presentation': 'Presentation and Originality'
                }
                
                scores_created = 0
                for field_name, criteria_name in criteria_mapping.items():
                    score_value = request.POST.get(field_name)
                    comment_value = request.POST.get(f'comment_{field_name}', '')
                    
                    if score_value:
                        try:
                            criteria = JudgingCriteria.objects.get(name=criteria_name)
                            Score.objects.create(
                                submission=submission,
                                criteria=criteria,
                                score=int(score_value),
                                comments=comment_value
                            )
                            scores_created += 1
                        except JudgingCriteria.DoesNotExist:
                            print(f"Warning: Criteria '{criteria_name}' not found")
                            continue

                if scores_created > 0:
                    update_team_final_scores(team)
                    messages.success(request, f'Successfully submitted judgment for {team.name}!')
                    return redirect('judge_dashboard')
                else:
                    messages.error(request, 'No scores were submitted. Please fill in at least one score.')
                    
        except Exception as e:
            messages.error(request, f'Error submitting judgment: {str(e)}')

    context = {
        'team': team,
        'judge': judge,
        'allowed_criteria': allowed_criteria,
    }
    return render(request, 'judging/judge_team.html', context)


def admin_results(request):
    if not request.user.is_authenticated:
        return redirect('judge_login')

    if not (request.user.is_staff or hasattr(request.user, 'judge')):
        messages.error(request, "You don't have permission to view results.")
        return redirect('judge_dashboard')

    # Get teams with final scores
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

    # Get NEW criteria and calculate per-team averages
    criteria_qs = JudgingCriteria.objects.all()
    team_crit_avg = defaultdict(dict)

    for crit in criteria_qs:
        for row in (Score.objects
                    .filter(criteria=crit)
                    .values('submission__team')
                    .annotate(avg=Avg('score'))):
            team_id = row['submission__team']
            team_crit_avg[team_id][crit.name] = float(row['avg'])

    # Fill in missing criteria with 0
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
            'scores': scores_dict,  # This should match criteriaLbl exactly
            'members': getattr(tfs.team, 'members', 'Team Members'),
            'description': getattr(tfs.team, 'description', ''),
            'presentation_link': getattr(tfs.team, 'presentation_link', ''),
        })

    # Raw scores for charts
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
    }
    
    return render(request, 'judging/admin_results.html', context)