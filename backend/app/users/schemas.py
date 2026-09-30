from pydantic import BaseModel, EmailStr
from app.users.models import UserRole


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
    email: str
    phone: str
    role: UserRole
    is_active: bool

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserUpdate(BaseModel):
    full_name: str | None = None
    business_name: str | None = None
    phone: str | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str