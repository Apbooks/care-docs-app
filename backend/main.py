from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

# Import database initialization
from database import init_db

# Import routes
from routes import auth, events, setup, quick_templates, settings as settings_routes, feeds, stream, recipients, photos, medications, med_reminders

# Import pub/sub service
from services import pubsub

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

# Create uploads directories if they don't exist
os.makedirs("photos", exist_ok=True)
os.makedirs(settings.AVATAR_UPLOAD_DIR, exist_ok=True)

# Mount static files for photos
app.mount("/photos", StaticFiles(directory="photos"), name="photos")
# Mount static files for avatars
app.mount("/avatars", StaticFiles(directory=settings.AVATAR_UPLOAD_DIR), name="avatars")

# Initialize database tables and start pub/sub listener
@app.on_event("startup")
async def startup_event():
    """Initialize database and start pub/sub listener on application startup"""
    init_db()
    # Register local broadcast handler and start listening for cross-worker events
    pubsub.register_handler(stream.local_broadcast)
    await pubsub.start_listener()


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up pub/sub listener on application shutdown"""
    await pubsub.stop_listener()

# Health check endpoint
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "Care Documentation API is running"}

# Serve setup.html
@app.get("/setup.html")
async def serve_setup():
    """Serve the setup HTML page"""
    from fastapi.responses import FileResponse
    import os
    setup_file = os.path.join(os.path.dirname(__file__), "setup.html")
    if os.path.exists(setup_file):
        return FileResponse(setup_file, media_type="text/html")
    return {"error": "Setup page not found"}

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
app.include_router(quick_templates.router, prefix="/api", tags=["quick-templates"])
app.include_router(settings_routes.router, prefix="/api", tags=["settings"])
app.include_router(feeds.router, prefix="/api", tags=["feeds"])
app.include_router(stream.router, prefix="/api", tags=["stream"])
app.include_router(recipients.router, prefix="/api", tags=["recipients"])
app.include_router(photos.router, prefix="/api/photos", tags=["photos"])
app.include_router(medications.router, prefix="/api/medications", tags=["medications"])
app.include_router(med_reminders.router, prefix="/api/med-reminders", tags=["med-reminders"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
