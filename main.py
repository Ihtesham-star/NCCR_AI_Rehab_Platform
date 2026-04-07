"""
FastAPI Backend - Main Application Entry Point
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import uvicorn

from config.settings import settings, ensure_directories
from database.connection import init_db, get_db
from api import patients, assessments, recommendations, data_import, clinical_documents

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Based System for Motor and Cognitive Function Assessment in Children with Disabilities"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(patients.router, prefix="/api/patients", tags=["Patients"])
app.include_router(assessments.router, prefix="/api/assessments", tags=["Assessments"])
app.include_router(recommendations.router, prefix="/api/recommendations", tags=["Recommendations"])
app.include_router(data_import.router, prefix="/api/import", tags=["Data Import"])
app.include_router(clinical_documents.router, prefix="/api/clinical-documents", tags=["Clinical Documents"])

# Mount static files for professional web UI
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    print(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    ensure_directories()
    init_db()
    print("✅ Application initialized successfully")


@app.get("/")
async def root():
    """Root endpoint - Redirect to Web UI"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/static/index.html")


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }


@app.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get system statistics"""
    from database.models import Patient, Assessment, EMGSession, BalanceTest
    
    patient_count = db.query(Patient).count()
    assessment_count = db.query(Assessment).count()
    emg_count = db.query(EMGSession).count()
    balance_count = db.query(BalanceTest).count()
    
    return {
        "total_patients": patient_count,
        "total_assessments": assessment_count,
        "emg_sessions": emg_count,
        "balance_tests": balance_count
    }


@app.post("/api/shutdown")
async def shutdown():
    """Shutdown the entire system (API + Streamlit)"""
    import os
    import signal
    import psutil
    
    # Kill all Python processes related to this application
    current_process = psutil.Process(os.getpid())
    parent = current_process.parent()
    
    # Find and kill Streamlit processes
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['cmdline']:
                cmdline_str = ' '.join(proc.info['cmdline'])
                # Kill Streamlit processes
                if 'streamlit' in cmdline_str.lower() and 'app_streamlit.py' in cmdline_str:
                    psutil.Process(proc.info['pid']).terminate()
                # Kill uvicorn/FastAPI processes
                elif 'uvicorn' in cmdline_str.lower() or 'main:app' in cmdline_str:
                    psutil.Process(proc.info['pid']).terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    # Kill self
    os.kill(os.getpid(), signal.SIGTERM)
    
    return {"status": "shutting down"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
