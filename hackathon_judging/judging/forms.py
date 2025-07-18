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

from django import forms
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

    # Guide text for criteria
    CRITERIA_GUIDES = {
        'Quantum Tech Quality': "How well did the team apply quantum computing? Is the approach technically sound and complete?",
        'Social Impact': "How well does the project align with Sustainable Development Goals (SDGs)? Who benefits from this solution and how?",
        'Innovation': "How novel or creative is the idea? Does it stand out from typical solutions?",
        'Business Viability': "Can this project be developed into a sustainable business or scalable solution?",
        'Presentation': "Was the presentation clear and effective? Did all team members contribute? Was the communication engaging?"
    }

    def __init__(self, *args, **kwargs):
        judge = kwargs.pop('judge', None)
        team = kwargs.pop('team', None)
        super().__init__(*args, **kwargs)

        if judge:
            # Get areas of expertise
            judge_expertise = judge.expertise_areas.all()
            all_areas = [ea.name for ea in judge_expertise]
            quantum_keywords = ['Quantum', 'Computer Science', 'Engineering']

            # Determine if judge should score all or partial criteria
            is_technical_judge = any(
                any(keyword.lower() in area.lower() for keyword in quantum_keywords)
                for area in all_areas
            )

            if is_technical_judge:
                criteria = JudgingCriteria.objects.all()
            else:
                allowed_names = ['Social Impact', 'Business Viability', 'Presentation']
                criteria = JudgingCriteria.objects.filter(name__in=allowed_names)

            # Add form fields dynamically
            for criterion in criteria:
                field_name = f'score_{criterion.id}'
                guide_text = self.CRITERIA_GUIDES.get(criterion.name, criterion.description)

                self.fields[field_name] = forms.IntegerField(
                    label=f"{criterion.name} (Weight: {criterion.weight}%)",
                    min_value=1,
                    max_value=5,
                    widget=forms.NumberInput(attrs={
                        'class': 'form-control',
                        'placeholder': '1-5'
                    }),
                    help_text=guide_text
                )

                # Optional comment field per criterion
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



class RoleBasedTeamScoreForm(forms.Form):
    """Dynamic form based on judge's allowed criteria"""
    
    def __init__(self, *args, **kwargs):
        self.judge = kwargs.pop('judge')
        self.team = kwargs.pop('team')
        self.allowed_criteria = kwargs.pop('allowed_criteria')
        super().__init__(*args, **kwargs)
        
        # Add fields only for allowed criteria
        for criterion in self.allowed_criteria:
            # Score field
            self.fields[f'score_{criterion.id}'] = forms.ChoiceField(
                choices=[(i, i) for i in range(1, 6)],
                label=f"{criterion.name} ({criterion.weight}%)",
                help_text=criterion.description,
                widget=forms.Select(attrs={'class': 'form-select'})
            )
            
            # Comment field
            self.fields[f'comment_{criterion.id}'] = forms.CharField(
                label=f"Comments on {criterion.name}",
                required=False,
                widget=forms.Textarea(attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': f'Optional feedback on {criterion.name}...'
                })
            )
        
        # General comments
        self.fields['comments'] = forms.CharField(
            label="Overall Comments",
            required=False,
            widget=forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Overall feedback for the team...'
            })
        )

class PublicTeamScoreForm(forms.Form):
    """Form for public judges (all criteria)"""
    
    def __init__(self, *args, **kwargs):
        self.team = kwargs.pop('team')
        self.allowed_criteria = kwargs.pop('allowed_criteria')
        super().__init__(*args, **kwargs)
        
        # Add fields for all criteria (public judges see everything)
        for criterion in self.allowed_criteria:
            self.fields[f'score_{criterion.id}'] = forms.ChoiceField(
                choices=[(i, i) for i in range(1, 6)],
                label=f"{criterion.name} ({criterion.weight}%)",
                help_text=criterion.description,
                widget=forms.Select(attrs={'class': 'form-select'})
            )
            
            self.fields[f'comment_{criterion.id}'] = forms.CharField(
                label=f"Comments on {criterion.name}",
                required=False,
                widget=forms.Textarea(attrs={
                    'class': 'form-control',
                    'rows': 2,
                    'placeholder': f'Optional feedback on {criterion.name}...'
                })
            )
        
        self.fields['comments'] = forms.CharField(
            label="Overall Comments",
            required=False,
            widget=forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Overall feedback for the team...'
            })
        )

