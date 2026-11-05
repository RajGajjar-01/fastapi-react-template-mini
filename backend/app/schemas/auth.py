from typing import Annotated, Literal

from pydantic import BaseModel, EmailStr, Field, StringConstraints, field_validator

UserRole = Literal["user", "moderator", "admin"]

# Upper bounds keep stored profile text and request bodies small. They match
# the CHECK constraints added in the harden_profiles migration.
FULL_NAME_MAX = 200
AVATAR_URL_MAX = 2048
PASSWORD_MIN = 8
PASSWORD_MAX = 128

NewPassword = Annotated[str, Field(min_length=PASSWORD_MIN, max_length=PASSWORD_MAX)]
FullName = Annotated[str, StringConstraints(strip_whitespace=True, max_length=FULL_NAME_MAX)]


class LoginRequest(BaseModel):
    email: EmailStr
    # No minimum here: accounts made under an older policy must still log in.
    password: str = Field(min_length=1, max_length=PASSWORD_MAX)


class SignupRequest(BaseModel):
    email: EmailStr
    password: NewPassword
    full_name: FullName | None = None


class UpdateProfileRequest(BaseModel):
    full_name: FullName | None = None
    avatar_url: str | None = Field(default=None, max_length=AVATAR_URL_MAX)

    @field_validator("avatar_url")
    @classmethod
    def _avatar_must_be_http_url(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return None
        if not value.lower().startswith(("http://", "https://")):
            raise ValueError("avatar_url must be an http(s) URL")
        return value


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    # The one-time token hash from the recovery email link.
    token: str = Field(min_length=1, max_length=512)
    password: NewPassword


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=PASSWORD_MAX)
    new_password: NewPassword


class AssignRoleRequest(BaseModel):
    role: UserRole
