"""
database.py — Connexion à la base de données.

Rôle : créer le "moteur" SQLAlchemy et fournir une session par requête.
La base utilisée est définie par la variable d'environnement DATABASE_URL :
  - en local, par défaut : un fichier SQLite (sqldzigner.db)
  - avec Docker : PostgreSQL (voir docker-compose.yml)
"""
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Charge le fichier .env s'il existe (réglages propres à chaque ordinateur)
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sqldzigner.db")
IS_SQLITE = DATABASE_URL.startswith("sqlite")

# SQLite n'accepte pas, par défaut, qu'une connexion soit utilisée
# par plusieurs "fils d'exécution" ; FastAPI en a besoin.
connect_args = {"check_same_thread": False} if IS_SQLITE else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

if IS_SQLITE:
    # SQLite ignore les clés étrangères (et donc ON DELETE CASCADE)
    # tant qu'on ne les active pas, à chaque nouvelle connexion.
    @event.listens_for(engine, "connect")
    def _activer_cles_etrangeres(dbapi_connection, _record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# Fabrique à sessions : chaque requête HTTP aura sa propre session.
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    """Classe mère de tous les modèles (voir models.py)."""


def get_db():
    """Ouvre une session pour une requête, et la ferme quoi qu'il arrive."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()