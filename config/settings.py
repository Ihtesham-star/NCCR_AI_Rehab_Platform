"""
Application Configuration Settings
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "NCCR Rehabilitation Analytics Platform"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database
    DATABASE_URL: str = "sqlite:///./nccr_rehabilitation.db"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Claude AI API
    CLAUDE_API_KEY: str = "your-claude-api-key-here"
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"
    CLAUDE_MAX_TOKENS: int = 4096
    
    # Data Paths
    DATA_IMPORT_PATH: str = "./data/import"
    PDF_STORAGE_PATH: str = "./data/pdfs"
    EXCEL_STORAGE_PATH: str = "./data/excel"
    EXPORT_PATH: str = "./data/exports"
    
    # Model Paths
    MODEL_PATH: str = "./models"
    ENABLE_GPU: bool = False
    BATCH_SIZE: int = 32
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # EMG Processing Configuration
    EMG_SAMPLING_RATE: int = 2000
    EMG_FILTER_LOWCUT: float = 20.0
    EMG_FILTER_HIGHCUT: float = 450.0
    EMG_FILTER_ORDER: int = 4
    
    # Balance Test Configuration
    BALANCE_STABILITY_THRESHOLD: float = 3.0
    BALANCE_TIME_THRESHOLD: int = 30
    
    # Clinical Test Standards
    GMFCS_LEVELS: int = 5
    MIN_6MWT_DISTANCE: int = 0
    MAX_6MWT_DISTANCE: int = 1000
    MIN_10MWT_TIME: float = 0.0
    MAX_10MWT_TIME: float = 300.0
    
    # Muscle Groups for EMG Analysis
    UPPER_BODY_MUSCLES: List[str] = [
        "BICEPS_FEM_LT", "BICEPS_FEM_RT",
        "VLO_LT", "VLO_RT"
    ]
    
    LOWER_BODY_MUSCLES: List[str] = [
        "GLUT_MED_LT", "GLUT_MED_RT",
        "GLUT_MAX_LT", "GLUT_MAX_RT",
        "ADDUCTORS_LT", "ADDUCTORS_RT",
        "TIB_ANT_LT", "TIB_ANT_RT",
        "MED_GAS_LT", "MED_GAS_RT",
        "GASTRO_RT", "GASTRO_LT"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings"""
    return settings


def ensure_directories():
    """Ensure all required directories exist"""
    directories = [
        settings.DATA_IMPORT_PATH,
        settings.PDF_STORAGE_PATH,
        settings.EXCEL_STORAGE_PATH,
        settings.EXPORT_PATH,
        settings.MODEL_PATH,
        os.path.dirname(settings.LOG_FILE)
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
