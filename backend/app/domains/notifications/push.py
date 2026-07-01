import json
import os
import logging
from pywebpush import webpush, WebPushException

logger = logging.getLogger(__name__)

VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY")
VAPID_CLAIM_EMAIL = os.getenv("VAPID_CLAIM_EMAIL")

def send_web_push(subscription_info: dict, payload_data: dict):
    """
    Send a Web Push notification to a specific subscription.
    subscription_info must have: endpoint, keys { p256dh, auth }
    """
    if not VAPID_PRIVATE_KEY or not VAPID_CLAIM_EMAIL:
        logger.warning("VAPID keys not configured, skipping web push")
        return False

    try:
        webpush(
            subscription_info=subscription_info,
            data=json.dumps(payload_data),
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims={"sub": VAPID_CLAIM_EMAIL}
        )
        return True
    except WebPushException as ex:
        logger.error(f"Web Push failed: {repr(ex)}")
        if ex.response and ex.response.json():
            logger.error(f"Web Push response: {ex.response.json()}")
        # We should typically remove expired subscriptions if 410 Gone
        if ex.response and ex.response.status_code == 410:
            return "EXPIRED"
        return False
    except Exception as e:
        logger.error(f"Unexpected error in web push: {e}")
        return False
