import os
import sys
import django
import json
import time
import logging
import ssl
from imap_tools import MailBox, AND

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "OOCAA.settings")
django.setup()

from django.conf import settings
from core.services.cdm_service import parse_cdm_json
from core.services.pc_calculation_service import calculate_pc_multistep, update_cdm_with_pc_result

# Configure logging
logger = logging.getLogger(__name__)

# Load email configuration from Django settings
IMAP_SERVER = settings.EMAIL_IMAP_SERVER
USERNAME = settings.EMAIL_USERNAME
PASSWORD = settings.EMAIL_PASSWORD


def credentials_configured():
    """Check if email credentials are properly configured."""
    if not USERNAME or not PASSWORD:
        logger.warning(
            "⚠️  Email credentials not configured. "
            "Set EMAIL_USERNAME and EMAIL_PASSWORD in your .env file to enable email CDM ingestion."
        )
        return False
    return True


def validate_credentials():
    """Validate email credentials by attempting a login."""
    try:
        logger.info(f"🔐 Validating email credentials for {USERNAME} on {IMAP_SERVER}...")
        
        # Create SSL context for Office 365 compatibility
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = True
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        
        with MailBox(IMAP_SERVER, ssl_context=ssl_context).login(USERNAME, PASSWORD) as mailbox:
            logger.info("✅ Email credentials validated successfully!")
            return True
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Authentication failed: {error_msg}")
        
        if "AuthFailed" in error_msg or "BasicAuthBlocked" in error_msg:
            logger.error(
                "📧 Gmail authentication failed.\n"
                "   → Generate an App Password: https://myaccount.google.com/apppasswords\n"
                "   → Must enable 2-step verification first\n"
                "   → Copy the 16-digit password and paste into EMAIL_PASSWORD in .env\n"
                "   → Then restart the server"
            )
        elif "certificate" in error_msg.lower() or "ssl" in error_msg.lower():
            logger.error(
                "🔒 SSL/TLS Certificate issue detected.\n"
                "   → Make sure your system certificates are up to date\n"
                "   → Try running: pip install --upgrade certifi"
            )
        else:
            logger.error(
                "💡 Gmail troubleshooting:\n"
                f"   → Server: {IMAP_SERVER}, Port: 993 (SSL)\n"
                "   → Ensure 2-step verification is enabled\n"
                "   → Generate fresh app password and try again"
            )
        return False


def process_cdm_attachment(payload_bytes, auto_calculate_pc=True):
    """Process a .json attachment payload from email and create CDM(s)."""
    data = json.loads(payload_bytes.decode("utf-8"))

    if isinstance(data, dict):
        entries = [data]
    elif isinstance(data, list):
        entries = data
    else:
        raise ValueError("CDM JSON must be an object or an array")

    results = {"created": 0, "failed": 0, "errors": []}

    for idx, cdm_data in enumerate(entries, start=1):
        try:
            cdm, obj1, obj2 = parse_cdm_json(cdm_data)
            results["created"] += 1

            if auto_calculate_pc:
                try:
                    calc_result = calculate_pc_multistep(cdm, None)
                    if calc_result.get("success"):
                        update_cdm_with_pc_result(cdm, calc_result, save=True)
                except Exception as e:
                    results["errors"].append(f"CDM {cdm.cdm_id} saved, Pc calc failed: {e}")
        except Exception as e:
            results["failed"] += 1
            results["errors"].append(f"entry #{idx}: {e}")

    return results


def run_email_listener():
    """Listen for incoming mail, process JSON attachments, create CDMs."""
    # Validate credentials before starting
    if not credentials_configured():
        logger.warning("Email CDM ingestion listener disabled: credentials not configured")
        return

    if not validate_credentials():
        logger.error("Email CDM ingestion listener failed to authenticate")
        return

    logger.info("🚀 Starting email-based CDM ingestion listener... (Ctrl+C to stop)")
    last_known_uid = None
    reconnect_delay = 10
    
    # Create SSL context for Office 365 compatibility
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = True
    ssl_context.verify_mode = ssl.CERT_REQUIRED

    while True:
        try:
            with MailBox(IMAP_SERVER, ssl_context=ssl_context).login(USERNAME, PASSWORD) as mailbox:
                if last_known_uid is None:
                    msgs = list(mailbox.fetch(reverse=True, limit=1))
                    last_known_uid = int(msgs[0].uid) if msgs else 0
                    logger.info(f"📧 Monitoring inbox for new CDM emails (UID > {last_known_uid})")

                while True:
                    criteria = AND(uid=f"{last_known_uid + 1}:*", seen=False)

                    for msg in mailbox.fetch(criteria):
                        logger.info(f"📬 New email received: {msg.subject}")
                        last_known_uid = max(last_known_uid, int(msg.uid))

                        cdm_count = 0
                        for att in msg.attachments:
                            if att.filename and att.filename.lower().endswith(".json"):
                                try:
                                    result = process_cdm_attachment(att.payload, auto_calculate_pc=True)
                                    cdm_count += result["created"]
                                    logger.info(f"✅ Processed {att.filename}: {result}")
                                except Exception as e:
                                    logger.error(f"❌ Error processing attachment {att.filename}: {e}")

                        if cdm_count > 0:
                            logger.info(f"🎉 Successfully ingested {cdm_count} CDM(s) from email")
                        mailbox.flag(msg.uid, "\\SEEN", True)

                    logger.debug("⏳ Waiting for new email...")
                    mailbox.idle.wait(timeout=60)

        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Connection error: {error_msg}")
            
            if "AuthFailed" in error_msg or "BasicAuthBlocked" in error_msg:
                logger.error("Authentication failed. Check your email credentials in .env")
            
            logger.info(f"🔄 Retrying connection in {reconnect_delay} seconds...")
            time.sleep(reconnect_delay)

if __name__ == "__main__":
    run_email_listener()
