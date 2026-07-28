from typing import Optional

from pydantic import BaseModel, EmailStr, model_validator


class UserCreate(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

class UserLogin(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

    @model_validator(mode="after")
    def validate_login(self):
        if not self.email and not self.phone:
            raise ValueError("Either email or phone must be provided.")
        return self


class UserResponse(BaseModel):
    id: int
    name: str
    email: Optional[str]
    phone: Optional[str]

    class Config:
        from_attributes = True