from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core import store
from app.auth.jwt_handler import decode_access_token
from app.db.database import get_db
from app.users.models import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    x_user_id: Optional[str] = Header(None),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User | dict:
    """
    Resolve the current user from the X-User-ID header.

    Returns the user dictionary from the in-memory store.
    """

    if credentials is not None:
        try:
            claims = decode_access_token(credentials.credentials)
            user_id = int(claims["sub"])
        except (KeyError, TypeError, ValueError):
            raise HTTPException(status_code=401, detail="Invalid authentication token")

        user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
        if not user:
            raise HTTPException(status_code=401, detail="User account is unavailable")
        return user

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
            detail=(
                f"User '{x_user_id}' not found. "
                f"Available: {list(store.users.keys())}"
            ),
        )

    return user


def require_role(*roles: str):
    """
    Dependency factory that enforces user roles.

    Example:
        current_user: dict = Depends(require_role("seller"))
        current_user: dict = Depends(require_role("buyer", "admin"))
    """

    def _check(
        current_user: User | dict = Depends(get_current_user),
    ) -> dict:
        role = current_user.role.value.lower() if isinstance(current_user, User) else current_user["role"]
        if role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Role '{role}' is not allowed. "
                    f"Required: {list(roles)}"
                ),
            )

        if isinstance(current_user, User):
            return {"id": str(current_user.id), "role": role}
        return current_user

    return _check