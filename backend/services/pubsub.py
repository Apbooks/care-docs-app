"""
PostgreSQL LISTEN/NOTIFY pub/sub service for cross-worker SSE broadcasting.

This module enables real-time event broadcasting across multiple Uvicorn workers
by using PostgreSQL's built-in LISTEN/NOTIFY mechanism.
"""

import asyncio
import json
import logging
from typing import Callable, Dict, Any, Optional, List

import asyncpg

from config import get_settings

logger = logging.getLogger(__name__)

CHANNEL_NAME = "sse_events"

_connection: Optional[asyncpg.Connection] = None
_listen_task: Optional[asyncio.Task] = None
_handlers: List[Callable[[Dict[str, Any]], Any]] = []
_lock = asyncio.Lock()


async def _get_connection() -> asyncpg.Connection:
    """Get or create asyncpg connection for pub/sub."""
    global _connection
    async with _lock:
        if _connection is None or _connection.is_closed():
            settings = get_settings()
            _connection = await asyncpg.connect(settings.DATABASE_URL)
            logger.info("Created new asyncpg connection for pub/sub")
        return _connection


async def publish(payload: Dict[str, Any]) -> None:
    """
    Publish event to all workers via PostgreSQL NOTIFY.

    Args:
        payload: Dictionary to broadcast (will be JSON-encoded)
    """
    try:
        conn = await _get_connection()
        message = json.dumps(payload)
        # PostgreSQL NOTIFY has a payload limit of ~8000 bytes
        if len(message) > 7500:
            logger.warning("Pub/sub message truncated due to size")
            message = json.dumps({"type": payload.get("type"), "id": payload.get("id")})
        await conn.execute(f"NOTIFY {CHANNEL_NAME}, $1", message)
    except Exception as e:
        logger.error(f"Failed to publish to pub/sub: {e}")
        # Reset connection on error
        global _connection
        _connection = None


def register_handler(handler: Callable[[Dict[str, Any]], Any]) -> None:
    """
    Register a handler to receive notifications.

    Args:
        handler: Async function that receives the decoded payload dict
    """
    if handler not in _handlers:
        _handlers.append(handler)
        logger.info(f"Registered pub/sub handler: {handler.__name__}")


async def _notification_callback(
    conn: asyncpg.Connection,
    pid: int,
    channel: str,
    payload: str
) -> None:
    """Handle incoming notifications from PostgreSQL."""
    try:
        data = json.loads(payload)
        for handler in _handlers:
            try:
                result = handler(data)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"Handler error in pub/sub: {e}")
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode pub/sub message: {e}")


async def start_listener() -> None:
    """Start listening for PostgreSQL notifications."""
    global _listen_task

    if _listen_task is not None and not _listen_task.done():
        logger.info("Pub/sub listener already running")
        return

    try:
        conn = await _get_connection()
        await conn.add_listener(CHANNEL_NAME, _notification_callback)
        logger.info(f"Started listening on channel: {CHANNEL_NAME}")

        # Keepalive task to maintain connection
        async def keepalive():
            while True:
                try:
                    await asyncio.sleep(30)
                    if _connection and not _connection.is_closed():
                        await _connection.execute("SELECT 1")
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    logger.warning(f"Pub/sub keepalive error: {e}")
                    # Try to reconnect
                    try:
                        await _reconnect()
                    except Exception:
                        pass

        _listen_task = asyncio.create_task(keepalive())

    except Exception as e:
        logger.error(f"Failed to start pub/sub listener: {e}")
        raise


async def _reconnect() -> None:
    """Reconnect to PostgreSQL and re-register listener."""
    global _connection

    async with _lock:
        if _connection and not _connection.is_closed():
            try:
                await _connection.remove_listener(CHANNEL_NAME, _notification_callback)
                await _connection.close()
            except Exception:
                pass
        _connection = None

    conn = await _get_connection()
    await conn.add_listener(CHANNEL_NAME, _notification_callback)
    logger.info("Reconnected pub/sub listener")


async def stop_listener() -> None:
    """Stop the listener and close connection."""
    global _listen_task, _connection

    if _listen_task:
        _listen_task.cancel()
        try:
            await _listen_task
        except asyncio.CancelledError:
            pass
        _listen_task = None
        logger.info("Stopped pub/sub keepalive task")

    async with _lock:
        if _connection and not _connection.is_closed():
            try:
                await _connection.remove_listener(CHANNEL_NAME, _notification_callback)
                await _connection.close()
                logger.info("Closed pub/sub connection")
            except Exception as e:
                logger.error(f"Error closing pub/sub connection: {e}")
        _connection = None
