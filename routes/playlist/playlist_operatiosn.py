# app/routers/playlists.py

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, JSONResponse
import requests
from managers.BaseManager import BaseManager
from models.User import User
from core.config import API_BASE_URL

router = APIRouter(prefix="/playlists", tags=["playlists"])


@router.get("/playlists/{user_id}")
def get_playlists_by_user(user_id: str):
    base_manager = BaseManager()
    token = base_manager._obtain_user_token(user_id)

    if base_manager._check_token_expired(user_id):
        refresh_token_obteined = base_manager._obtain_user_refresh_token(user_id)
        original_params = {"user_id": user_id}
        return RedirectResponse(
            url=f"/refresh_token?rute_back=playlists/playlists&refresh_token={refresh_token_obteined}&id={user_id}&original_params={original_params}"
        )

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(API_BASE_URL + 'me/playlists', headers=headers)
    if response.status_code != 200:
        return JSONResponse(content={"error": response.text}, status_code=500)

    return JSONResponse(content=response.json())


@router.get("/check_collaborative_playlist/{user_id}")
def check_collaborative_playlist(user_id: str):
    base_manager = BaseManager()
    token = base_manager._obtain_user_token(user_id)

    if base_manager._check_token_expired(user_id):
        refresh_token_obteined = base_manager._obtain_user_refresh_token(user_id)
        original_params = {"user_id": user_id}
        return RedirectResponse(
            url=f"/refresh_token?rute_back=playlists/check_collaborative_playlist&refresh_token={refresh_token_obteined}&id={user_id}&original_params={original_params}"
        )

    if not base_manager._user_has_coop_playlists(user_id):
        return JSONResponse(content={"error": "El usuario no tiene playlists colaborativas"}, status_code=500)

    coops_data = base_manager._obtain_coop_playlists(user_id)
    return JSONResponse(content={"message": "El usuario tiene playlists colaborativas", "playlists": coops_data})


@router.get("/create_playlist/{user_id}/{playlist_name}/{playlist_description}/{is_public}/{is_collaborative}")
def create_playlist(user_id: str, playlist_name: str, playlist_description: str, is_public: str, is_collaborative: str):
    base_manager = BaseManager()
    token = base_manager._obtain_user_token(user_id)

    if is_collaborative == 'True':
        is_collaborative = True
        is_public = False
    else:
        is_collaborative = False
        is_public = True

    if base_manager._check_token_expired(user_id):
        refresh_token_obteined = base_manager._obtain_user_refresh_token(user_id)
        original_params = {
            "user_id": user_id,
            "playlist_name": playlist_name,
            "playlist_description": playlist_description,
            "is_public": str(is_public),
            "is_collaborative": str(is_collaborative)
        }
        return RedirectResponse(
            url=f"/refresh_token?rute_back=playlists/create_playlist&refresh_token={refresh_token_obteined}&id={user_id}&original_params={original_params}"
        )

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(API_BASE_URL + 'me', headers=headers)
    if response.status_code != 200:
        return JSONResponse(content={"error": response.text}, status_code=500)
    spotify_user_id = response.json()['id']

    data = {
        'name': playlist_name,
        'description': playlist_description,
        'public': is_public,
        'collaborative': is_collaborative
    }

    response = requests.post(API_BASE_URL + f'users/{spotify_user_id}/playlists', headers=headers, json=data)
    if response.status_code != 201:
        return JSONResponse(content={"error": response.text}, status_code=500)

    playlist = response.json()
    base_manager._add_coop_playlists(user_id, [playlist['id']])

    return JSONResponse(content=playlist)


@router.get("/add_song_to_playlist/{user_id}/{playlist_id}/{track_uri}")
def add_songs_to_playlist(user_id: str, playlist_id: str, track_uri: str):
    base_manager = BaseManager()
    token = base_manager._obtain_user_token(user_id)

    if base_manager._check_token_expired(user_id):
        refresh_token_obteined = base_manager._obtain_user_refresh_token(user_id)
        original_params = {
            "user_id": user_id,
            "playlist_id": playlist_id,
            "track_uri": track_uri
        }
        return RedirectResponse(
            url=f"/refresh_token?rute_back=playlists/add_song_to_playlist&refresh_token={refresh_token_obteined}&id={user_id}&original_params={original_params}"
        )

    headers = {"Authorization": f"Bearer {token}"}
    data = {"uris": [track_uri], "position": 0}
    response = requests.post(API_BASE_URL + f'playlists/{playlist_id}/tracks', headers=headers, json=data)

    if response.status_code != 201:
        return JSONResponse(content={"error": response.text}, status_code=500)

    return JSONResponse(content={"message": "Canciones añadidas a la playlist correctamente"})
