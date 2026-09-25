from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from app.auth.dependencies import get_current_user
from app.users.models import User
from app.ai.gemini_service import classify_image
from app.ai.schemas import ClassificationResponse

router = APIRouter(prefix="/api/ai", tags=["ai"])

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_SIZE_MB = 5


@router.post("/classify", response_model=ClassificationResponse)
async def classify_waste_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, or WEBP images are allowed")

    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > MAX_SIZE_MB:
        raise HTTPException(status_code=400, detail=f"Image must be under {MAX_SIZE_MB}MB")

    try:
        result = classify_image(contents, file.content_type)
    except Exception:
        raise HTTPException(status_code=502, detail="AI classification failed, please try again")

    return ClassificationResponse(**result)