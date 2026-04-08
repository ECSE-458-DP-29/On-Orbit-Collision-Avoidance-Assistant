import logging
from django.conf import settings
from django.core.mail import send_mail
from twilio.rest import Client

logger = logging.getLogger(__name__)

def send_collision_email_notification(cdm, pc_value, recipients=None):
    recipients = recipients or getattr(settings, "PC_NOTIFICATION_EMAILS", [])
    if not recipients:
        logger.warning("No high-Pc email recipients configured.")
        return

    subject = f"High collision probability for CDM {cdm.cdm_id}"
    body = (
        f"CDM {cdm.cdm_id} has a calculated probability of collision of "
        f"{pc_value:.2e}.\n\n"
        f"TCA: {cdm.tca}\n"
        f"Miss distance: {cdm.miss_distance_m} m\n"
        f"Relative speed: {cdm.relative_speed_ms} m/s\n"
    )

    send_mail(
        subject,
        body,
        settings.DEFAULT_FROM_EMAIL,
        recipients,
        fail_silently=False,
    )
    logger.info("Sent high-Pc email notification for CDM %s", cdm.cdm_id)


def send_collision_sms_notification(cdm, pc_value, phone=None):
    phone = phone or getattr(settings, "PC_NOTIFICATION_PHONE_NUMBER", None)
    if not phone:
        logger.warning("No high-Pc SMS recipient configured.")
        return

    account_sid = getattr(settings, "TWILIO_ACCOUNT_SID", None)
    auth_token = getattr(settings, "TWILIO_AUTH_TOKEN", None)
    from_number = getattr(settings, "TWILIO_FROM_NUMBER", None)

    if not all([account_sid, auth_token, from_number]):
        logger.error("Twilio credentials are not fully configured.")
        return

    body = (
        f"HIGH Pc ALERT: CDM {cdm.cdm_id} has Pc={pc_value:.2e}. "
        f"TCA: {cdm.tca}, Miss distance: {cdm.miss_distance_m}m."
    )

    client = Client(account_sid, auth_token)
    message = client.messages.create(
        body=body,
        from_=from_number,
        to=phone,
    )
    logger.info(
        "Sent high-Pc SMS notification for CDM %s (SID: %s)",
        cdm.cdm_id,
        message.sid,
    )

def notify_high_pc(cdm, pc_value):
    threshold = getattr(settings, "PC_NOTIFICATION_THRESHOLD", 1e-4)
    if float(pc_value) < threshold:
        return

    send_collision_email_notification(cdm, pc_value)

    phone = getattr(settings, "PC_NOTIFICATION_PHONE_NUMBER", None)
    if phone:
        send_collision_sms_notification(cdm, pc_value, phone)