"""
Image processing service for photo uploads.
Handles compression, thumbnail generation, and EXIF stripping.
"""

import os
import uuid
from io import BytesIO
from typing import Tuple, Optional, Dict, Any
from PIL import Image, ExifTags
from config import get_settings

settings = get_settings()

# Supported image types
ALLOWED_MIME_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}

# Maximum dimensions for full-size images (will be scaled down if larger)
MAX_IMAGE_DIMENSION = 2048

# Thumbnail dimensions
THUMBNAIL_SIZE = (200, 200)

# Target size for compressed images (in KB)
TARGET_SIZE_KB = 500


def validate_image_type(mime_type: str) -> bool:
    """Check if the mime type is allowed."""
    return mime_type.lower() in ALLOWED_MIME_TYPES


def validate_image_size(size_bytes: int) -> bool:
    """Check if the file size is within limits."""
    max_bytes = settings.MAX_PHOTO_SIZE_MB * 1024 * 1024
    return size_bytes <= max_bytes


def generate_unique_filename(original_filename: str, mime_type: str) -> str:
    """Generate a unique filename while preserving the correct extension."""
    extension = ALLOWED_MIME_TYPES.get(mime_type.lower(), ".jpg")
    unique_id = uuid.uuid4().hex[:12]
    return f"{unique_id}{extension}"


def get_thumbnail_filename(filename: str) -> str:
    """Generate thumbnail filename from original filename."""
    name, ext = os.path.splitext(filename)
    return f"{name}_thumb{ext}"


def strip_exif_gps(image: Image.Image) -> Image.Image:
    """
    Remove GPS and sensitive EXIF data from image for privacy.
    Preserves orientation data for correct display.
    """
    # Get orientation before stripping EXIF
    orientation = None
    try:
        exif = image._getexif()
        if exif:
            for tag, value in exif.items():
                if ExifTags.TAGS.get(tag) == 'Orientation':
                    orientation = value
                    break
    except (AttributeError, KeyError, IndexError):
        pass

    # Create a new image without EXIF data
    data = list(image.getdata())
    image_without_exif = Image.new(image.mode, image.size)
    image_without_exif.putdata(data)

    # Apply orientation correction if needed
    if orientation:
        if orientation == 2:
            image_without_exif = image_without_exif.transpose(Image.FLIP_LEFT_RIGHT)
        elif orientation == 3:
            image_without_exif = image_without_exif.rotate(180)
        elif orientation == 4:
            image_without_exif = image_without_exif.rotate(180).transpose(Image.FLIP_LEFT_RIGHT)
        elif orientation == 5:
            image_without_exif = image_without_exif.rotate(-90, expand=True).transpose(Image.FLIP_LEFT_RIGHT)
        elif orientation == 6:
            image_without_exif = image_without_exif.rotate(-90, expand=True)
        elif orientation == 7:
            image_without_exif = image_without_exif.rotate(90, expand=True).transpose(Image.FLIP_LEFT_RIGHT)
        elif orientation == 8:
            image_without_exif = image_without_exif.rotate(90, expand=True)

    return image_without_exif


def extract_safe_metadata(image: Image.Image) -> Dict[str, Any]:
    """Extract non-sensitive metadata from image."""
    metadata = {
        "width": image.width,
        "height": image.height,
        "mode": image.mode,
        "format": image.format,
    }

    # Extract safe EXIF tags (exclude GPS and personal info)
    safe_tags = {'Make', 'Model', 'DateTime', 'DateTimeOriginal', 'Software'}
    try:
        exif = image._getexif()
        if exif:
            for tag, value in exif.items():
                tag_name = ExifTags.TAGS.get(tag, str(tag))
                if tag_name in safe_tags:
                    # Convert to string for JSON serialization
                    metadata[tag_name] = str(value) if value else None
    except (AttributeError, KeyError, IndexError):
        pass

    return metadata


def resize_image(image: Image.Image, max_dimension: int = MAX_IMAGE_DIMENSION) -> Image.Image:
    """Resize image if it exceeds max dimension while maintaining aspect ratio."""
    if max(image.width, image.height) <= max_dimension:
        return image

    if image.width > image.height:
        new_width = max_dimension
        new_height = int(image.height * (max_dimension / image.width))
    else:
        new_height = max_dimension
        new_width = int(image.width * (max_dimension / image.height))

    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)


