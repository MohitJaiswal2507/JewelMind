"""
Pydantic Schemas for Authentication and User Management
"""

import uuid
from datetime import datetime
from typing import Optional, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator

try:
    import email_validator
    from pydantic import EmailStr
except ImportError:
    from pydantic import StringConstraints
    from typing_extensions import Annotated
    EmailStr = Annotated[str, StringConstraints(pattern=r"^[^@]+@[^@]+\.[^@]+$")]


class UserBase(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    full_name: str = Field(..., min_length=2, max_length=100, description="Full name of user")


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128, description="Plaintext password")

    @field_validator("email", mode="after")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        if len(v.strip()) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        return v


class UserLogin(BaseModel):
    email: Union[EmailStr, str] = Field(..., description="Registered email address")
    password: str = Field(..., description="User password")

    @field_validator("email", mode="after")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    is_active: bool
    role: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Token validity duration in seconds")
    user: UserResponse


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    password: Optional[str] = Field(None, min_length=8, max_length=128)
