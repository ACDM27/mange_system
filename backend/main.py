"""
Student Information Service Platform - Backend API
FastAPI Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from config import settings
from database import init_db
import os

# Import routers
from routers import auth, common, student, admin, certificate

# Create FastAPI app
app = FastAPI(
    title="Student Information Service Platform API",
    description="Backend API for student achievement management and AI analysis",
    version="3.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add certificate access control middleware
from middleware.certificate_access import CertificateAccessMiddleware
app.add_middleware(CertificateAccessMiddleware)

# Create upload directory if not exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

# Mount static files for uploads
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include routers
app.include_router(auth.router)
app.include_router(common.router)
app.include_router(student.router)
app.include_router(admin.router)
app.include_router(certificate.router)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    print("Initializing database...")
    init_db()
    print("Database initialized successfully!")


@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Student Information Service Platform API",
        "version": "3.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
