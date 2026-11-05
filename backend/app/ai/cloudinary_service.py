import os
import base64
from dotenv import load_dotenv

load_dotenv()

try:
    import cloudinary
    import cloudinary.uploader

    cloudinary.config(
        cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
        api_key=os.getenv("CLOUDINARY_API_KEY"),
        api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    )
    CLOUDINARY_CONFIGURED = bool(
        os.getenv("CLOUDINARY_CLOUD_NAME")
        and os.getenv("CLOUDINARY_API_KEY")
        and os.getenv("CLOUDINARY_API_SECRET")
    )
except Exception:
    cloudinary = None
    CLOUDINARY_CONFIGURED = False


def upload_image(image_bytes: bytes) -> str:
    if CLOUDINARY_CONFIGURED and cloudinary:
        try:
            result = cloudinary.uploader.upload(image_bytes, folder="doki_waste_images")
            return result["secure_url"]
        except Exception:
            pass
    # Fallback: return a data URL for local development
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}"