# app/routers/player_operations.py

from fastapi import APIRouter, Query
from fastapi.responses import RedirectResponse, JSONResponse
import requests
import urllib.parse
from managers.BaseManager import BaseManager
from core.config import API_BASE_URL
import datetime

router = APIRouter(prefix="/player", tags=["player"])

@router.get("/top/{user_id}/{type}")
async def get_top_items(user_id: str, type: str):
    base_manager = BaseManager()
    token = base_manager._obtain_user_token(user_id)


    print(f"Token for user {user_id}: {token}")

    if base_manager._check_token_expired(user_id):
        refresh_token_obteined = base_manager._obtain_user_refresh_token(user_id)
        original_params = {"user_id": user_id, "type": type}
        params = {
            "rute_back": "player/top",
            "refresh_token": refresh_token_obteined,
            "id": user_id,
            "original_params": str(original_params)
        }
        return RedirectResponse(f"/refresh_token?{urllib.parse.urlencode(params)}")

    headers = {"Authorization": f"Bearer {token}"}
    params = {"type": type, "time_range": "long_term", "limit": 10}
    response = requests.get(f"{API_BASE_URL}me/top/{type}", headers=headers, params=params)

    if response.status_code != 200:
        return JSONResponse(content={"error": "Error al obtener las canciones/artistas", "detail": response.text}, status_code=500)

    top_items = response.json()
    if type in ["artists", "tracks"]:
        names = [item["name"] for item in top_items["items"]]
        return JSONResponse(content=names)

    return JSONResponse(content=top_items)

@router.get("/add_target_song_to_playlist/{user_id}/{target_id}/{playlist_id}")
async def add_song_to_playlist(user_id: str, target_id: str, playlist_id: str):
    base_manager = BaseManager()
    token = base_manager._obtain_user_token(user_id)

    if base_manager._check_token_expired(user_id):
        refresh_token_obteined = base_manager._obtain_user_refresh_token(user_id)
        original_params = {"user_id": user_id, "target_id": target_id, "playlist_id": playlist_id}
        params = {
            "rute_back": "player/add_target_song_to_playlist",
            "refresh_token": refresh_token_obteined,
            "id": user_id,
            "original_params": str(original_params)
        }
        return RedirectResponse(f"/refresh_token?{urllib.parse.urlencode(params)}")

    if not base_manager._check_user_is_login(target_id):
        return JSONResponse(content="El usuario target no está logueado en la aplicación", status_code=500)

    target_token = base_manager._obtain_user_token(target_id)
    headers = {"Authorization": f"Bearer {target_token}"}
    response = requests.get(f"{API_BASE_URL}me/player", headers=headers)

    if response.status_code != 200:
        return JSONResponse(content="Error al obtener la canción o no hay reproducción", status_code=500)

    song = response.json()
    if 'item' not in song:
        return JSONResponse(content=f"No track is currently playing: {song}", status_code=500)

    track_uri = song['item']['uri']
    track_id = song['item']['id']
    track_name = song['item']['name']

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    req_body = {"uris": [track_uri], "position": 0}

    response = requests.post(f"{API_BASE_URL}playlists/{playlist_id}/tracks", headers=headers, json=req_body)
    if response.status_code != 201:
        return JSONResponse(content=f"Error al añadir la canción: {response.text}", status_code=500)

    return JSONResponse(content={"message": "Canción añadida", "track_id": track_id, "track_name": track_name, "track_uri": track_uri})


@router.get("/check_if_user_is_logged/{id}")
async def check_if_user_is_logged(id: str):
    is_logged_in = BaseManager()._check_user_is_login(id)
    return JSONResponse(content={"is_logged_in": is_logged_in}, status_code=200 if is_logged_in else 404)
    
@router.get("/add_target_song_to_queue/{user_id}/{target_id}")
async def add_target_song_to_queue(user_id: str, target_id: str):
    base_manager = BaseManager()
    token = base_manager._obtain_user_token(user_id)

    if base_manager._check_token_expired(user_id):
        refresh_token_obteined = base_manager._obtain_user_refresh_token(user_id)
        original_params = {"user_id": user_id, "target_id": target_id}
        params = {
            "rute_back": "player/add_target_song_to_queue",
            "refresh_token": refresh_token_obteined,
            "id": user_id,
            "original_params": str(original_params)
        }
        return RedirectResponse(f"/refresh_token?{urllib.parse.urlencode(params)}")

    if not base_manager._check_user_is_login(target_id):
        return JSONResponse(content="El usuario target no está logueado", status_code=500)

    target_token = base_manager._obtain_user_token(target_id)

    if base_manager._check_token_expired(target_id):
        refresh_token_obteined = base_manager._obtain_user_refresh_token(target_id)
        original_params = {"user_id": user_id, "target_id": target_id}
        params = {
            "rute_back": "player/add_target_song_to_queue",
            "refresh_token": refresh_token_obteined,
            "id": target_id,
            "original_params": str(original_params)
        }
        return RedirectResponse(f"/refresh_token?{urllib.parse.urlencode(params)}")

    user_info = requests.get(f"{API_BASE_URL}me", headers={"Authorization": f"Bearer {token}"}).json()
    if user_info.get("product") == "free":
        return JSONResponse(content="El usuario no es premium", status_code=501)

    response = requests.get(f"{API_BASE_URL}me/player", headers={"Authorization": f"Bearer {target_token}"})
    if response.status_code != 200:
        return JSONResponse(content="Error al obtener la canción del target", status_code=500)

    song = response.json()
    if 'item' not in song:
        return JSONResponse(content=f"No hay canción en reproducción: {song}", status_code=500)

    track_uri = song['item']['uri']
    track_id = song['item']['id']
    track_name = song['item']['name']

    response = requests.post(
        f"{API_BASE_URL}me/player/queue",
        headers={"Authorization": f"Bearer {token}"},
        params={"uri": track_uri}
    )

    return JSONResponse(content={"message": "Canción en cola", "track_uri": track_uri, "track_name": track_name, "track_id": track_id})


@router.get('/friends_activity/{user_id}')
async def get_friends_activity(user_id: str):
    base_manager = BaseManager()

    if base_manager._check_token_expired(user_id):
        refresh_token_obteined = base_manager._obtain_user_refresh_token(user_id)
        original_params = {"user_id": user_id}
        params = {
            "rute_back": "player/friends_activity",
            "refresh_token": refresh_token_obteined,
            "id": user_id,
            "original_params": str(original_params)
        }
        return RedirectResponse(f"/refresh_token?{urllib.parse.urlencode(params)}")
    

    token = base_manager._obtain_user_token(user_id)

    # Primero antes de nada debemos obtener la canción que está escuchando el usuario
    headers = {
        'Authorization': f'Bearer {token}'
    }

    # Obtenemos la canción que está escuchando el usuario y guaradamos los id de los artistas
    response = requests.get(API_BASE_URL + 'me/player', headers=headers)

    if response.status_code != 200:
        return JSONResponse(content={"error": "Error al obtener la canción actual del usuario", "detail": response.text}, status_code=500)
    
    informarion = response.json()

    headers = {
        'Authorization': f'Bearer {token}'
    }

    # Obtenemos la informacion de las 3 reprudcciones mas recientes del usuario
    response = requests.get(API_BASE_URL + 'me/player/recently-played?limit=3', headers=headers)

    if response.status_code != 200:
        return JSONResponse(content={"error": "Error al obtener la actividad reciente del usuario", "detail": response.text}, status_code=500)
    
    recent_plays = response.json()

    informacion_extraida = {
        "device_type": informarion['device']['type'],
        "volume_percent": informarion['device']['volume_percent'],
        "currently_playing": informarion['item']['name'],
        "currently_playing_type": informarion['currently_playing_type'],
        "last_played": [item['track']['name'] for item in recent_plays['items']],
    }

    return JSONResponse(content=informacion_extraida)

@router.get('/follow/{user_id}/{target_id}')
async def follow_user(user_id: str, target_id: str):
    base_manager = BaseManager()
    token = base_manager._obtain_user_token(user_id)

    if base_manager._check_token_expired(user_id):
        refresh_token_obteined = base_manager._obtain_user_refresh_token(user_id)
        original_params = {"user_id": user_id, "target_id": target_id}
        params = {
            "rute_back": "player/follow",
            "refresh_token": refresh_token_obteined,
            "id": user_id,
            "original_params": str(original_params)
        }
        return RedirectResponse(f"/refresh_token?{urllib.parse.urlencode(params)}")

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.put(f"{API_BASE_URL}me/following?type=user&ids={target_id}", headers=headers)

    if response.status_code == 204:
        return JSONResponse(content={"message": "Usuario seguido correctamente"}, status_code=200)
    else:
        return JSONResponse(content={"error": "Error al seguir al usuario", "detail": response.text}, status_code=500)
    
@router.get('/unfollow/{user_id}/{target_id}')
async def unfollow_user(user_id: str, target_id: str):
    base_manager = BaseManager()
    token = base_manager._obtain_user_token(user_id)

    if base_manager._check_token_expired(user_id):
        refresh_token_obteined = base_manager._obtain_user_refresh_token(user_id)
        original_params = {"user_id": user_id, "target_id": target_id}
        params = {
            "rute_back": "player/unfollow",
            "refresh_token": refresh_token_obteined,
            "id": user_id,
            "original_params": str(original_params)
        }
        return RedirectResponse(f"/refresh_token?{urllib.parse.urlencode(params)}")

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.delete(f"{API_BASE_URL}me/following?type=user&ids={target_id}", headers=headers)

    if response.status_code == 204:
        return JSONResponse(content={"message": "Usuario dejado de seguir correctamente"}, status_code=200)
    else:
        return JSONResponse(content={"error": "Error al dejar de seguir al usuario", "detail": response.text}, status_code=500)
    
