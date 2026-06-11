# backend/schemas.py
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, EmailStr, Field, computed_field


class UserBase(BaseModel):
    """Schéma de base pour un utilisateur"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr

class UserCreate(UserBase):
    """Schéma pour créer un utilisateur (avec mot de passe)"""
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    """Schéma pour la connexion"""
    username: str
    password: str

class UserResponse(UserBase):
    """Schéma pour les réponses (sans mot de passe)"""
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

"""Token JWT"""
class Token(BaseModel):

    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[int] = None


# CONVERSATION SCHEMAS - Gestion des sessions de chat


class ConversationBase(BaseModel):
    title: Optional[str] = "Nouvelle conversation"

class ConversationCreate(ConversationBase):
    pass

class ConversationResponse(ConversationBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# MESSAGE SCHEMAS


class MessageBase(BaseModel):
    content: str

class MessageCreate(MessageBase):
    role: str = Field(..., pattern="^(user|assistant|system)$")

class MessageResponse(MessageBase):
    id: int
    conversation_id: int
    role: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# VIDEO SCHEMAS


class VideoBase(BaseModel):
    original_filename: str

class VideoCreate(VideoBase):
    conversation_id: Optional[int] = None

class VideoResponse(VideoBase):
    id: int
    user_id: int
    conversation_id: Optional[int]
    filename: str
    file_size: Optional[int]
    duration: Optional[float]
    resolution: Optional[str]
    fps: Optional[float]
    status: str
    created_at: datetime

    @computed_field
    @property
    def url(self) -> str:
        return f"/uploads/{self.filename}"

    class Config:
        from_attributes = True


# DETECTION SCHEMAS


class DetectionBase(BaseModel):
    detection_type: str

class DetectionCreate(DetectionBase):
    video_id: int
    result: dict
    confidence: Optional[str]
    timestamp_start: Optional[float]
    timestamp_end: Optional[float]

class DetectionResponse(DetectionBase):
    id: int
    video_id: int
    result: dict
    confidence: Optional[str]
    timestamp_start: Optional[float]
    timestamp_end: Optional[float]
    created_at: datetime
    
    class Config:
        from_attributes = True


# DETECTION REQUEST - PARAMÈTRES CONFIGURABLES


class DetectionRequest(BaseModel):
    """
    Schéma unifié pour toutes les analyses vidéo
    
    Tous les paramètres du CLI sont exposés via l'UI
    L'utilisateur contrôle TOUS les paramètres
    Le backend applique exactement ce que l'utilisateur demande
    """
    
    video_id: int
    
    
    # DETECTION TYPE
    
    detection_type: Literal[
    "shoplifting",
    "suspicious_behavior",
    "checkout_interactions",
    "timeline",
    "crowd_analysis",
    "general"
   ]= Field(..., description="Type d'analyse vidéo")
    
    #  QUESTION PERSONNALISÉE
    
    custom_question: Optional[str] = Field(
        None,
        description="Question personnalisée qui remplace le prompt prédéfini"
    )
    
    
    # CORE PARAMETERS (required from user)
    
    frames: int = Field(
        ...,
        ge=16,
        le=128,
        description="Nombre de frames par segment (16-128) - CLI: --frames"
    )
    
    resolution: Literal[448, 560, 672] = Field(
    ...,
    description="Résolution des frames (448, 560, 672) - CLI: --resolution"
)
    
    smart: bool = Field(
        ...,
        description="Mode extraction intelligente - CLI: --smart"
    )
    
    
    # TIME RANGE - Seconds
    
    start: Optional[float] = Field(
        None,
        description="Temps de début en secondes - CLI: --start"
    )
    
    end: Optional[float] = Field(
        None,
        description="Temps de fin en secondes - CLI: --end"
    )
    
    
    # PLAGE TEMPORELLE - En Frames 
    
    start_frame: Optional[int] = Field(
        None,
        description="Frame de début - CLI: --start-frame"
    )
    
    end_frame: Optional[int] = Field(
        None,
        description="Frame de fin - CLI: --end-frame"
    )
    
    
    # PARAMÈTRES AVANCÉS
    
    multipass: bool = Field(
        ...,
        description="Analyse multi-passes scan rapide puis détaillé- CLI: --multipass"
    )
    
    cumulative: bool = Field(
        ...,
        description="Contexte cumulatif entre segments pour cohérence- CLI: --cumulative"
    )
    
    overlap: int = Field(
        0,
        ge=0,
        le=64,
        description="Chevauchement entre segments en frames (0-64) - CLI: --overlap"
    )
    
    span: Optional[float] = Field(
        None,
        description="Répartir frames sur X secondes - CLI: --span"
    )
    
    
    # PARAMÈTRES MULTIPASS
    
    pass1_frames: Optional[int] = Field(
        16,
        ge=8,
        le=64,
        description="Nombre de frames pour pass 1 (scan rapide) - CLI: --pass1-frames"
    )
    
    pass2_frames: Optional[int] = Field(
        64,
        ge=32,
        le=128,
        description="Nombre de frames pour pass 2 (analyse détaillée) - CLI: --pass2-frames"
    )
    
    pass2_window: Optional[float] = Field(
        8.0,
        description="Fenêtre temporelle en secondes pour pass 2 - CLI: --pass2-window"
    )
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "video_id": 1,
                "detection_type": "shoplifting",
                "custom_question": None,
                "frames": 32,
                "resolution": 560,
                "smart": True,
                "start": None,
                "end": None,
                "start_frame": None,
                "end_frame": None,
                "multipass": False,
                "cumulative": False,
                "overlap": 16,
                "span": None,
                "pass1_frames": 16,
                "pass2_frames": 64,
                "pass2_window": 8.0
            }
        }
