<<<<<<< HEAD
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError
from app.db.database import get_db
from app.users.models import User
from app.auth.jwt_handler import decode_access_token

bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user
=======
"""
Auth dependencies — stub implementation.

Until the real auth/JWT layer is wired in, callers pass a plain header:
  X-User-ID: user-seller-001   (or any id from store.users)

This keeps all marketplace endpoints fully testable right now.
When the DB + JWT auth is added, only this file changes.
"""

from fastapi import Depends, Header, HTTPException, status
from typing import Optional
from app.core import store


def get_current_user(x_user_id: Optional[str] = Header(None)) -> dict:
    """
    Resolve the current user from the X-User-ID header.
    Returns the user dict from the in-memory store.
    """
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-User-ID header. Pass a valid user id to authenticate.",
            headers={"WWW-Authenticate": "X-User-ID"},
        )
    user = store.users.get(x_user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"User '{x_user_id}' not found. "
                   f"Available: {list(store.users.keys())}",
        )
    return user


def require_role(*roles: str):
    """
    Dependency factory — enforce that the current user has one of the given roles.

    Usage:
        current_user: dict = Depends(require_role("seller"))
        current_user: dict = Depends(require_role("buyer", "admin"))
    """
    def _check(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user["role"] not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user['role']}' is not allowed. "
                       f"Required: {list(roles)}",
            )
        return current_user
    return _check
>>>>>>> origin/feature/marketplace
