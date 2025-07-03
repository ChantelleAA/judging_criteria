# Create: judging/management/commands/setup_new_criteria.py

from django.core.management.base import BaseCommand
from judging.models import JudgeExpertise, JudgingCriteria

class Command(BaseCommand):
    help = 'Set up NEW judging criteria from paste.txt for AIMS Ghana Quantathon 2025'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset all existing criteria before setup',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write('🔄 Resetting existing criteria...')
            JudgingCriteria.objects.all().delete()
            self.stdout.write(self.style.WARNING('Existing criteria deleted'))

        self.stdout.write('🚀 Setting up NEW judging criteria...')

        # Create expertise areas if they don't exist
        quantum_expert, _ = JudgeExpertise.objects.get_or_create(
            name="Quantum Technology",
            defaults={'description': "Experts in quantum computing, algorithms, and hardware"}
        )
        
        sustainability_expert, _ = JudgeExpertise.objects.get_or_create(
            name="Sustainability & SDG",
            defaults={'description': "Experts in sustainable development and social impact"}
        )
        
        business_expert, _ = JudgeExpertise.objects.get_or_create(
            name="Business & Innovation",
            defaults={'description': "Experts in business strategy, innovation, and commercialization"}
        )

        # Create the NEW judging criteria exactly as in paste.txt
        new_criteria = [
            {
                'name': 'Quantum Computing Relevance',
                'description': 'Evaluate if quantum computing is essential for solving this problem and if the team clearly articulated why QC is appropriate and necessary.',
                'weight': 35.00,
                'guide_questions': 'Is quantum computing essential for solving this problem?\nHas the team clearly articulated why QC is appropriate and necessary?\nDoes the solution target a real-world need or application?',
                'expertise_areas': [quantum_expert]
            },
            {
                'name': 'Quantum Computing Quality',
                'description': 'Evaluate the technical implementation including algorithm selection, code quality, and integration of quantum aspects.',
                'weight': 25.00,
                'guide_questions': 'Did the team select appropriate quantum algorithms or models?\nWas the code functional, well-documented, and thoughtfully constructed?\nWas the quantum aspect clearly integrated into the proposed solution?\nWas there creativity in the technical implementation?',
                'expertise_areas': [quantum_expert]
            },
            {
                'name': 'Social Impact Based on the SDGs',
                'description': 'Evaluate alignment with UN Sustainable Development Goals and potential for scalable social impact.',
                'weight': 25.00,
                'guide_questions': 'Is the solution directly addressing a UN SDG?\nIs the impact scalable or applicable in other domains or regions?\nDoes the solution have practical potential for solving an African or global issue?',
                'expertise_areas': [sustainability_expert]
            },
            {
                'name': 'Presentation and Originality',
                'description': 'Evaluate presentation quality, communication effectiveness, and evidence of original thinking.',
                'weight': 15.00,
                'guide_questions': 'Did the team present the problem and solution clearly?\nWas the pitch well-structured and compelling?\nDid they demonstrate their prototype or application?\nWas there evidence of original thinking or creative exploration?',
                'expertise_areas': [quantum_expert, sustainability_expert, business_expert]
            }
        ]

        for criteria_info in new_criteria:
            criteria, created = JudgingCriteria.objects.get_or_create(
                name=criteria_info['name'],
                defaults={
                    'description': criteria_info['description'],
                    'weight': criteria_info['weight'],
                    'guide_questions': criteria_info['guide_questions']
                }
            )
            
            # Clear existing expertise areas and add new ones
            criteria.expertise_areas.clear()
            for expertise in criteria_info['expertise_areas']:
                criteria.expertise_areas.add(expertise)
            
            status = "✅ Created" if created else "🔄 Updated"
            self.stdout.write(f'{status} criteria: {criteria.name} ({criteria.weight}%)')

        self.stdout.write(self.style.SUCCESS('🎉 NEW criteria setup complete!'))
        
        # Verify the setup
        self.stdout.write('\n📋 Current criteria in database:')
        for criteria in JudgingCriteria.objects.all().order_by('-weight'):
            self.stdout.write(f'  • {criteria.name} ({criteria.weight}%)')
        
        total_weight = sum(JudgingCriteria.objects.values_list('weight', flat=True))
        self.stdout.write(f'\n📊 Total weight: {total_weight}%')
        
        if total_weight == 100:
            self.stdout.write(self.style.SUCCESS('✅ Weights sum to 100% - Perfect!'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠️  Weights sum to {total_weight}% - Should be 100%'))