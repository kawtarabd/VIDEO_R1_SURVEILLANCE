from typing import Optional
import logging
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import get_db
from backend.models import User
from backend.schemas import TokenData
from datetime import datetime, timedelta, timezone  

logger = logging.getLogger(__name__)

# Configuration du hashing de mots de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuration OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie un mot de passe contre son hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash un mot de passe avec bcrypt"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crée un token JWT"""

    to_encode = data.copy()

    # Définir l'expiration
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
     # Ajouter l'expiration aux données
    to_encode.update({"exp": expire})

    # Encoder le token
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[TokenData]:
    """
     Décode et valide un token JWT
    
    Returns:
        TokenData si valide, None sinon
    """
    try:

        # Décoder le token
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
       
       # Extraire le user_id
        user_id = payload.get("sub")
        if user_id is None:
            logger.warning("JWT missing sub field")
            return None

        return TokenData(user_id=int(user_id))
    except JWTError as e:
        logger.warning(f"JWT decode failed: {e}")
        return None

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    Authentifie un utilisateur
    """

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
     Récupère l'utilisateur courant depuis le token JWT
    
    Utilisé comme dépendance dans les routes protégées
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Décoder le token
    token_data = decode_access_token(token)
    if token_data is None or token_data.user_id is None:
        raise credentials_exception
    
    # Récupérer l'utilisateur de la base de données
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if user is None:
        raise credentials_exception
    
    # Vérifier que l'utilisateur est actif
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Vérifie que l'utilisateur connecté est admin.
    Utilisé comme dépendance dans les routes réservées aux admins.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé. Droits administrateur requis."
        )
    return current_user