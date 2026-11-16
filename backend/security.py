"""
security.py — Mots de passe et jetons de connexion (JWT).

1. Mots de passe : on ne stocke JAMAIS un mot de passe en clair, seulement son
   "empreinte" calculée avec bcrypt (lent exprès, et salé : deux mots de passe
   identiques donnent deux empreintes différentes).
2. Jetons : après la connexion, le serveur remet à l'interface un jeton JWT signé
   avec SECRET_KEY. L'interface le renvoie à chaque requête (en-tête
   "Authorization: Bearer <jeton>") et get_current_user() retrouve l'utilisateur.
"""
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

import models
from database import get_db

# Clé secrète qui signe les jetons. En production, elle DOIT venir du fichier .env.
SECRET_KEY = os.getenv("SECRET_KEY", "cle-de-developpement-a-changer")
ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "1440"))  # 24 h

# bcrypt n'accepte pas plus de 72 octets
MAX_PASSWORD_BYTES = 72


# ---------------------------------------------------------------------------
# Mots de passe
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    """Calcule l'empreinte bcrypt d'un mot de passe."""
    data = password.encode("utf-8")
    if len(data) > MAX_PASSWORD_BYTES:
        raise HTTPException(status_code=400, detail="Mot de passe trop long (72 caractères maximum).")
    return bcrypt.hashpw(data, bcrypt.gensalt()).decode("utf-8")


def is_legacy_md5(password_hash: str) -> bool:
    """Les anciens comptes étaient hachés en MD5 : 32 caractères hexadécimaux."""
    return len(password_hash) == 32 and all(c in "0123456789abcdef" for c in password_hash)


def verify_password(password: str, password_hash: str) -> bool:
    """Vérifie un mot de passe (bcrypt, ou ancien MD5 pour les vieux comptes)."""
    if is_legacy_md5(password_hash):
        md5 = hashlib.md5(password.encode("utf-8")).hexdigest()
        return hmac.compare_digest(md5, password_hash)
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


# ---------------------------------------------------------------------------
# Jetons JWT
# ---------------------------------------------------------------------------

def create_access_token(user_id: int) -> str:
    """Fabrique un jeton qui dit « je suis l'utilisateur n° user_id », valable 24 h."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),                                   # "subject" : à qui appartient le jeton
        "iat": now,                                            # "issued at" : date de création
        "exp": now + timedelta(minutes=ACCESS_TOKEN_MINUTES),  # "expiration"
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    """Retrouve l'utilisateur à partir du jeton envoyé par l'interface ; sinon erreur 401."""
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Non connecté ou session expirée.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise unauthorized

    user = db.get(models.User, user_id)
    if user is None:
        raise unauthorized
    return user