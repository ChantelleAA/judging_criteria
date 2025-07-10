from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from judging.models import Judge, JudgeExpertise, JudgingCriteria

class Command(BaseCommand):
    help = 'Set up real judges and expertise areas based on actual judge list'

    def handle(self, *args, **options):
        # Create expertise areas based on the real judges' backgrounds
        expertise_areas = [
            {
                'name': 'Quantum Physics & Materials',
                'description': 'Condensed matter physics, quantum materials, quantum optics, quantum photonics'
            },
            {
                'name': 'Quantum Information & Computing',
                'description': 'Quantum information theory, quantum machine learning, quantum algorithms'
            },
            {
                'name': 'Quantum Hardware & Engineering',
                'description': 'Superconducting circuits, Josephson junctions, quantum simulations'
            },
            {
                'name': 'Mathematical & Theoretical Physics',
                'description': 'Mathematical foundations, quantum gravity, integrable systems, field theory'
            },
            {
                'name': 'Innovation & Strategy',
                'description': 'Innovation strategy, ecosystem development, science policy, quantum industry'
            },
            {
                'name': 'Education & Outreach',
                'description': 'Science education, quantum computing education, technology education'
            },
            {
                'name': 'Climate & Environmental Science',
                'description': 'Climate science, atmospheric physics, environmental modeling'
            },
            {
                'name': 'Computer Science & Technology',
                'description': 'Computer science, web/mobile technology, digital infrastructure'
            },
            {
                'name': 'Engineering & Applied Sciences',
                'description': 'Engineering education, biomedical engineering, applied physics'
            },
            {
                'name': 'Science Policy & Development',
                'description': 'Science policy, development cooperation, science philanthropy'
            }
        ]

        # Create expertise areas
        created_expertise = {}
        for area_data in expertise_areas:
            expertise, created = JudgeExpertise.objects.get_or_create(
                name=area_data['name'],
                defaults={'description': area_data['description']}
            )
            created_expertise[area_data['name']] = expertise
            if created:
                self.stdout.write(f"Created expertise area: {expertise.name}")

        # Real judges data
        judges_data = [
            {
                'name': 'Karen Hallberg',
                'email': 'karen.hallberg@judges.hackathon.com',
                'expertise': ['Quantum Physics & Materials', 'Mathematical & Theoretical Physics']
            },
            {
                'name': 'Ian Walmsley',
                'email': 'ian.walmsley@judges.hackathon.com',
                'expertise': ['Quantum Physics & Materials', 'Quantum Information & Computing']
            },
            {
                'name': 'Philipp Kammerlander',
                'email': 'philipp.kammerlander@judges.hackathon.com',
                'expertise': ['Quantum Information & Computing', 'Mathematical & Theoretical Physics']
            },
            {
                'name': 'Reena Dayal Yadav',
                'email': 'reena.yadav@judges.hackathon.com',
                'expertise': ['Innovation & Strategy', 'Science Policy & Development']
            },
            {
                'name': 'Leandro Tosi',
                'email': 'leandro.tosi@judges.hackathon.com',
                'expertise': ['Quantum Hardware & Engineering', 'Quantum Physics & Materials']
            },
            {
                'name': 'Marcelo Terra Cunha',
                'email': 'marcelo.cunha@judges.hackathon.com',
                'expertise': ['Mathematical & Theoretical Physics', 'Quantum Information & Computing']
            },
            {
                'name': 'Ryan Sweke',
                'email': 'ryan.sweke@judges.hackathon.com',
                'expertise': ['Quantum Information & Computing', 'Mathematical & Theoretical Physics']
            },
            {
                'name': 'Jonathan Oppenheim',
                'email': 'jonathan.oppenheim@judges.hackathon.com',
                'expertise': ['Quantum Information & Computing', 'Mathematical & Theoretical Physics']
            },
            {
                'name': 'Trond Ikdahl Andersen',
                'email': 'trond.andersen@judges.hackathon.com',
                'expertise': ['Quantum Hardware & Engineering', 'Quantum Physics & Materials']
            },
            {
                'name': 'Maïté Dupuis',
                'email': 'maite.dupuis@judges.hackathon.com',
                'expertise': ['Mathematical & Theoretical Physics', 'Education & Outreach']
            },
            {
                'name': 'Stéphane Decoutère',
                'email': 'stephane.decoutere@judges.hackathon.com',
                'expertise': ['Science Policy & Development', 'Innovation & Strategy']
            },
            {
                'name': 'Sandro Giuliani',
                'email': 'sandro.giuliani@judges.hackathon.com',
                'expertise': ['Science Policy & Development', 'Education & Outreach']
            },
            {
                'name': 'Sana Odeh',
                'email': 'sana.odeh@judges.hackathon.com',
                'expertise': ['Computer Science & Technology', 'Education & Outreach']
            },
            {
                'name': 'Nii Quaynor',
                'email': 'nii.quaynor@judges.hackathon.com',
                'expertise': ['Computer Science & Technology', 'Innovation & Strategy']
            },
            {
                'name': 'Nana Ama Browne Klutse',
                'email': 'nana.klutse@judges.hackathon.com',
                'expertise': ['Climate & Environmental Science', 'Mathematical & Theoretical Physics']
            },
            {
                'name': 'Patrick Dorey',
                'email': 'chantelleope@gmail.com',
                'expertise': ['Mathematical & Theoretical Physics', 'Quantum Physics & Materials']
            },
            {
                'name': 'Elsie Kaufmann',
                'email': 'elsie.kaufmann@judges.hackathon.com',
                'expertise': ['Engineering & Applied Sciences', 'Education & Outreach']
            },
            {
                'name': 'David',
                'email': 'david@judges.hackathon.com',
                'expertise': ['Business & Innovation', 'Education & Outreach']
            },
            {
                'name': 'Yaw Frimpong',
                'email': 'yaw@judges.hackathon.com',
                'expertise': ['Business & Innovation', 'Education & Outreach']
            }
        ]

        # Create judges
        for judge_data in judges_data:
            # Split name into first and last name
            name_parts = judge_data['name'].split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            # Create or get user
            user, created = User.objects.get_or_create(
                username=judge_data['email'],
                defaults={
                    'email': judge_data['email'],
                    'first_name': first_name,
                    'last_name': last_name,
                    'is_active': True,
                }
            )
            
            if created:
                # Set a temporary password - they should reset it
                user.set_password('hackathon2025!')
                user.save()
                self.stdout.write(f"Created user: {user.get_full_name()}")
            
            # Create or get judge profile
            judge, judge_created = Judge.objects.get_or_create(
                user=user,
                defaults={'has_submitted': False}
            )
            
            if judge_created or not judge.expertise_areas.exists():
                # Add expertise areas
                judge.expertise_areas.clear()  # Clear existing if any
                for expertise_name in judge_data['expertise']:
                    if expertise_name in created_expertise:
                        judge.expertise_areas.add(created_expertise[expertise_name])
                
                self.stdout.write(f"Set up judge: {user.get_full_name()} with expertise: {', '.join(judge_data['expertise'])}")

        # Update judging criteria to match new expertise areas
        criteria_mappings = [
            {
                'name': 'Quantum Tech Quality',
                'description': 'Technical excellence in quantum computing implementation, algorithm design, and quantum advantage demonstration',
                'weight': 40.00,
                'expertise_areas': [
                    'Quantum Physics & Materials',
                    'Quantum Information & Computing', 
                    'Quantum Hardware & Engineering',
                    'Mathematical & Theoretical Physics'
                ]
            },
            {
                'name': 'Social Impact',
                'description': 'Alignment with UN SDGs, potential for positive societal impact, and addressing global challenges',
                'weight': 25.00,
                'expertise_areas': [
                    'Climate & Environmental Science',
                    'Science Policy & Development',
                    'Innovation & Strategy',
                    'Education & Outreach'
                ]
            },
            {
                'name': 'Innovation',
                'description': 'Novelty of approach, creative problem-solving, and breakthrough potential',
                'weight': 20.00,
                'expertise_areas': [
                    'Quantum Information & Computing',
                    'Innovation & Strategy',
                    'Computer Science & Technology',
                    'Mathematical & Theoretical Physics'
                ]
            },
            {
                'name': 'Presentation',
                'description': 'Quality of presentation, clarity of communication, and educational value',
                'weight': 10.00,
                'expertise_areas': [
                    'Education & Outreach',
                    'Science Policy & Development',
                    'Computer Science & Technology'
                ]
            },
            {
                'name': 'Business Viability',
                'description': 'Commercial potential, scalability, and real-world implementation feasibility',
                'weight': 5.00,
                'expertise_areas': [
                    'Innovation & Strategy',
                    'Engineering & Applied Sciences',
                    'Computer Science & Technology'
                ]
            }
        ]

        # Create or update judging criteria
        for criteria_data in criteria_mappings:
            criteria, created = JudgingCriteria.objects.get_or_create(
                name=criteria_data['name'],
                defaults={
                    'description': criteria_data['description'],
                    'weight': criteria_data['weight']
                }
            )
            
            # Update description and weight if needed
            if not created:
                criteria.description = criteria_data['description']
                criteria.weight = criteria_data['weight']
                criteria.save()
            
            # Clear and set expertise areas
            criteria.expertise_areas.clear()
            for expertise_name in criteria_data['expertise_areas']:
                if expertise_name in created_expertise:
                    criteria.expertise_areas.add(created_expertise[expertise_name])
            
            if created:
                self.stdout.write(f"Created criteria: {criteria.name}")
            else:
                self.stdout.write(f"Updated criteria: {criteria.name}")

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully set up:\n'
                f'- {len(expertise_areas)} expertise areas\n'
                f'- {len(judges_data)} expert judges\n'
                f'- {len(criteria_mappings)} judging criteria\n\n'
                f'Default password for all judges: hackathon2025!\n'
                f'Judges should change their passwords after first login.'
            )
        )