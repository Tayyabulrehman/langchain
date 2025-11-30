import os
import shutil
import uuid
from datetime import timedelta
from typing import Optional, List

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db import engine, get_db
from app.services import models
from app.services.models import Base, PDFDocument, User
from app.services.shema import UserRead, UserCreate, Token, PDFResponse, TokenData
from app.utils.auth import get_password_hash, verify_password, ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, \
    SECRET_KEY, ALGORITHM, get_user_by_email, authenticate_user
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import FileResponse
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from datetime import datetime, timedelta
from typing import List, Optional
import os
import shutil
import uuid
from pydantic import BaseModel, EmailStr

import hashlib
from passlib.context import CryptContext
from jose import JWTError, jwt

from utils.embedder import embed_pdfs, delete_docs_by_metadata

app = FastAPI()
base_dir = os.path.abspath(os.path.dirname(__file__))
parent_dir = os.path.dirname(base_dir)

print("Base:", base_dir)
print("Parent:", parent_dir)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.post("/signup/", response_model=UserRead)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user exists
    db_user = db.execute(select(models.User).where(models.User.email == user.email)).scalar_one_or_none()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.post("/login/", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login and get access token"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, status
PDF_UPLOAD_DIR = "./uploaded_pdfs"


async def \
        get_current_user(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception

    user = get_user_by_email(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@app.post("/pdfs/", response_model=PDFResponse, status_code=status.HTTP_201_CREATED)
async def upload_pdf(
        file: UploadFile = File(...),
        description: Optional[str] = None,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """Upload a new PDF file (authenticated users only)"""

    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Generate unique filename
    file_extension = ".pdf"
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(PDF_UPLOAD_DIR, unique_filename)

    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Get file size
    file_size = os.path.getsize(file_path)

    # Extract text from PDF
    # extracted_text, page_count = extract_pdf_text(file_path)

    # Create database record linked to current user
    db_pdf = PDFDocument(
        filename=unique_filename,
        original_filename=file.filename,
        file_path=file_path,
        file_size=file_size,
        # extracted_text=extracted_text,
        # page_count=page_count,
        description=description,
        owner_id=current_user.id
    )

    db.add(db_pdf)
    db.commit()
    db.refresh(db_pdf)

    file_path=os.path.join(parent_dir,PDF_UPLOAD_DIR, db_pdf.filename)
    print(f"File path: {file_path}")
    print(f"File name: {db_pdf.filename}")
    print(f"File size: {db_pdf.file_size}")
    print(f"File description: {db_pdf.description}")
    print(f"File owner_id: {db_pdf.owner_id}")



    embed_pdfs(
        [file_path],
        metadata={
            "file_id": db_pdf.id,
            "user_id": db_pdf.owner_id,
        }
    )

    return db_pdf


@app.get("/pdfs/", response_model=List[PDFResponse])
async def list_user_pdfs(
        skip: int = 0,
        limit: int = 100,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """List all PDFs belonging to the current user"""
    pdfs = db.query(PDFDocument).filter(
        PDFDocument.owner_id == current_user.id
    ).offset(skip).limit(limit).all()
    return pdfs


@app.get("/pdfs/{pdf_id}", response_model=PDFResponse)
async def get_pdf_metadata(
        pdf_id: int,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """Get PDF metadata (only if owned by current user)"""
    pdf = db.query(PDFDocument).filter(
        PDFDocument.id == pdf_id,
        PDFDocument.owner_id == current_user.id
    ).first()

    if not pdf:
        raise HTTPException(status_code=404, detail="PDF not found")
    return pdf


from fastapi.responses import FileResponse


@app.get("/pdfs/{pdf_id}/download")
async def download_pdf(
        pdf_id: int,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """Download the original PDF file"""
    pdf = db.query(PDFDocument).filter(
        PDFDocument.id == pdf_id,
        PDFDocument.owner_id == current_user.id
    ).first()

    if not pdf:
        raise HTTPException(status_code=404, detail="PDF not found")

    if not os.path.exists(pdf.file_path):
        raise HTTPException(status_code=404, detail="PDF file not found on disk")

    return FileResponse(
        path=pdf.file_path,
        filename=pdf.original_filename,
        media_type='application/pdf'
    )


@app.delete("/pdfs/{pdf_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pdf(
        pdf_id: int,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """Delete a PDF document (only if owned by current user)"""
    pdf = db.query(PDFDocument).filter(
        PDFDocument.id == pdf_id,
        PDFDocument.owner_id == current_user.id
    ).first()

    if not pdf:
        raise HTTPException(status_code=404, detail="PDF not found")

    # Delete file from disk
    if os.path.exists(pdf.file_path):
        os.remove(pdf.file_path)

    delete_docs_by_metadata(
        index_name=os.getenv("PINECONE_INDEX_NAME"),
        metadata={"user_id": {"$eq": pdf.owner_id}, "file_id": {"$eq": pdf.id}}
    )

    # Delete from database
    db.delete(pdf)
    db.commit()

    return None

