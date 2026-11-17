"""
main.py — Point d'entrée du serveur.

Il ne contient plus les routes elles-mêmes : il crée l'application FastAPI,
la configure (CORS, gestion des erreurs) et branche les "routeurs" du dossier
routers/ (un fichier par sujet : comptes, schémas, tables, champs, relations).
"""
import os

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

import models
from database import engine
from routers import auth, fields, projects, relations, tables

# Crée les tables de la base si elles n'existent pas encore
# (remplacé plus tard par des migrations Alembic, étape 12)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SqlDesigner API",
    description="Conception visuelle de schémas de bases de données relationnelles.",
    version="2.0.0",
)

# ---------------------------------------------------------------------------
# CORS : quelles pages web ont le droit d'appeler ce serveur
# ---------------------------------------------------------------------------
allowed_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Erreurs : toujours une réponse JSON lisible {"detail": "..."}
# ---------------------------------------------------------------------------
@app.exception_handler(IntegrityError)
def integrity_error_handler(request: Request, exc: IntegrityError):
    """La base a refusé l'opération (doublon, lien impossible…) : erreur 409 au lieu de 500."""
    message = str(exc.orig).lower()
    if "unique" in message or "duplicate" in message:
        detail = "Ce nom existe déjà à cet endroit (doublon)."
    else:
        detail = "Opération refusée par la base de données (contrainte non respectée)."
    return JSONResponse(status_code=409, content={"detail": detail})


@app.exception_handler(RequestValidationError)
def validation_error_handler(request: Request, exc: RequestValidationError):
    """Données invalides : on renvoie un message simple et lisible."""
    messages = []
    for error in exc.errors():
        field = ".".join(str(part) for part in error["loc"] if part != "body")
        text = error["msg"].removeprefix("Value error, ")
        messages.append(f"{field} : {text}" if field else text)
    return JSONResponse(status_code=422, content={"detail": " · ".join(messages)})


# ---------------------------------------------------------------------------
# Les routes
# ---------------------------------------------------------------------------
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(tables.router)
app.include_router(fields.router)
app.include_router(relations.router)


@app.get("/", tags=["Divers"])
def health():
    """Permet de vérifier rapidement que le serveur tourne."""
    return {"status": "ok"}
