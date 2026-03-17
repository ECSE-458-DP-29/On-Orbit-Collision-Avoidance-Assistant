import sys
import threading
import logging
from django.apps import AppConfig

logger = logging.getLogger(__name__)


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        """Start email listener when Django initializes during runserver."""
        # Only start listener during runserver (not during migrations, tests, etc.)
        if 'runserver' in sys.argv:
            thread = threading.Thread(target=self._start_email_listener, daemon=True)
            thread.start()

    def _start_email_listener(self):
        """Run email listener in background thread."""
        try:
            from core.utils.email_client import run_email_listener
            run_email_listener()
        except Exception as e:
            logger.error(f"❌ Error starting email listener: {e}")
