from django.core.management.base import BaseCommand
from core.utils.email_client import run_email_listener

class Command(BaseCommand):
    help = "Listen for incoming emails containing CDM JSON attachments and ingest them"

    def handle(self, *args, **options):
        self.stdout.write("Launching email CDM ingestion listener...")
        try:
            run_email_listener()
        except KeyboardInterrupt:
            self.stdout.write("Email CDM ingestion listener stopped by user.")