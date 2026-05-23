"""
Modèles SQLAlchemy pour la base de données PostgreSQL

Responsabilités:
- Définir la structure des tables (ORM)
- Définir les relations entre tables (foreign keys)
- Définir les contraintes (unique, nullable, cascade)
- Mapper les objets Python ↔ Tables SQL


Tables:
1. users: Utilisateurs du système
2. conversations: Sessions de chat/analyse
3. messages: Messages dans les conversations
4. videos: Fichiers vidéo uploadés
5. detections: Résultats d'analyse

Relations:
User 1→N Conversations 1→N Messages
User 1→N Videos 1→N Detections
Conversation 1→N Videos 
"""


from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

# BASE CLASS - Toutes les tables héritent de Base

Base = declarative_base()

# TABLE: USERS - Utilisateurs du système

class User(Base):
    """
    Table des utilisateurs
    
    Responsabilités:
    - Authentification (username, password)
    - Autorisation (is_active, is_admin)
    - Ownership (videos, conversations)
    
    Relations:
    - 1 User → N Conversations
    - 1 User → N Videos
    
    Cascade Delete:
    - Si User supprimé → Conversations supprimées
    - Si User supprimé → Videos supprimées
    """
    """
    Nom de la table dans PostgreSQL
    """
    __tablename__ = "users"
    

 # COLONNES - Champs de la table
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))  
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)) 
    

    
    #Relations avec d'autres tables
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    videos = relationship("Video", back_populates="user", cascade="all, delete-orphan")

class Conversation(Base):

    """
    Table des conversations
    
    Responsabilités:
    - Organiser les sessions d'analyse
    - Grouper les messages
    - Lier avec les vidéos analysées
    
    Relations:
    - N Conversations → 1 User (propriétaire)
    - 1 Conversation → N Messages
    - 1 Conversation → N Videos (optionnel)
    
    Usage:
    - Interface ChatGPT-like
    - Historique par session
    - Context pour analyses
    """

    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), default="Nouvelle conversation")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))  
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)) 
    
    # Relations avec d'autres tables
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    videos = relationship("Video", back_populates="conversation")

class Message(Base):
     
    """
    Table des messages
    
    Responsabilités:
    - Stocker les messages user/assistant/system
    - Historique des conversations
    - Context pour analyses
    
    Relations:
    - N Messages → 1 Conversation
    
    Types de messages:
    - "user": Message utilisateur
    - "assistant": Réponse IA
    - "system": Métadonnées (video_uploaded, etc.)
    """
     
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)   # 'user', 'assistant' or 'system'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc)) 
    
     # Relations avec d'autres tables
    conversation = relationship("Conversation", back_populates="messages")

class Video(Base):

    """
    Table des vidéos
    
    Responsabilités:
    - Stocker métadonnées des vidéos
    - Tracking du statut d'analyse
    - Lien avec détections
    
    Relations:
    - N Videos → 1 User 
    - N Videos → 1 Conversation 
    - 1 Video → N Detections
    
    Statuts possibles:
    - "uploaded": Vidéo uploadée, prête
    - "processing": Analyse en cours
    - "completed": Analyse terminée
    - "failed": Analyse échouée
    """
    __tablename__ = "videos"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    duration = Column(Float)
    resolution = Column(String(20))
    fps = Column(Float)
    status = Column(String(20), default="uploaded")  # uploaded, processing, completed, failed
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    #  Relations avec d'autres tables
    user = relationship("User", back_populates="videos")
    conversation = relationship("Conversation", back_populates="videos")
    detections = relationship("Detection", back_populates="video", cascade="all, delete-orphan")

class Detection(Base):
    """
    Table des détections/analyses
    
    Responsabilités:
    - Stocker résultats d'analyses Video-R1
    - Historique des analyses par vidéo
    - Métadonnées de détection
    
    Relations:
    - N Detections → 1 Video
    
    Une vidéo peut avoir plusieurs détections:
    - Différents types (shoplifting, crowd, etc.)
    - Différentes plages temporelles
    - Différentes configurations
    - Historique des analyses
    """
    __tablename__ = "detections"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    detection_type = Column(String(50), nullable=False)  # shoplifting, description, etc.
    result = Column(JSON, nullable=False)
    confidence = Column(String(20))
    timestamp_start = Column(Float)
    timestamp_end = Column(Float)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
   #  Relations avec d'autres tables
    video = relationship("Video", back_populates="detections")