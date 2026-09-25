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
