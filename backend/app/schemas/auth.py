from pydantic import BaseModel, EmailStr


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
