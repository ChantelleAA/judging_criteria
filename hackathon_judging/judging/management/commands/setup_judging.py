from django.core.management.base import BaseCommand
from judging.models import JudgeExpertise, JudgingCriteria

class Command(BaseCommand):
    help = 'Set up initial judging criteria and expertise areas'

    def handle(self, *args, **options):
        # Create expertise areas
        quantum_expert = JudgeExpertise.objects.get_or_create(
            name="Quantum Technology",
            defaults={'description': "Experts in quantum computing, algorithms, and hardware"}
        )[0]
        
        sustainability_expert = JudgeExpertise.objects.get_or_create(
            name="Sustainability & SDG",
            defaults={'description': "Experts in sustainable development and social impact"}
        )[0]
        
        business_expert = JudgeExpertise.objects.get_or_create(
            name="Business & Innovation",
            defaults={'description': "Experts in business strategy, innovation, and commercialization"}
        )[0]
        
        presentation_expert = JudgeExpertise.objects.get_or_create(
            name="Presentation & Communication",
            defaults={'description': "Experts in communication, public speaking, and presentation skills"}
        )[0]
        
        # Create judging criteria
        quantum_criteria = JudgingCriteria.objects.get_or_create(
            name="Quantum Tech Quality",
            defaults={
                'description': "Technical implementation and quantum computing excellence",
                'weight': 40.00
            })[0]
        quantum_criteria.expertise_areas.add(quantum_expert)
        
        social_criteria = JudgingCriteria.objects.get_or_create(
            name="Social Impact",
            defaults={
                'description': "Alignment with SDGs and potential social benefit",
                'weight': 25.00
            })[0]
        social_criteria.expertise_areas.add(sustainability_expert)
        
        innovation_criteria = JudgingCriteria.objects.get_or_create(
            name="Innovation",
            defaults={
                'description': "Novelty and creative approach to problem-solving",
                'weight': 20.00
            })[0]
        innovation_criteria.expertise_areas.add(quantum_expert, business_expert)
        
        presentation_criteria = JudgingCriteria.objects.get_or_create(
            name="Presentation",
            defaults={
                'description': "Quality of presentation and communication",
                'weight': 10.00
            })[0]
        presentation_criteria.expertise_areas.add(presentation_expert)
        
        business_criteria = JudgingCriteria.objects.get_or_create(
            name="Business Viability",
            defaults={
                'description': "Commercial potential and scalability",
                'weight': 5.00
            })[0]
        business_criteria.expertise_areas.add(business_expert)
        
        self.stdout.write(
            self.style.SUCCESS('Successfully set up judging criteria and expertise areas')
        )