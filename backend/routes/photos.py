from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from uuid import UUID

from database import get_db
from models.user import User
from models.event import Event
from models.photo import Photo
from routes.auth import get_current_user
from services.image_service import (
    validate_image_type,
    validate_image_size,
    process_uploaded_image,
    save_image_to_disk,
    delete_image_from_disk,
)

router = APIRouter()


class PhotoResponse(BaseModel):
    id: str
    event_id: str
    filename: str
    original_filename: Optional[str]
    thumbnail_filename: Optional[str]
    size_bytes: int
    mime_type: str
    metadata: Dict[str, Any]
    url: str
    thumbnail_url: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


def photo_to_response(photo: Photo) -> PhotoResponse:
    """Convert Photo model to response schema."""
    return PhotoResponse(
        id=str(photo.id),
        event_id=str(photo.event_id),
        filename=photo.filename,
        original_filename=photo.original_filename,
        thumbnail_filename=photo.thumbnail_filename,
        size_bytes=photo.size_bytes,
        mime_type=photo.mime_type,
        metadata=photo.metadata or {},
        url=f"/photos/{photo.filename}",
        thumbnail_url=f"/photos/{photo.thumbnail_filename}" if photo.thumbnail_filename else None,
        created_at=photo.created_at.isoformat() if photo.created_at else None,
    )


@router.post("/", response_model=PhotoResponse, status_code=status.HTTP_201_CREATED)
async def upload_photo(
    file: UploadFile = File(..., description="Image file to upload"),
    event_id: str = Form(..., description="ID of the event to attach photo to"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a photo and attach it to an event.

    Supported formats: JPEG, PNG, WebP, GIF
    Max file size: 10MB (configurable)

    The image will be:
    - Compressed to reduce file size
    - Resized if larger than 2048px
    - Stripped of GPS/location EXIF data for privacy
    - A thumbnail will be generated for list views
    """
    # Validate event exists
    try:
        event_uuid = UUID(event_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid event_id format"
        )

    event = db.query(Event).filter(Event.id == event_uuid).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    # Validate file type
    if not file.content_type or not validate_image_type(file.content_type):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Supported formats: JPEG, PNG, WebP, GIF"
        )

    # Read file content
    content = await file.read()

    # Validate file size
    if not validate_image_size(len(content)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Maximum size is 10MB"
        )

    try:
        # Process the image
        full_buffer, thumb_buffer, filename, thumbnail_filename, size_bytes, metadata = process_uploaded_image(
            content,
            file.filename or "photo.jpg",
            file.content_type
        )

        # Save files to disk
        save_image_to_disk(full_buffer, filename)
        save_image_to_disk(thumb_buffer, thumbnail_filename)

        # Create database record
        photo = Photo(
            event_id=event_uuid,
            filename=filename,
            original_filename=file.filename,
            thumbnail_filename=thumbnail_filename,
            size_bytes=size_bytes,
            mime_type=file.content_type,
            metadata=metadata,
        )

        db.add(photo)
        db.commit()
        db.refresh(photo)

        return photo_to_response(photo)

    except Exception as e:
        # Clean up any saved files on error
        delete_image_from_disk(filename)
        delete_image_from_disk(thumbnail_filename)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process image: {str(e)}"
        )


@router.get("/event/{event_id}", response_model=List[PhotoResponse])
async def get_event_photos(
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all photos attached to an event."""
    # Verify event exists
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    photos = db.query(Photo).filter(Photo.event_id == event_id).order_by(Photo.created_at).all()

    return [photo_to_response(photo) for photo in photos]


@router.get("/{photo_id}", response_model=PhotoResponse)
async def get_photo(
    photo_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific photo by ID."""
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found"
        )

    return photo_to_response(photo)


@router.delete("/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_photo(
    photo_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a photo."""
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found"
        )

    # Delete files from disk
    delete_image_from_disk(photo.filename)
    if photo.thumbnail_filename:
        delete_image_from_disk(photo.thumbnail_filename)

    # Delete database record
    db.delete(photo)
    db.commit()

    return None


@router.get("/count/{event_id}")
async def get_photo_count(
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the count of photos for an event (lightweight endpoint for badges)."""
    count = db.query(Photo).filter(Photo.event_id == event_id).count()
    return {"event_id": str(event_id), "count": count}
