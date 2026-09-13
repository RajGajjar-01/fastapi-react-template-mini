from typing import Literal

from pydantic import BaseModel, EmailStr

UserRole = Literal["user", "moderator", "admin"]


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None


class UpdateProfileRequest(BaseModel):
    full_name: str | None = None
    avatar_url: str | None = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class AssignRoleRequest(BaseModel):
    role: UserRole