import os
import sys
import django
import json
import time
from imap_tools import MailBox, AND

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "OOCAA.settings")
django.setup()

from core.services.cdm_service import parse_cdm_json
from core.services.pc_calculation_service import calculate_pc_multistep, update_cdm_with_pc_result

IMAP_SERVER = "imap.gmail.com"
USERNAME = "email"
PASSWORD = "app password 16-digits"

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
    print("Starting email-based CDM ingestion listener... (Ctrl+C to stop)")
    last_known_uid = None

    while True:
        try:
            with MailBox(IMAP_SERVER).login(USERNAME, PASSWORD) as mailbox:
                if last_known_uid is None:
                    msgs = list(mailbox.fetch(reverse=True, limit=1))
                    last_known_uid = int(msgs[0].uid) if msgs else 0
                    print(f"Baseline established. Monitoring for UIDs > {last_known_uid}")

                while True:
                    criteria = AND(uid=f"{last_known_uid + 1}:*", seen=False)

                    for msg in mailbox.fetch(criteria):
                        print(f"New email: {msg.subject} (UID: {msg.uid})")
                        last_known_uid = max(last_known_uid, int(msg.uid))

                        for att in msg.attachments:
                            if att.filename and att.filename.lower().endswith(".json"):
                                try:
                                    result = process_cdm_attachment(att.payload, auto_calculate_pc=True)
                                    print(f"Processed {att.filename}: {result}")
                                except Exception as e:
                                    print(f"Error processing attachment {att.filename}: {e}")

                        mailbox.flag(msg.uid, "\\SEEN", True)

                    print("IDLE: Waiting for new email…")
                    mailbox.idle.wait(timeout=60)

        except Exception as e:
            print(f"Connection or processing error: {e}")
            print("Retrying in 10 seconds…")
            time.sleep(10)

if __name__ == "__main__":
    run_email_listener()
