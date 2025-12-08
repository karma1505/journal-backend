
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
from supabase import create_client, Client

app = FastAPI(title="Personal Journal API")

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://sginmhviemnhjorlzbme.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNnaW5taHZpZW1uaGpvcmx6Ym1lIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1OTE2ODE0MiwiZXhwIjoyMDc0NzQ0MTQyfQ.7bcsLn28W28w32cf0EmvW6V0QIpEN0-ztoHC2OhHrZ8")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "https://journal.karmanya.dev",  # Custom domain
        "https://journal-frontend-nk9hrrr8p-karma1505s-projects.vercel.app",
        "https://journal-frontend-swart.vercel.app",
        "https://journal-frontend-beta.vercel.app",
        "https://*.vercel.app"  # Allow all Vercel domains
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory only in development
if not os.getenv("VERCEL"):
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
    session = None
    try:
        session = SessionLocal()
        yield session
    except Exception as e:
        if session:
            try:
                await session.rollback()
            except:
                pass
        raise e
    finally:
        if session:
            try:
                await session.close()
            except Exception as close_error:
                print(f"Error closing session: {close_error}")
                # Don't raise the close error to avoid masking the original error

@app.on_event("startup")
async def startup():
    print("Starting database initialization...")
    try:
        # Test database connection first
        async with engine.begin() as conn:
            print("Database connection successful")
            # Create tables
            await conn.run_sync(EntryModel.metadata.create_all)
            print("Database tables created successfully")
    except Exception as e:
        print(f"Error creating database tables: {e}")
        print(f"Database URL: {os.getenv('DATABASE_URL', 'Not set')}")
        # Don't fail the startup if tables already exist

@app.get("/")
async def root():
    return {"message": "Journal API is running!", "status": "healthy"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "database": "connected"}

@app.post("/create-tables")
async def create_tables():
    """Manual endpoint to create database tables"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(EntryModel.metadata.create_all)
        return {"message": "Tables created successfully"}
    except Exception as e:
        return {"error": f"Failed to create tables: {str(e)}"}

@app.get("/test-db")
async def test_database():
    """Test database connection"""
    try:
        async with SessionLocal() as session:
            result = await session.execute(select(EntryModel))
            entries = result.scalars().all()
            return {"status": "connected", "entries_count": len(entries)}
    except Exception as e:
        return {"error": f"Database connection failed: {str(e)}"}

@app.get("/entries", response_model=List[EntryRead])
def get_entries():
    # Use synchronous Supabase REST API - much simpler and more reliable
    try:
        import requests
        
        # Use Supabase REST API to avoid all async connection issues
        supabase_url = os.getenv("SUPABASE_URL", "https://sginmhviemnhjorlzbme.supabase.co")
        supabase_key = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNnaW5taHZpZW1uaGpvcmx6Ym1lIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTkxNjgxNDIsImV4cCI6MjA3NDc0NDE0Mn0.nlTC3Q2AUogT3lLo685JAs14JV9DC-8CPE_4g2lGJ8E")
        
        response = requests.get(
            f"{supabase_url}/rest/v1/entries",
            headers={
                "apikey": supabase_key,
                "Authorization": f"Bearer {supabase_key}",
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code == 200:
            entries = response.json()
            return entries
        else:
            raise HTTPException(status_code=500, detail="Failed to fetch entries")
            
    except Exception as e:
        print(f"Error fetching entries: {e}")
        raise HTTPException(status_code=500, detail="Database error")

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
        
        if os.getenv("VERCEL"):
            # Production: Upload to Supabase Storage
            try:
                content_bytes = await image.read()
                file_path = f"blog-images/{unique_filename}"
                
                # Upload to Supabase Storage
                result = supabase.storage.from_("blog-images").upload(
                    file_path, 
                    content_bytes,
                    file_options={"content-type": image.content_type or "image/jpeg"}
                )
                
                # Check if upload was successful
                if hasattr(result, 'error') and result.error:
                    print(f"Supabase upload error: {result.error}")
                    image_path = None
                else:
                    # Get the public URL
                    public_url = supabase.storage.from_("blog-images").get_public_url(file_path)
                    image_path = public_url
                    print(f"Image uploaded successfully: {public_url}")
            except Exception as e:
                print(f"Error uploading to Supabase: {e}")
                image_path = None
        else:
            # Development: Save to local uploads directory
            image_path = f"uploads/{unique_filename}"
            with open(image_path, "wb") as buffer:
                content_bytes = await image.read()
                buffer.write(content_bytes)
    
    db_entry = EntryModel(title=title, content=content, image_path=image_path)
    db.add(db_entry)
    await db.commit()
    await db.refresh(db_entry)
    return db_entry

@app.get("/entries/{entry_id}", response_model=EntryRead)
def get_entry(entry_id: int):
    try:
        import requests
        
        supabase_url = os.getenv("SUPABASE_URL", "https://sginmhviemnhjorlzbme.supabase.co")
        supabase_key = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNnaW5taHZpZW1uaGpvcmx6Ym1lIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTkxNjgxNDIsImV4cCI6MjA3NDc0NDE0Mn0.nlTC3Q2AUogT3lLo685JAs14JV9DC-8CPE_4g2lGJ8E")
        
        response = requests.get(
            f"{supabase_url}/rest/v1/entries?id=eq.{entry_id}",
            headers={
                "apikey": supabase_key,
                "Authorization": f"Bearer {supabase_key}",
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code == 200:
            entries = response.json()
            if not entries:
                raise HTTPException(status_code=404, detail="Entry not found.")
            return entries[0]
        else:
            raise HTTPException(status_code=500, detail="Failed to fetch entry")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching entry: {e}")
        raise HTTPException(status_code=500, detail="Database error")

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
        # Delete old image if exists (only in development)
        if not os.getenv("VERCEL") and entry.image_path and os.path.exists(entry.image_path):
            os.remove(entry.image_path)
        
        # Save new image
        file_extension = image.filename.split('.')[-1] if '.' in image.filename else 'jpg'
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        image_path = f"uploads/{unique_filename}"
        
        if os.getenv("VERCEL"):
            # Production: Upload to Supabase Storage
            try:
                content_bytes = await image.read()
                file_path = f"blog-images/{unique_filename}"
                
                # Upload to Supabase Storage
                result = supabase.storage.from_("blog-images").upload(
                    file_path, 
                    content_bytes,
                    file_options={"content-type": image.content_type or "image/jpeg"}
                )
                
                # Check if upload was successful
                if hasattr(result, 'error') and result.error:
                    print(f"Supabase upload error: {result.error}")
                    entry.image_path = None
                else:
                    # Get the public URL
                    public_url = supabase.storage.from_("blog-images").get_public_url(file_path)
                    entry.image_path = public_url
                    print(f"Image uploaded successfully: {public_url}")
            except Exception as e:
                print(f"Error uploading to Supabase: {e}")
                entry.image_path = None
        else:
            # Development: Save to local uploads directory
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
    
    # Delete associated image file if exists (only in development)
    if not os.getenv("VERCEL") and entry.image_path and os.path.exists(entry.image_path):
        os.remove(entry.image_path)
    
    await db.delete(entry)
    await db.commit()
    return {"detail": "Entry deleted."}
