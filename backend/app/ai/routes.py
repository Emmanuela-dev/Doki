from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.auth.dependencies import get_current_user
from app.users.models import User
from app.db.database import get_db
from app.ai.gemini_service import classify_image
from app.ai.cloudinary_service import upload_image
from app.ai.models import Classification
from app.ai.schemas import ClassificationResponse, ConfirmClassification

router = APIRouter(prefix="/api/ai", tags=["ai"])

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_SIZE_MB = 5


@router.post("/classify", response_model=ClassificationResponse)
async def classify_waste_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, or WEBP images are allowed")

    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > MAX_SIZE_MB:
        raise HTTPException(status_code=400, detail=f"Image must be under {MAX_SIZE_MB}MB")

    try:
        ai_result = classify_image(contents, file.content_type)
    except Exception:
        raise HTTPException(status_code=502, detail="AI classification failed, please try again")

    try:
        image_url = upload_image(contents)
    except Exception:
        raise HTTPException(status_code=502, detail="Image upload failed, please try again")
    record = Classification(
        user_id=current_user.id,
        image_url=image_url,
        waste_type=ai_result["waste_type"],
        confidence=ai_result["confidence"],
        description=ai_result["description"],
        possible_uses=ai_result["possible_uses"],
        status="pending_review",
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/classifications", response_model=list[ClassificationResponse])
def list_my_classifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Classification)
        .filter(Classification.user_id == current_user.id)
        .order_by(Classification.created_at.desc())
        .all()
    )


@router.put("/classifications/{classification_id}/confirm", response_model=ClassificationResponse)
def confirm_classification(
    classification_id: int,
    updates: ConfirmClassification,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = (
        db.query(Classification)
        .filter(Classification.id == classification_id, Classification.user_id == current_user.id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Classification not found")

    if updates.waste_type is not None:
        record.waste_type = updates.waste_type
    if updates.description is not None:
        record.description = updates.description
    record.status = "confirmed"

    db.commit()
    db.refresh(record)
    return record