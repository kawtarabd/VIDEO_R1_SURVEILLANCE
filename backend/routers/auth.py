# backend/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
import logging

from backend.database import get_db
from backend.models import User
from backend.schemas import UserCreate, UserLogin, UserResponse, Token
from backend.security import (
    get_password_hash,
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_current_admin_user 
)
from backend.config import settings
from typing import List         

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])

# AUTHENTICATION
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Inscription d'un nouvel utilisateur
    """
    logger.info(f"Tentative d'inscription: {user.username}")
    
    # Vérifier unicité username
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Le nom d'utilisateur '{user.username}' est déjà pris"
        )
    
    # Vérifier unicité email
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"L'email '{user.email}' est déjà utilisé"
        )
    
    # Créer utilisateur avec password hashé
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=get_password_hash(user.password)  # Bcrypt avec salt auto
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    logger.info(f" Utilisateur créé: id={db_user.id}, username={db_user.username}")
    return db_user


@router.post("/login", response_model=Token)
def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    logger.info(f"Tentative de connexion: {user_credentials.username}")
    
    user = authenticate_user(
        db, 
        user_credentials.username, 
        user_credentials.password
    )
    
    if not user:
        logger.warning(f"❌ Échec connexion: {user_credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiant ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        logger.warning(f"Compte désactivé: user_id={user.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte désactivé. Veuillez contacter l'administrateur."
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )
    
    logger.info(f"✅ Connexion réussie: user_id={user.id}")
    return {
        "access_token": access_token, 
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Récupérer le profil de l'utilisateur connecté
    
    """
    return current_user


@router.post("/logout")
def logout(current_user: User = Depends(get_current_active_user)):
    """
    Déconnexion 
    
    """
    logger.info(f"Déconnexion: user_id={current_user.id}")
    return {"message": "Déconnecté avec succès"}



@router.get("/admin/users", response_model=List[UserResponse])
def get_all_users(
    skip: int = 0,
    limit: int = 100,
    admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)                  
):
    """Lister tous les utilisateurs — Admin seulement"""
    users = db.query(User).offset(skip).limit(limit).all()
    return users                                    


@router.patch("/admin/users/{user_id}/toggle-active")
def toggle_user_active(
    user_id: int,
    admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Activer / Désactiver un utilisateur — Admin seulement"""
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )

    if user.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vous ne pouvez pas désactiver votre propre compte"
        )

    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)

    status_text = "activé" if user.is_active else "désactivé"
    logger.info(f"👤 User {user_id} {status_text} par admin {admin.id}")

    return {
        "message": f"Utilisateur {status_text} avec succès",
        "user_id": user_id,
        "is_active": user.is_active
    }


@router.get("/admin/stats")
def get_stats(
    admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Statistiques globales — Admin seulement"""
    from backend.models import Video, Detection, Conversation

    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    total_videos = db.query(Video).count()
    total_detections = db.query(Detection).count()
    total_conversations = db.query(Conversation).count()

    videos_completed = db.query(Video).filter(Video.status == "completed").count()
    videos_failed = db.query(Video).filter(Video.status == "failed").count()
    videos_processing = db.query(Video).filter(Video.status == "processing").count()

    return {
        "users": {
            "total": total_users,
            "active": active_users,
            "inactive": total_users - active_users
        },
        "videos": {
            "total": total_videos,
            "completed": videos_completed,
            "failed": videos_failed,
            "processing": videos_processing
        },
        "detections": total_detections,
        "conversations": total_conversations
    }