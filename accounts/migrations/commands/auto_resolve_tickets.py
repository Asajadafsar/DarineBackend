# management/commands/auto_resolve_tickets.py

from django.core.management.base import BaseCommand
from accounts.views import auto_resolve_tickets


class Command(BaseCommand):
    help = 'Auto resolve tickets that are in answered status for more than 2 days'

    def handle(self, *args, **options):
        resolved_count = auto_resolve_tickets()
        self.stdout.write(
            self.style.SUCCESS(f'Successfully auto-resolved {resolved_count} tickets')
        )