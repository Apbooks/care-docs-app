import asyncio
import json
from typing import Dict, Any, Optional, Set

from fastapi import APIRouter, Depends, HTTPException, Request, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from routes.auth import get_token_from_request
from services.auth_service import decode_token, verify_token_type
from services import pubsub

router = APIRouter()

_subscribers: Set[asyncio.Queue] = set()
_lock = asyncio.Lock()


async def local_broadcast(payload: Dict[str, Any]) -> None:
    """Broadcast to this worker's local SSE subscribers only."""
    async with _lock:
        queues = list(_subscribers)

    for queue in queues:
        try:
            queue.put_nowait(payload)
        except asyncio.QueueFull:
            pass


async def _get_current_user_from_stream(
    request: Request,
    db: Session,
    token: Optional[str]
) -> User:
    if not token:
        token = await get_token_from_request(request)

    payload = decode_token(token)
    if payload is None or not verify_token_type(payload, "access"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return user


async def broadcast_event(payload: Dict[str, Any]) -> None:
    """Publish event to all workers via PostgreSQL NOTIFY."""
    await pubsub.publish(payload)


@router.get("/stream")
async def stream_events(
    request: Request,
    token: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    await _get_current_user_from_stream(request, db, token)

    queue: asyncio.Queue = asyncio.Queue(maxsize=100)

    async with _lock:
        _subscribers.add(queue)

    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break

                try:
                    message = await asyncio.wait_for(queue.get(), timeout=15)
                    yield f"data: {json.dumps(message)}\n\n"
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            async with _lock:
                _subscribers.discard(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
