from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.users.models import User
from app.users.schemas import (
    UserCreate,
    UserOut,
    LoginRequest,
    TokenResponse,
    UserUpdate,
    ChangePasswordRequest,
)
from app.auth.security import hash_password, verify_password
from app.auth.jwt_handler import create_access_token
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserOut)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    if user_in.phone:
        existing_phone = db.query(User).filter(User.phone == user_in.phone).first()
        if existing_phone:
            raise HTTPException(status_code=400, detail="Phone number already registered")

    new_user = User(
        full_name=user_in.full_name,
        business_name=user_in.business_name,
        email=user_in.email,
        phone=user_in.phone,
        password_hash=hash_password(user_in.password),
        role=user_in.role,
    )
    db.add(new_user)
    try:
        db.commit()
    except IntegrityError:
        # Safety net for races or any other unique constraint: return a clean 400
        # instead of an unhandled 500 (which the browser reports as a CORS error).
        db.rollback()
        raise HTTPException(
            status_code=400, detail="An account with these details already exists"
        )
    db.refresh(new_user)
    return new_user


@router.post("/login", response_model=TokenResponse)
def login(login_in: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_in.email).first()
    if not user or not verify_password(login_in.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserOut)
def update_profile(
    updates: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if updates.full_name is not None:
        current_user.full_name = updates.full_name
    if updates.business_name is not None:
        current_user.business_name = updates.business_name
    if updates.phone is not None:
        current_user.phone = updates.phone

    db.commit()
    db.refresh(current_user)
    return current_user


@router.put("/change-password")
def change_password(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(body.current_password, current_user.password_hash):
        raise HTTPException(status_code=401, detail="Current password is incorrect")

    current_user.password_hash = hash_password(body.new_password)
    db.commit()
    return {"message": "Password updated successfully"}