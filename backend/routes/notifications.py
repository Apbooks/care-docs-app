from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from models.push_subscription import PushSubscription
from models.user import User
from routes.auth import get_current_user
from config import get_settings
from services.notification_service import send_push_notifications

router = APIRouter()


class SubscriptionKeys(BaseModel):
    p256dh: str
    auth: str


class SubscriptionPayload(BaseModel):
    endpoint: str
    keys: SubscriptionKeys
    expiration_time: Optional[datetime] = Field(default=None, alias="expirationTime")

    model_config = {"populate_by_name": True}


class SubscriptionResponse(BaseModel):
    id: str
    endpoint: str
    expiration_time: Optional[str]


class TestNotificationRequest(BaseModel):
    title: str = "Care Docs Reminder"
    body: str = "Test notification from Care Docs"


def _to_response(subscription: PushSubscription) -> SubscriptionResponse:
    return SubscriptionResponse(
        id=str(subscription.id),
        endpoint=subscription.endpoint,
        expiration_time=subscription.expiration_time.isoformat() if subscription.expiration_time else None
    )


@router.get("/subscriptions", response_model=List[SubscriptionResponse])
async def list_subscriptions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    subscriptions = db.query(PushSubscription).filter(
        PushSubscription.user_id == current_user.id
    ).order_by(PushSubscription.created_at.desc()).all()
    return [_to_response(subscription) for subscription in subscriptions]


@router.post("/subscribe", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def subscribe(
    payload: SubscriptionPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing = db.query(PushSubscription).filter(
        PushSubscription.endpoint == payload.endpoint
    ).first()

    if existing:
        existing.user_id = current_user.id
        existing.p256dh = payload.keys.p256dh
        existing.auth = payload.keys.auth
        existing.expiration_time = payload.expiration_time
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return _to_response(existing)

    subscription = PushSubscription(
        user_id=current_user.id,
        endpoint=payload.endpoint,
        p256dh=payload.keys.p256dh,
        auth=payload.keys.auth,
        expiration_time=payload.expiration_time
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    return _to_response(subscription)


@router.post("/unsubscribe", status_code=status.HTTP_204_NO_CONTENT)
async def unsubscribe(
    payload: SubscriptionPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    subscription = db.query(PushSubscription).filter(
        PushSubscription.endpoint == payload.endpoint,
        PushSubscription.user_id == current_user.id
    ).first()
    if not subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    db.delete(subscription)
    db.commit()
    return None


@router.post("/test", status_code=status.HTTP_202_ACCEPTED)
async def test_notification(
    payload: TestNotificationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    settings = get_settings()
    if not (settings.VAPID_PUBLIC_KEY and settings.VAPID_PRIVATE_KEY):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="VAPID keys not configured"
        )
    subscriptions = db.query(PushSubscription).filter(
        PushSubscription.user_id == current_user.id
    ).all()
    if not subscriptions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No subscriptions found")

    subscription_payloads: List[Dict[str, Any]] = [
        {
            "endpoint": sub.endpoint,
            "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
        }
        for sub in subscriptions
    ]

    send_push_notifications(subscription_payloads, {
        "type": "test",
        "title": payload.title,
        "body": payload.body,
        "url": "/"
    })
    return {"status": "sent"}


@router.get("/vapid-public-key")
async def vapid_public_key():
    settings = get_settings()
    if not settings.VAPID_PUBLIC_KEY:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VAPID public key not configured"
        )
    return {"public_key": settings.VAPID_PUBLIC_KEY}
