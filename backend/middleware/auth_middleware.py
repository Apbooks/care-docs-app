from fastapi import Request, HTTPException, status
from typing import Optional
from services.auth_service import decode_token


async def get_token_from_cookie(request: Request) -> Optional[str]:
    """
    Extract JWT token from HTTP-only cookie

    Args:
        request: FastAPI request object

    Returns:
        Token string if found, None otherwise
    """
    return request.cookies.get("access_token")


async def verify_auth_cookie(request: Request) -> dict:
    """
    Middleware to verify authentication from cookie

    Args:
        request: FastAPI request object

    Returns:
        Decoded token payload

    Raises:
        HTTPException: If token is invalid or missing
    """
    token = await get_token_from_cookie(request)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload
