# main.py

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from templates import templates

from routes.player import player_operations  
from routes.playlist import playlist_operatiosn
from core import auth

app = FastAPI()

# No hace falta calcular rutas, están en el mismo nivel
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth.router)
app.include_router(player_operations.router)
app.include_router(playlist_operatiosn.router)
