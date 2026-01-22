import json
import logging
from typing import Dict, Any, List

from pywebpush import webpush, WebPushException

from config import get_settings

logger = logging.getLogger(__name__)


def _has_vapid_keys() -> bool:
    settings = get_settings()
    return bool(settings.VAPID_PUBLIC_KEY and settings.VAPID_PRIVATE_KEY)


def send_push_notifications(subscriptions: List[Dict[str, Any]], payload: Dict[str, Any]) -> None:
    """Send a push notification payload to each subscription."""
    settings = get_settings()
    if not _has_vapid_keys():
        logger.warning("VAPID keys not configured; skipping push notifications")
        return

    data = json.dumps(payload)
    vapid_claims = {"sub": f"mailto:{settings.VAPID_CLAIM_EMAIL}"}

    for subscription in subscriptions:
        try:
            webpush(
                subscription_info=subscription,
                data=data,
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims=vapid_claims
            )
        except WebPushException as exc:
            logger.warning("Web push failed for endpoint %s: %s", subscription.get("endpoint"), exc)
