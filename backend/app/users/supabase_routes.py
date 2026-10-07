from enum import Enum

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr
from postgrest.exceptions import APIError

from app.auth.security import hash_password
from app.auth.security import verify_password
from app.auth.jwt_handler import create_access_token, decode_access_token
from app.db.supabase import get_supabase

router = APIRouter(prefix="/api/auth", tags=["auth"])
bearer_scheme = HTTPBearer(auto_error=False)


class UserRole(str, Enum):
    SELLER = "SELLER"
    BUYER = "BUYER"


class UserCreate(BaseModel):
    full_name: str
    business_name: str
    email: EmailStr
    phone: str
    password: str
    role: UserRole


class UserOut(BaseModel):
    id: int
    full_name: str
    business_name: str
    email: EmailStr
    phone: str
    role: UserRole
    is_active: bool


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


def get_authenticated_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        claims = decode_access_token(credentials.credentials)
        user_id = int(claims["sub"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    response = (
        get_supabase()
        .table("users")
        .select("id, full_name, business_name, email, phone, role, is_active")
        .eq("id", user_id)
        .limit(1)
        .execute()
    )
    if not response.data or not response.data[0]["is_active"]:
        raise HTTPException(status_code=401, detail="User account is unavailable")
    return response.data[0]


@router.post("/register", response_model=UserOut, status_code=201)
def register(user_in: UserCreate) -> UserOut:
    user = {
        "full_name": user_in.full_name,
        "business_name": user_in.business_name,
        "email": str(user_in.email),
        "phone": user_in.phone,
        "password_hash": hash_password(user_in.password),
        "role": user_in.role.value,
    }

    try:
        response = get_supabase().table("users").insert(user).execute()
    except APIError as exc:
        if "duplicate" in str(exc).lower() or "unique" in str(exc).lower():
            raise HTTPException(
                status_code=400,
                detail="An account with these details already exists",
            ) from exc
        raise HTTPException(
            status_code=502,
            detail="Could not create the account in Supabase",
        ) from exc

    if not response.data:
        raise HTTPException(
            status_code=502,
            detail="Supabase returned no account after registration",
        )

    return UserOut.model_validate(response.data[0])


@router.post("/login", response_model=TokenResponse)
def login(login_in: LoginRequest) -> TokenResponse:
    try:
        response = (
            get_supabase()
            .table("users")
            .select("id, role, password_hash, is_active")
            .eq("email", str(login_in.email))
            .limit(1)
            .execute()
        )
    except (httpx.HTTPError, APIError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Supabase is temporarily unavailable. Please try again.",
        ) from exc

    if not response.data:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user = response.data[0]
    try:
        password_matches = verify_password(
            login_in.password, user["password_hash"]
        )
    except (TypeError, ValueError):
        password_matches = False

    if not user["is_active"] or not password_matches:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": str(user["id"]), "role": user["role"]})
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserOut)
def read_current_user(
    current_user: dict = Depends(get_authenticated_user),
) -> UserOut:
    return UserOut.model_validate(current_user)
