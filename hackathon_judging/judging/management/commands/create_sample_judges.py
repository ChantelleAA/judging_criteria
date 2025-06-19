from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from judging.models import Judge, Team, JudgeExpertise
import random

class Command(BaseCommand):
    help = 'Create sample teams and judges for testing'

    def handle(self, *args, **options):
        # Create sample teams
        teams_data = [
            {
                'name': 'QuantumSolve',
                'description': 'A quantum algorithm for optimizing supply chain logistics while reducing carbon footprint.',
                'members': 'Alice Johnson, Bob Chen, Carol Martinez',
                'presentation_link': 'https://example.com/presentation1'
            },
            {
                'name': 'EcoQuantum',
                'description': 'Quantum-enhanced simulation for sustainable energy grid optimization.',
                'members': 'David Kim, Emma Rodriguez, Frank Williams',
                'presentation_link': 'https://example.com/presentation2'
            },
            {
                'name': 'QuantumHealth',
                'description': 'Quantum machine learning for drug discovery and personalized medicine.',
                'members': 'Grace Liu, Henry Taylor, Isabel Garcia',
                'presentation_link': 'https://example.com/presentation3'
            },
            {
                'name': 'ClimateQ',
                'description': 'Quantum computing solutions for climate change modeling and prediction.',
                'members': 'Jack Brown, Kelly Wang, Luis Hernandez',
                'presentation_link': 'https://example.com/presentation4'
            },
            {
                'name': 'QuantumFinance',
                'description': 'Quantum algorithms for sustainable investment portfolio optimization.',
                'members': 'Maria Gonzalez, Nathan Lee, Olivia Davis',
                'presentation_link': 'https://example.com/presentation5'
            }
        ]
        
        for team_data in teams_data:
            team, created = Team.objects.get_or_create(
                name=team_data['name'],
                defaults=team_data
            )
            if created:
                self.stdout.write(f"Created team: {team.name}")
        
        # Create sample judges
        judges_data = [
            {
                'username': 'quantum_expert@email.com',
                'first_name': 'Dr. Sarah',
                'last_name': 'Quantum',
                'email': 'quantum_expert@email.com',
                'expertise': ['Quantum Technology']
            },
            {
                'username': 'sustainability_expert@email.com',
                'first_name': 'Prof. Michael',
                'last_name': 'Green',
                'email': 'sustainability_expert@email.com',
                'expertise': ['Sustainability & SDG']
            },
            {
                'username': 'business_expert@email.com',
                'first_name': 'Ms. Jennifer',
                'last_name': 'Business',
                'email': 'business_expert@email.com',
                'expertise': ['Business & Innovation']
            }
        ]
        
        for judge_data in judges_data:
            user, created = User.objects.get_or_create(
                username=judge_data['username'],
                defaults={
                    'first_name': judge_data['first_name'],
                    'last_name': judge_data['last_name'],
                    'email': judge_data['email'],
                }
            )
            
            if created:
                user.set_password('password123')  # Set a default password
                user.save()
                
                judge, judge_created = Judge.objects.get_or_create(user=user)
                if judge_created:
                    for expertise_name in judge_data['expertise']:
                        expertise = JudgeExpertise.objects.get(name=expertise_name)
                        judge.expertise_areas.add(expertise)
                    
                    self.stdout.write(f"Created judge: {user.get_full_name()}")
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created sample data')
        )