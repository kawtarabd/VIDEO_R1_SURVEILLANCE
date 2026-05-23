# backend/routers/video.py
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
import logging

from backend.database import get_db
from backend.models import User, Video, Detection, Conversation
from backend.schemas import VideoResponse, DetectionRequest, DetectionResponse
from backend.security import get_current_active_user, get_current_admin_user
from backend.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/video", tags=["Video"])


# ─── VIDEO UPLOAD ─────────────────────────────────────────────────────────────

@router.post("/upload", response_model=VideoResponse, status_code=status.HTTP_201_CREATED)
async def upload_video(
    file: UploadFile = File(...),
    conversation_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    logger.info(f"📤 Upload: {file.filename} par {current_user.username}")

    # Valider extension
    video_extension = os.path.splitext(file.filename)[1].lower()
    if video_extension not in settings.ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Format non supporté. Acceptés: {', '.join(settings.ALLOWED_VIDEO_EXTENSIONS)}"
        )

    # Valider MIME type
    if file.content_type and not file.content_type.startswith("video/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le fichier uploadé doit être une vidéo"
        )

    # Lire le fichier une seule fois
    content = await file.read()
    real_size = len(content)

    if real_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le fichier est vide"
        )

    if real_size > settings.MAX_UPLOAD_SIZE:
        max_mb = settings.MAX_UPLOAD_SIZE / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Fichier trop volumineux (max {max_mb:.0f}MB, reçu {real_size / (1024 * 1024):.1f}MB)"
        )

    # Générer nom unique
    unique_filename = f"{uuid.uuid4()}{video_extension}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)

    # Sauvegarder le fichier
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(content)
    except Exception as e:
        logger.error(f"❌ Erreur sauvegarde: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Échec de la sauvegarde"
        )

    # Extraire métadonnées vidéo
    try:
        from src.video_utils import get_video_info
        video_info = get_video_info(file_path)

    except ImportError:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Module Video-R1 non disponible"
        )

    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Vidéo invalide ou corrompue: {str(e)}"
        )

    # Vérifier conversation ownership
    if conversation_id is not None:
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        ).first()

        if not conversation:
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation non trouvée"
            )

    # Créer enregistrement DB
    db_video = Video(
        user_id=current_user.id,
        conversation_id=conversation_id,
        filename=unique_filename,
        original_filename=file.filename,
        file_path=file_path,
        file_size=real_size,
        duration=video_info.get("duration_seconds"),
        resolution=f"{video_info.get('width')}x{video_info.get('height')}",
        fps=video_info.get("fps"),
        status="uploaded"
    )

    db.add(db_video)
    db.commit()
    db.refresh(db_video)

    logger.info(f"✅ Vidéo créée: id={db_video.id}, durée={db_video.duration}s")
    return db_video


# ─── GET VIDEOS ───────────────────────────────────────────────────────────────

@router.get("/videos", response_model=List[VideoResponse])
def get_user_videos(
    skip: int = 0,
    limit: int = 100,
    filename: Optional[str] = None,
    conversation_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    query = db.query(Video).filter(Video.user_id == current_user.id)

    if filename:
        query = query.filter(Video.original_filename == filename)

    if conversation_id is not None:
        query = query.filter(Video.conversation_id == conversation_id)

    videos = query.order_by(Video.created_at.desc()).offset(skip).limit(limit).all()
    return videos


@router.get("/videos/{video_id}", response_model=VideoResponse)
def get_video(
    video_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    video = db.query(Video).filter(
        Video.id == video_id,
        Video.user_id == current_user.id
    ).first()

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vidéo non trouvée"
        )

    return video


@router.delete("/videos/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_video(
    video_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    video = db.query(Video).filter(
        Video.id == video_id,
        Video.user_id == current_user.id
    ).first()

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vidéo non trouvée"
        )

    if os.path.exists(video.file_path):
        try:
            os.remove(video.file_path)
        except Exception as e:
            logger.error(f"❌ Erreur suppression fichier: {e}")

    db.delete(video)
    db.commit()

    logger.info(f"🗑️ Vidéo supprimée: id={video_id}")
    return None


# ─── DETECTION ────────────────────────────────────────────────────────────────

@router.post("/detect", response_model=dict)
async def detect_shoplifting(
    request: DetectionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    video = db.query(Video).filter(
        Video.id == request.video_id,
        Video.user_id == current_user.id
    ).first()

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vidéo non trouvée"
        )

    if video.status == "processing":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Analyse déjà en cours"
        )

    video.status = "processing"
    db.commit()

    user_params = request.dict()

    logger.info("=" * 70)
    logger.info("USER CONFIGURATION APPLIED:")
    logger.info("=" * 70)
    for key, value in user_params.items():
        if key != "video_id":
            logger.info(f"{key}: {value}")
    logger.info("=" * 70)

    from backend.services.video_r1 import VideoR1Service

    background_tasks.add_task(
        VideoR1Service.run_detection_task,
        video.id,
        video.file_path,
        user_params
    )

    logger.info(f"🚀 Analyse lancée: video_id={video.id}")

    return {
        "message": "Analyse lancée avec succès",
        "video_id": video.id,
        "status": "processing",
        "applied_parameters": {
            k: v for k, v in user_params.items() if k != "video_id"
        }
    }


@router.get("/videos/{video_id}/detections", response_model=List[DetectionResponse])
def get_video_detections(
    video_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    video = db.query(Video).filter(
        Video.id == video_id,
        Video.user_id == current_user.id
    ).first()

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vidéo non trouvée"
        )

    detections = db.query(Detection).filter(
        Detection.video_id == video_id
    ).order_by(
        Detection.created_at.desc()
    ).all()

    return detections


# ─── ADMIN ────────────────────────────────────────────────────────────────────

@router.get("/admin/videos", response_model=List[VideoResponse])
def get_all_videos(
    skip: int = 0,
    limit: int = 100,
    admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Voir toutes les vidéos — Admin seulement"""
    videos = db.query(Video).order_by(
        Video.created_at.desc()
    ).offset(skip).limit(limit).all()

    return videos