import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Video-R1 Surveillance API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database - lit depuis .env
    DATABASE_URL: str 
    
    # Security - lit depuis .env
    SECRET_KEY: str 
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
        "http://localhost:5500",
        "http://localhost:5173",
    ]
    
    # File Upload
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 500 * 1024 * 1024  # 500MB
    ALLOWED_VIDEO_EXTENSIONS: list = [".mp4", ".avi", ".mov", ".mkv", ".webm"]
    
    # Video-R1 CLI
    VIDEO_R1_CLI_PATH: str = "src.cli"
    VIDEO_R1_TIMEOUT: int = 600  # 10 minutes
    
    # RunPod
    RUNPOD_API_KEY: Optional[str] = None
    RUNPOD_ENDPOINT_ID: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

settings = Settings()

# Create upload directory if not exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)