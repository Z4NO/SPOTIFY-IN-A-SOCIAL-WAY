# main.py

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from templates import templates
import secrets

from routes.player import player_operations  
from routes.playlist import playlist_operatiosn
from routes.tracks import tracks_operations
from core import auth

app = FastAPI()

# Configurar middleware de sesiones
app.add_middleware(
    SessionMiddleware,
    secret_key=secrets.token_urlsafe(32)  # Genera una clave secreta aleatoria
)

# No hace falta calcular rutas, están en el mismo nivel
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth.router)
app.include_router(player_operations.router)
app.include_router(playlist_operatiosn.router)
app.include_router(tracks_operations.router)