import cloudinary
import cloudinary.uploader
import logging
from src.config import settings

logger = logging.getLogger(__name__)

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET
)

def upload_image(file_path_or_bytes: str | bytes, folder: str = 'infographics') -> str:
    """Uploads an image to Cloudinary and returns the public URL."""
    try:
        response = cloudinary.uploader.upload(
            file_path_or_bytes,
            folder=folder,
            resource_type="image"
        )
        return response.get("secure_url", "")
    except Exception as e:
        logger.error(f"Failed to upload image to Cloudinary: {e}")
        return ""
