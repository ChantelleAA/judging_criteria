# models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
from django.utils import timezone

class JudgeExpertise(models.Model):
    """Different areas of expertise for judges"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

class JudgingCriteria(models.Model):
    """Criteria for judging with weights"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    weight = models.DecimalField(max_digits=5, decimal_places=2)  # e.g., 40.00 for 40%
    expertise_areas = models.ManyToManyField(JudgeExpertise, blank=True)
    guide_questions = models.TextField(
        blank=True,
        help_text="Optional guiding questions to assist judges in scoring this criterion"
    )
    
    class Meta:
        verbose_name_plural = "Judging Criteria"
    
    def __str__(self):
        return f"{self.name} ({self.weight}%)"

class Judge(models.Model):
    """Judge information and expertise"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    expertise_areas = models.ManyToManyField(JudgeExpertise)
    unique_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    has_submitted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    JUDGE_TYPE_CHOICES = [
    ('quantum_expert', 'Quantum Expert'),
    ('general_judge', 'General Judge'),
    ('public', 'Public Judge'),
]
    judge_type = models.CharField(
        max_length=20, 
        choices=JUDGE_TYPE_CHOICES, 
        default='general_judge',
        help_text="Determines which criteria this judge can evaluate"
    )
    

    def get_allowed_criteria(self):
        """Return criteria this judge can evaluate based on their type"""
        if self.judge_type == 'quantum_expert':
            # Quantum experts judge ALL criteria
            return JudgingCriteria.objects.all()
        elif self.judge_type == 'public':
            # Public judges ALL criteria  
            return JudgingCriteria.objects.all()
        else:
            # General judges: exclude quantum-specific criteria
            return JudgingCriteria.objects.exclude(
                name__in=['Quantum Tech Quality', 'Innovation']
            )
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.get_judge_type_display()})"

class Team(models.Model):
    """Teams participating in the hackathon"""
    name = models.CharField(max_length=200)
    description = models.TextField()
    presentation_link = models.URLField(blank=True)
    members = models.TextField(help_text="Comma-separated list of team members")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class Submission(models.Model):
    """Individual judge's submission for a team"""
    judge = models.ForeignKey(Judge, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    submitted_at = models.DateTimeField(auto_now_add=True)
    comments = models.TextField(blank=True)
    
    class Meta:
        unique_together = ('judge', 'team')  # Ensure one submission per judge per team
    
    def __str__(self):
        return f"{self.judge.user.get_full_name()} - {self.team.name}"

class Score(models.Model):
    """Individual scores for each criteria"""
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='scores')
    criteria = models.ForeignKey(JudgingCriteria, on_delete=models.CASCADE)
    score = models.IntegerField(
    validators=[MinValueValidator(1), MaxValueValidator(5)],
    help_text="Score from 1–5"
)
    comments = models.TextField(blank=True)
    
    class Meta:
        unique_together = ('submission', 'criteria')
    
    def __str__(self):
        return f"{self.submission.team.name} - {self.criteria.name}: {self.score}"


class TeamFinalScore(models.Model):
    """Calculated final scores for teams"""
    team = models.OneToOneField(Team, on_delete=models.CASCADE)
    quantum_computing_relevance = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    quantum_computing_quality = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    social_impact_based_on_sdgs = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    presentation_and_originality = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    final_weighted_score = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    rank = models.IntegerField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    def calculate_final_score(self):
        """Calculate weighted final score using NEW criteria field names"""
        self.final_weighted_score = (
            (self.quantum_computing_relevance * 0.35) +    # "Quantum Computing Relevance" 35%
            (self.quantum_computing_quality * 0.25) +      # "Quantum Computing Quality" 25%
            (self.social_impact_based_on_sdgs * 0.25) +    # "Social Impact Based on the SDGs" 25%
            (self.presentation_and_originality * 0.15)     # "Presentation and Originality" 15%
        )
        self.save()
        return self.final_weighted_score
    
    def has_any_scores(self):
        """Check if this team has received any judge scores"""
        return self.team.submission_set.exists()
    
    def get_score_breakdown(self):
        """Get detailed breakdown with CORRECT field names"""
        return {
            'quantum_computing_relevance': {
                'score': float(self.quantum_computing_relevance),
                'weight': 35,
                'weighted': float(self.quantum_computing_relevance * 0.35)
            },
            'quantum_computing_quality': {
                'score': float(self.quantum_computing_quality),
                'weight': 25,
                'weighted': float(self.quantum_computing_quality * 0.25)
            },
            'social_impact_based_on_sdgs': {
                'score': float(self.social_impact_based_on_sdgs),
                'weight': 25,
                'weighted': float(self.social_impact_based_on_sdgs * 0.25)
            },
            'presentation_and_originality': {
                'score': float(self.presentation_and_originality),
                'weight': 15,
                'weighted': float(self.presentation_and_originality * 0.15)
            },
            'final_weighted_score': float(self.final_weighted_score)
        }
    
    def get_judge_count(self):
        """Get number of judges who have scored this team"""
        return self.team.submission_set.count()
    
    def is_complete(self):
        """Check if team has been scored by at least one judge"""
        return self.has_any_scores() and self.final_weighted_score > 0
    
    class Meta:
        ordering = ['-final_weighted_score', 'team__name']
        verbose_name = "Team Final Score"
        verbose_name_plural = "Team Final Scores"
    
    def __str__(self):
        status = "✅" if self.is_complete() else "⏳"
        return f"{status} {self.team.name} - {self.final_weighted_score:.2f}/5.0 ({self.get_judge_count()} judges)"