def compress_image(
    image: Image.Image,
    target_size_kb: int = TARGET_SIZE_KB,
    mime_type: str = "image/jpeg"
) -> Tuple[BytesIO, int]:
    """
    Compress image to target size.
    Returns (BytesIO buffer, final size in bytes).
    """
    # Convert to RGB if necessary (for PNG with alpha)
    if image.mode in ('RGBA', 'LA', 'P'):
        if mime_type == "image/jpeg":
            # Convert to RGB for JPEG
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background

    # Determine format
    if mime_type == "image/png":
        format_type = "PNG"
        # PNG doesn't have quality setting, just optimize
        buffer = BytesIO()
        image.save(buffer, format=format_type, optimize=True)
        buffer.seek(0)
        return buffer, buffer.getbuffer().nbytes
    elif mime_type == "image/webp":
        format_type = "WEBP"
    else:
        format_type = "JPEG"

    # Binary search for optimal quality
    target_bytes = target_size_kb * 1024
    min_quality = 20
    max_quality = 95
    best_buffer = None
    best_size = 0

    while min_quality <= max_quality:
        quality = (min_quality + max_quality) // 2
        buffer = BytesIO()

        if format_type == "WEBP":
            image.save(buffer, format=format_type, quality=quality, method=4)
        else:
            image.save(buffer, format=format_type, quality=quality, optimize=True)

        buffer.seek(0)
        size = buffer.getbuffer().nbytes

        if size <= target_bytes:
            best_buffer = buffer
            best_size = size
            min_quality = quality + 1
        else:
            max_quality = quality - 1

    # If we couldn't get under target, use the last result
    if best_buffer is None:
        best_buffer = buffer
        best_size = size

    best_buffer.seek(0)
    return best_buffer, best_size


def create_thumbnail(image: Image.Image, size: Tuple[int, int] = THUMBNAIL_SIZE) -> Image.Image:
    """Create a thumbnail from the image."""
    # Make a copy to avoid modifying the original
    thumb = image.copy()
    thumb.thumbnail(size, Image.Resampling.LANCZOS)
    return thumb


def process_uploaded_image(
    file_content: bytes,
    original_filename: str,
    mime_type: str
) -> Tuple[BytesIO, BytesIO, str, str, int, Dict[str, Any]]:
    """
    Process an uploaded image file.

    Returns:
        - full_image_buffer: BytesIO of the processed full-size image
        - thumbnail_buffer: BytesIO of the thumbnail
        - filename: Generated unique filename
        - thumbnail_filename: Generated thumbnail filename
        - size_bytes: Size of the processed image
        - metadata: Safe metadata extracted from the image
    """
    # Open the image
    image = Image.open(BytesIO(file_content))

    # Extract metadata before stripping EXIF
    metadata = extract_safe_metadata(image)

    # Strip GPS and sensitive EXIF data
    image = strip_exif_gps(image)

    # Resize if too large
    image = resize_image(image)

    # Compress the image
    full_buffer, size_bytes = compress_image(image, TARGET_SIZE_KB, mime_type)

    # Create thumbnail
    thumbnail = create_thumbnail(image)
    thumb_buffer = BytesIO()
    if mime_type == "image/png":
        thumbnail.save(thumb_buffer, format="PNG", optimize=True)
    elif mime_type == "image/webp":
        thumbnail.save(thumb_buffer, format="WEBP", quality=80)
    else:
        # Convert to RGB for JPEG thumbnail if needed
        if thumbnail.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', thumbnail.size, (255, 255, 255))
            if thumbnail.mode == 'P':
                thumbnail = thumbnail.convert('RGBA')
            background.paste(thumbnail, mask=thumbnail.split()[-1] if thumbnail.mode == 'RGBA' else None)
            thumbnail = background
        thumbnail.save(thumb_buffer, format="JPEG", quality=80, optimize=True)
    thumb_buffer.seek(0)

    # Generate filenames
    filename = generate_unique_filename(original_filename, mime_type)
    thumbnail_filename = get_thumbnail_filename(filename)

    return full_buffer, thumb_buffer, filename, thumbnail_filename, size_bytes, metadata


def save_image_to_disk(buffer: BytesIO, filename: str) -> str:
    """
    Save image buffer to disk.
    Returns the full path to the saved file.
    """
    upload_dir = settings.PHOTO_UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)

    filepath = os.path.join(upload_dir, filename)
    with open(filepath, 'wb') as f:
        f.write(buffer.getvalue())

    return filepath


def delete_image_from_disk(filename: str) -> bool:
    """Delete an image file from disk. Returns True if successful."""
    filepath = os.path.join(settings.PHOTO_UPLOAD_DIR, filename)
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
    except OSError:
        pass
    return False
