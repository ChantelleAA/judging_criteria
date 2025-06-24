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
    quantum_tech_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    social_impact_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    innovation_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    presentation_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    business_viability_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    final_weighted_score = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    rank = models.IntegerField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    def calculate_final_score(self):
        """Calculate weighted final score"""
        # Weights: Quantum Tech (40%), Social Impact (25%), Innovation (20%), 
        # Presentation (10%), Business Viability (5%)
        self.final_weighted_score = (
            (self.quantum_tech_score * 0.40) +
            (self.social_impact_score * 0.25) +
            (self.innovation_score * 0.20) +
            (self.presentation_score * 0.10) +
            (self.business_viability_score * 0.05)
        )
        self.save()
        return self.final_weighted_score
    
    def __str__(self):
        return f"{self.team.name} - Final Score: {self.final_weighted_score}"
    


class PublicJudgment(models.Model):
    """
    Model for storing public votes from community members
    """
    team = models.ForeignKey('Team', on_delete=models.CASCADE)
    
    # Scoring criteria (1-5 scale, same as judge criteria)
    quantum_tech_quality = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Technical implementation and quantum concepts (40% weight)"
    )
    social_impact = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Potential to benefit society (25% weight)"
    )
    innovation = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Creativity and novelty of approach (20% weight)"
    )
    presentation = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="How well the idea is communicated (10% weight)"
    )
    business_viability = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Potential for real-world implementation (5% weight)"
    )
    
    # Optional comments
    comments = models.TextField(blank=True, null=True, help_text="Overall feedback")
    
    # Individual criteria comments (optional)
    comment_quantum_tech = models.TextField(blank=True, null=True)
    comment_social_impact = models.TextField(blank=True, null=True)
    comment_innovation = models.TextField(blank=True, null=True)
    comment_presentation = models.TextField(blank=True, null=True)
    comment_business_viability = models.TextField(blank=True, null=True)
    
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
            self.quantum_tech_quality * 0.40 +
            self.social_impact * 0.25 +
            self.innovation * 0.20 +
            self.presentation * 0.10 +
            self.business_viability * 0.05
        )
    
    @property
    def average_score(self):
        """Simple average of all criteria scores"""
        return (
            self.quantum_tech_quality +
            self.social_impact +
            self.innovation +
            self.presentation +
            self.business_viability
        ) / 5
    
    def get_criteria_scores(self):
        """Return all criteria scores as a dictionary"""
        return {
            'quantum_tech_quality': self.quantum_tech_quality,
            'social_impact': self.social_impact,
            'innovation': self.innovation,
            'presentation': self.presentation,
            'business_viability': self.business_viability,
        }
    
    def get_criteria_comments(self):
        """Return all criteria comments as a dictionary"""
        return {
            'quantum_tech': self.comment_quantum_tech,
            'social_impact': self.comment_social_impact,
            'innovation': self.comment_innovation,
            'presentation': self.comment_presentation,
            'business_viability': self.comment_business_viability,
        }