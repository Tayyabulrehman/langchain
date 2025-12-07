from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    email: EmailStr






class UserGet(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    company: str


    class Config:
        orm_mode = True

class UserCreate(UserBase):
    password: str
    first_name: str
    last_name: str
    company: Optional[str]


class UserRead(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    first_name:  Optional[str]
    last_name:  Optional[str]
    company: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str


class PDFResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_size: int
    upload_date: datetime
    # page_count: Optional[int]
    description: Optional[str]

    class Config:
        from_attributes = True


class PDFUpdate(BaseModel):
    description: Optional[str] = None
    filename: Optional[str] = None


class PDFTextResponse(BaseModel):
    id: int
    filename: str
    extracted_text: str
    page_count: int


class TokenData(BaseModel):
    email: Optional[str] = None



