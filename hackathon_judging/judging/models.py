# models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

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
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {', '.join([exp.name for exp in self.expertise_areas.all()])}"

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