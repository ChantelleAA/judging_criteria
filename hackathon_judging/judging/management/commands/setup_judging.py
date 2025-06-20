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

        # Social Impact
        social_criteria, _ = JudgingCriteria.objects.update_or_create(
            name="Social Impact",
            defaults={
                "description": (
                    "• Does the idea address one or more Sustainable Development Goal(s) relevant to Africa?\n"
                    "• Is the social impact clearly articulated and supported with data or projections?\n"
                    "• How scalable is the impact — local (community), national, continental, or global?\n"
                    "• How urgent is the problem being addressed, and how timely is the solution?"
                ),
                "weight": 25.00
            }
        )
        social_criteria.expertise_areas.set([sustainability_expert])

        # Innovation
        innovation_criteria, _ = JudgingCriteria.objects.update_or_create(
            name="Innovation",
            defaults={
                "description": (
                    "• Is the idea bringing something new and valuable to Africa or the global community?\n"
                    "• Does it explore unconventional or underrepresented problem spaces?\n"
                    "• Can we clearly understand the proposed innovation and how it differs from existing approaches?\n"
                    "• Is the idea reframing or solving a known issue in a fresh, meaningful way?"
                ),
                "weight": 20.00
            }
        )
        innovation_criteria.expertise_areas.set([quantum_expert, business_expert])

        # Quantum Tech Quality
        quantum_criteria, _ = JudgingCriteria.objects.update_or_create(
            name="Quantum Tech Quality",
            defaults={
                "description": (
                    "• What aspect of Quantum Computing is being utilized in the project?\n"
                    "• How complex and technically rigorous is the solution or algorithm?\n"
                    "• Is the solution theoretically sound, practically implementable, or both?\n"
                    "• Were modern tools or methods used (e.g., AI, ML, Quantum simulation, NLP, Web, Mobile)?\n"
                    "• Can the prototype be expanded into research or education use in Africa?\n"
                    "• Will this help other learners in Africa build understanding in Quantum Computing?"
                ),
                "weight": 40.00
            }
        )
        quantum_criteria.expertise_areas.set([quantum_expert])

        # Business Viability
        business_criteria, _ = JudgingCriteria.objects.update_or_create(
            name="Business Viability",
            defaults={
                "description": (
                    "• Is the product useful, usable, and relevant to African or global markets?\n"
                    "• How well does the project consider ROI, adoption, and real-world traction?\n"
                    "• Can the solution be developed into a viable startup or scalable initiative?\n"
                    "• Is the proof of concept implementable in real communities or industries?\n"
                    "• What types of investors or partners would support this idea in Africa?"
                ),
                "weight": 5.00
            }
        )
        business_criteria.expertise_areas.set([business_expert])

        # Presentation
        presentation_criteria, _ = JudgingCriteria.objects.update_or_create(
            name="Presentation",
            defaults={
                "description": (
                    "• Is the problem clearly communicated with data, context, or real-life examples?\n"
                    "• Does the presentation or demo effectively show the solution’s value?\n"
                    "• Is the pitch inclusive, clear, and engaging for a diverse audience?\n"
                    "• Did all team members contribute to the delivery?\n"
                    "• Can the team deliver the core message within the time limit?\n"
                    "• Did the content include short- and long-term roadmaps or vision?\n"
                    "• Were success metrics, obstacles, and next steps addressed?\n"
                    "• Did the team anticipate and respond to possible judge questions?"
                ),
                "weight": 10.00
            }
        )
        presentation_criteria.expertise_areas.set([presentation_expert])

        self.stdout.write(
            self.style.SUCCESS('Successfully set up judging criteria and expertise areas with contextual guiding questions.')
        )
