# backend/routers/chat.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging
from datetime import datetime, timezone
from backend.database import get_db
from backend.models import User, Conversation, Message
from backend.schemas import (
    ConversationCreate,
    ConversationResponse,
    MessageCreate,
    MessageResponse
)
from backend.security import get_current_active_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])



# CONVERSATIONS


@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(
    conversation: ConversationCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Créer une nouvelle session de chat"""
    db_conversation = Conversation(
        user_id=current_user.id,
        title=conversation.title
    )
    
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)
    
    logger.info(f"Conversation créée: id={db_conversation.id}, user={current_user.username}")
    return db_conversation


@router.get("/conversations", response_model=List[ConversationResponse])
def get_conversations(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Liste des conversations de l'utilisateur
    
    Tri: Plus récent en premier (updated_at DESC)
    Pagination: skip/limit pour performances
    """
    conversations = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).order_by(
        Conversation.updated_at.desc()
    ).offset(skip).limit(limit).all()
    
    return conversations


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Récupérer une conversation spécifique
 
    """
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id  # Critical: ownership check
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation non trouvée"
        )
    
    return conversation


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Supprimer une conversation
    
    Supprime aussi tous les messages (défini dans models.py)
    """
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation non trouvée"
        )
    
    db.delete(conversation)
    db.commit()
    
    logger.info(f"Conversation supprimée: id={conversation_id}")
    return None



# MESSAGES


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
def get_messages(
    conversation_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Messages d'une conversation
    
    Tri: Chronologique (created_at ASC) pour affichage chat
    """
    # Vérifier ownership conversation
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation non trouvée"
        )
    
    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(
        Message.created_at.asc()  # Ordre chronologique
    ).offset(skip).limit(limit).all()
    
    return messages


@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def create_message(
    conversation_id: int,
    message: MessageCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Ajouter un message à la conversation
    
    Roles possibles:
    - "user": Message utilisateur
    - "assistant": Réponse IA
    - "system": Métadonnées (video_uploaded, etc.)
    """
    # Vérifier ownership
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation non trouvée"
        )
    
    db_message = Message(
        conversation_id=conversation_id,
        role=message.role,
        content=message.content
    )
    
    db.add(db_message)
    conversation.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(db_message)

    return db_message