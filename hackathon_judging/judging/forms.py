# forms.py
from django import forms
from django.forms import formset_factory
from .models import *

class JudgeRegistrationForm(forms.ModelForm):
    """Form for registering judges"""
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    email = forms.EmailField()
    
    class Meta:
        model = Judge
        fields = ['expertise_areas']
        widgets = {
            'expertise_areas': forms.CheckboxSelectMultiple(),
        }

class TeamScoreForm(forms.Form):
    """Dynamic form for scoring teams based on judge expertise"""
    comments = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Optional comments about this team...'}),
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        judge = kwargs.pop('judge', None)
        team = kwargs.pop('team', None)
        super().__init__(*args, **kwargs)
        
        if judge:
            # Get criteria relevant to this judge's expertise
            judge_expertise = judge.expertise_areas.all()
            criteria = JudgingCriteria.objects.filter(
                expertise_areas__in=judge_expertise
            ).distinct()
            
            for criterion in criteria:
                field_name = f'score_{criterion.id}'
                self.fields[field_name] = forms.IntegerField(
                    label=f"{criterion.name} (Weight: {criterion.weight}%)",
                    min_value=1,
                    max_value=10,
                    widget=forms.NumberInput(attrs={
                        'class': 'form-control',
                        'placeholder': '1-10'
                    }),
                    help_text=criterion.description
                )
                
                # Add comments field for each criterion
                comment_field_name = f'comment_{criterion.id}'
                self.fields[comment_field_name] = forms.CharField(
                    label=f"Comments for {criterion.name}",
                    widget=forms.Textarea(attrs={
                        'rows': 2, 
                        'class': 'form-control',
                        'placeholder': f'Optional comments about {criterion.name}...'
                    }),
                    required=False
                )
