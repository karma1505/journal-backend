# Journal Backend API

A FastAPI backend for a personal journaling/blogging application.

## Features

- ✅ Create, Read, Update, Delete blog entries
- ✅ Image upload support
- ✅ SQLite for development, PostgreSQL for production
- ✅ Async/await support
- ✅ CORS enabled for frontend integration

## API Endpoints

- `GET /entries` - Get all blog entries
- `POST /entries` - Create new blog entry
- `GET /entries/{id}` - Get specific blog entry
- `PATCH /entries/{id}` - Update blog entry
- `DELETE /entries/{id}` - Delete blog entry

## Development Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the server:**
   ```bash
   uvicorn main:app --reload
   ```

3. **Access API docs:**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## Production Deployment

This backend is configured for deployment on Vercel with PostgreSQL.

### Environment Variables

- `DATABASE_URL` - Database connection string
- `POSTGRES_URL` - Vercel Postgres connection string (production)

### Database

- **Development:** SQLite (file-based)
- **Production:** PostgreSQL (Vercel Postgres)

## File Structure

```
backend/
├── main.py          # FastAPI application
├── models.py        # SQLAlchemy models
├── database.py      # Database configuration
├── requirements.txt # Python dependencies
├── vercel.json     # Vercel deployment config
└── .gitignore      # Git ignore rules
```

## Tech Stack

- **FastAPI** - Web framework
- **SQLAlchemy** - ORM
- **SQLite/PostgreSQL** - Database
- **Pydantic** - Data validation
- **Uvicorn** - ASGI server