class PublicJudgment(models.Model):
    """
    Model for storing public votes from community members
    """
    team = models.ForeignKey('Team', on_delete=models.CASCADE)
    
    # Scoring criteria (1-5 scale, same as judge criteria)
    quantum_computing_quality = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Technical implementation and quantum concepts (40% weight)"
    )
    social_impact_based_on_sdgs = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Potential to benefit society (25% weight)"
    )
    quantum_computing_relevance  = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Creativity and novelty of approach (20% weight)"
    )
    presentation_and_originality = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="How well the idea is communicated (10% weight)"
    )

    # Optional comments
    comments = models.TextField(blank=True, null=True, help_text="Overall feedback")
    
    # Individual criteria comments (optional)
    comment_quantum_computing_relevance = models.TextField(blank=True, null=True)
    comment_quantum_computing_quality = models.TextField(blank=True, null=True)
    comment_social_impact_based_on_sdgs = models.TextField(blank=True, null=True)
    comment_presentation_and_originality = models.TextField(blank=True, null=True)
    
    # Tracking fields
    voter_ip = models.GenericIPAddressField(help_text="IP address of the voter")
    user_agent = models.TextField(blank=True, null=True, help_text="Browser user agent")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Optional: If you want to track registered users vs anonymous
    voter_email = models.EmailField(blank=True, null=True, help_text="Optional email for verification")
    voter_name = models.CharField(max_length=100, blank=True, null=True, help_text="Optional name")
    
    class Meta:
        # Prevent duplicate votes from same IP for same team
        unique_together = ['team', 'voter_ip']
        ordering = ['-created_at']
        verbose_name = "Public Judgment"
        verbose_name_plural = "Public Judgments"
    
    def __str__(self):
        return f"Public vote for {self.team.name} from {self.voter_ip}"
    
    @property
    def weighted_score(self):
        """Calculate weighted score using the same weights as judge criteria"""
        return (
            self.quantum_computing_quality * 0.35 +
            self.social_impact_based_on_sdgs* 0.25 +
            self.quantum_computing_relevance* 0.25 +
            self.presentation_and_originality * 0.15 
        )
    
    @property
    def average_score(self):
        """Simple average of all criteria scores"""
        return (
            self.quantum_computing_quality +
            self.social_impact_based_on_sdgs+
            self.quantum_computing_relevance+
            self.presentation_and_originality
        ) / 5
    
    def get_criteria_scores(self):
        """Return all criteria scores as a dictionary"""
        return {
            'quantum_computing_quality': self.quantum_computing_quality,
            'social_impact_based_on_sdgs': self.social_impact_based_on_sdgs,
            'quantum_computing_relevance': self.quantum_computing_relevance,
            'presentation_and_originality': self.presentation_and_originality,
        }
    
    def get_criteria_comments(self):
        """Return all criteria comments as a dictionary"""
        return {
            'quantum_computing_quality': self.comment_quantum_computing_quality,
            'social_impact_based_on_sdgs': self.comment_social_impact_based_on_sdgs,
            'quantum_computing_relevance': self.comment_quantum_computing_relevance,
            'presentation_and_originality': self.comment_presentation_and_originality,
        }