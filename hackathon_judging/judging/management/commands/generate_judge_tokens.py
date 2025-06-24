from django.core.management.base import BaseCommand
from judging.models import Judge
import uuid

class Command(BaseCommand):
    help = 'Generate unique tokens for existing judges without tokens'

    def handle(self, *args, **options):
        judges_updated = 0
        
        for judge in Judge.objects.all():
            if not judge.unique_token:
                judge.unique_token = uuid.uuid4()
                judge.save()
                judges_updated += 1
                self.stdout.write(f'Generated token for {judge.user.get_full_name()}: {judge.unique_token}')
        
        if judges_updated == 0:
            self.stdout.write(self.style.SUCCESS('All judges already have tokens!'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Generated tokens for {judges_updated} judges'))
