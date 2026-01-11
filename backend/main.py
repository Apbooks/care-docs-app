from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

# Import database initialization
from database import init_db

# Import routes
from routes import auth, events, setup
# from routes import photos, reminders, sync, reports

# Import settings
from config import get_settings

settings = get_settings()

app = FastAPI(
    title="Care Documentation API",
    description="API for tracking care activities, medications, and feeding schedules",
    version="0.1.0"
)

# CORS configuration - read from environment settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create photos directory if it doesn't exist
os.makedirs("photos", exist_ok=True)

# Mount static files for photos
app.mount("/photos", StaticFiles(directory="photos"), name="photos")

# Initialize database tables
@app.on_event("startup")
async def startup_event():
    """Initialize database on application startup"""
    init_db()

# Health check endpoint
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "Care Documentation API is running"}

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Care Documentation API",
        "version": "0.1.0",
        "docs": "/docs"
    }

# Register routes
app.include_router(setup.router, prefix="/api/setup", tags=["setup"])
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(events.router, prefix="/api/events", tags=["events"])
# app.include_router(photos.router, prefix="/api/photos", tags=["photos"])
# app.include_router(reminders.router, prefix="/api/reminders", tags=["reminders"])
# app.include_router(sync.router, prefix="/api/sync", tags=["sync"])
# app.include_router(reports.router, prefix="/api/reports", tags=["reports"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
