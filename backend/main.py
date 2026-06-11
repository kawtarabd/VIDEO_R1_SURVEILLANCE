from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from backend.config import settings
from backend.database import init_db
from backend.routers import auth, chat, video
from backend.security import get_current_active_user
from backend.models import User


init_db()          

# Creation du FASTAPI APP
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#  routers
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(video.router)

# STATIC FILES - Servir vidéos uploadées


@app.get("/uploads/{filename}")
async def serve_upload(
    filename: str,
    current_user: User = Depends(get_current_active_user)
):
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fichier non trouvé")
    return FileResponse(file_path)

@app.get("/")
def read_root():
    """API info"""
    return {
        "message": "Video-R1 Surveillance API",
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

# MAIN - Lancement serveur
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )