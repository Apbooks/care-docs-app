from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from models.med_route import MedRoute
from models.care_recipient import CareRecipient
from models.user import User
from routes.auth import get_current_user, get_current_active_admin
from services.access_control import get_allowed_recipient_ids

router = APIRouter()


class MedRouteCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    recipient_id: str = Field(..., min_length=1)
    is_active: bool = True


class MedRouteUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=120)
    recipient_id: Optional[str] = None
    is_active: Optional[bool] = None


class MedRouteResponse(BaseModel):
    id: str
    name: str
    recipient_id: Optional[str]
    is_active: bool
    created_by_user_id: str
    created_by_name: Optional[str]
    created_at: str
    updated_at: str


def _to_response(route: MedRoute) -> MedRouteResponse:
    return MedRouteResponse(
        id=str(route.id),
        name=route.name,
        recipient_id=str(route.recipient_id) if route.recipient_id else None,
        is_active=route.is_active,
        created_by_user_id=str(route.created_by_user_id),
        created_by_name=route.created_by.username if route.created_by else None,
        created_at=route.created_at.isoformat(),
        updated_at=route.updated_at.isoformat()
    )


@router.get("/med-routes", response_model=List[MedRouteResponse])
async def list_med_routes(
    recipient_id: Optional[str] = Query(None),
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if include_inactive and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required to view inactive routes"
        )

    allowed = get_allowed_recipient_ids(db, current_user)
    if allowed is not None:
        if recipient_id and recipient_id not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this recipient"
            )
        if not allowed:
            return []

    query = db.query(MedRoute)
    if not include_inactive:
        query = query.filter(MedRoute.is_active.is_(True))
    if recipient_id:
        query = query.filter(MedRoute.recipient_id == recipient_id)
    elif allowed is not None:
        query = query.filter(MedRoute.recipient_id.in_(allowed))

    routes = query.order_by(MedRoute.name.asc()).all()
    return [_to_response(route) for route in routes]


@router.post("/med-routes", response_model=MedRouteResponse, status_code=status.HTTP_201_CREATED)
async def create_med_route(
    payload: MedRouteCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin)
):
    recipient = db.query(CareRecipient).filter(CareRecipient.id == payload.recipient_id).first()
    if not recipient or not recipient.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Recipient not found or inactive")

    route = MedRoute(
        name=payload.name.strip(),
        recipient_id=recipient.id,
        is_active=payload.is_active,
        created_by_user_id=current_admin.id
    )
    db.add(route)
    db.commit()
    db.refresh(route)
    return _to_response(route)


@router.patch("/med-routes/{route_id}", response_model=MedRouteResponse)
async def update_med_route(
    route_id: UUID,
    payload: MedRouteUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin)
):
    route = db.query(MedRoute).filter(MedRoute.id == route_id).first()
    if not route:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found")

    if payload.name is not None:
        route.name = payload.name.strip()
    if payload.is_active is not None:
        route.is_active = payload.is_active
    if payload.recipient_id is not None:
        recipient = db.query(CareRecipient).filter(CareRecipient.id == payload.recipient_id).first()
        if not recipient or not recipient.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Recipient not found or inactive")
        route.recipient_id = recipient.id

    route.updated_at = datetime.now(timezone.utc)
    db.add(route)
    db.commit()
    db.refresh(route)
    return _to_response(route)


@router.delete("/med-routes/{route_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_med_route(
    route_id: UUID,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin)
):
    route = db.query(MedRoute).filter(MedRoute.id == route_id).first()
    if not route:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found")
    db.delete(route)
    db.commit()
    return None
