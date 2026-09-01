"""
FastAPI Reusable API Dependencies & Security Guards
"""

from typing import Optional
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.services.user_service import user_service

# Optional HTTPBearer to allow custom structured 401 JSON error responses
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Extracts, validates JWT access token and loads authenticated User.
    Raises 401 AppException on missing, invalid, or expired tokens.
    """
    if not credentials or not credentials.credentials:
        raise AppException(
            message="Authentication credentials were not provided.",
            code="NOT_AUTHENTICATED",
            status_code=401,
        )

    token = credentials.credentials
    payload = decode_access_token(token)
    user_id: Optional[str] = payload.get("sub")

    if not user_id:
        raise AppException(
            message="Authentication token is missing subject identity.",
            code="INVALID_TOKEN_SUBJECT",
            status_code=401,
        )

    user = user_service.get_by_id(db, user_id)
    if not user:
        raise AppException(
            message="User account associated with this token was not found.",
            code="USER_NOT_FOUND",
            status_code=401,
        )

    if not user.is_active:
        raise AppException(
            message="This user account is currently inactive.",
            code="USER_INACTIVE",
            status_code=403,
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency ensuring the authenticated user is active.
    """
    if not current_user.is_active:
        raise AppException(
            message="This user account is disabled.",
            code="USER_INACTIVE",
            status_code=403,
        )
    return current_user
