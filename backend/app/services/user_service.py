"""
User Service & Database Operations
"""

import uuid
from typing import Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.exceptions import AppException
from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.auth import UserCreate, UserUpdate


class UserService:
    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        """
        Retrieves a user by normalized email.
        """
        stmt = select(User).where(User.email == email.strip().lower())
        return db.scalars(stmt).first()

    @staticmethod
    def get_by_id(db: Session, user_id: Union[str, uuid.UUID]) -> Optional[User]:
        """
        Retrieves a user by UUID.
        """
        if isinstance(user_id, str):
            try:
                user_id = uuid.UUID(user_id)
            except ValueError:
                return None
        return db.get(User, user_id)

    @staticmethod
    def create(db: Session, obj_in: UserCreate) -> User:
        """
        Creates a new user with bcrypt password hashing.
        """
        normalized_email = obj_in.email.strip().lower()
        
        # Check if email is already registered
        existing_user = UserService.get_by_email(db, normalized_email)
        if existing_user:
            raise AppException(
                message="An account with this email address already exists.",
                code="EMAIL_ALREADY_EXISTS",
                status_code=409,
                details={"email": normalized_email},
            )

        db_user = User(
            email=normalized_email,
            hashed_password=get_password_hash(obj_in.password),
            full_name=obj_in.full_name.strip(),
            is_active=True,
            role="user",
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def authenticate(db: Session, email: str, password: str) -> Optional[User]:
        """
        Authenticates a user by email and password.
        """
        user = UserService.get_by_email(db, email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user


user_service = UserService()
