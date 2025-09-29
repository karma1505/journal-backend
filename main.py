
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import Entry as EntryModel
from database import SessionLocal, engine
import os
import uuid
from datetime import datetime

app = FastAPI(title="Personal Journal API")

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

class EntryCreate(BaseModel):
    title: str
    content: str

class EntryRead(BaseModel):
    id: int
    title: str
    content: str
    created_at: datetime
    image_path: Optional[str] = None
    class Config:
        from_attributes = True

async def get_db():
    async with SessionLocal() as session:
        yield session

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(EntryModel.metadata.create_all)

@app.get("/entries", response_model=List[EntryRead])
async def get_entries(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(EntryModel))
    entries = result.scalars().all()
    return entries

@app.post("/entries", response_model=EntryRead)
async def create_entry(
    title: str = Form(...),
    content: str = Form(...),
    image: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db)
):
    image_path = None
    if image:
        # Generate unique filename
        file_extension = image.filename.split('.')[-1] if '.' in image.filename else 'jpg'
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        image_path = f"uploads/{unique_filename}"
        
        # Save file
        with open(image_path, "wb") as buffer:
            content_bytes = await image.read()
            buffer.write(content_bytes)
    
    db_entry = EntryModel(title=title, content=content, image_path=image_path)
    db.add(db_entry)
    await db.commit()
    await db.refresh(db_entry)
    return db_entry

@app.get("/entries/{entry_id}", response_model=EntryRead)
async def get_entry(entry_id: int, db: AsyncSession = Depends(get_db)):
    entry = await db.get(EntryModel, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found.")
    return entry

class EntryUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

@app.patch("/entries/{entry_id}", response_model=EntryRead)
async def update_entry(
    entry_id: int, 
    entry_update: EntryUpdate,
    image: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db)
):
    entry = await db.get(EntryModel, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found.")
    
    # Handle image update
    if image:
        # Delete old image if exists
        if entry.image_path and os.path.exists(entry.image_path):
            os.remove(entry.image_path)
        
        # Save new image
        file_extension = image.filename.split('.')[-1] if '.' in image.filename else 'jpg'
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        image_path = f"uploads/{unique_filename}"
        
        with open(image_path, "wb") as buffer:
            content_bytes = await image.read()
            buffer.write(content_bytes)
        
        entry.image_path = image_path
    
    # Update only provided fields
    if entry_update.title is not None:
        entry.title = entry_update.title
    if entry_update.content is not None:
        entry.content = entry_update.content
    
    await db.commit()
    await db.refresh(entry)
    return entry

@app.delete("/entries/{entry_id}")
async def delete_entry(entry_id: int, db: AsyncSession = Depends(get_db)):
    entry = await db.get(EntryModel, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found.")
    
    # Delete associated image file if exists
    if entry.image_path and os.path.exists(entry.image_path):
        os.remove(entry.image_path)
    
    await db.delete(entry)
    await db.commit()
    return {"detail": "Entry deleted."}
