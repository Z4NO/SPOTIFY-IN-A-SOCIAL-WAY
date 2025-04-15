from flask import Flask, redirect, request, jsonify,  render_template, url_for, Blueprint
from flask import session
import requests
import secrets
import urllib.parse
import datetime
from BaseManager import BaseManager
from Encripter import Encripter
from dotenv import load_dotenv
from User import User
import os
from typing import Final


# Datos de la app de Spotify
CLIENT_ID = os.getenv('CLIENT_ID')
REDIRECT_URI = 'http://localhost:5000/callback'


# URLs de Spotify
AUTH_URL = 'https://accounts.spotify.com/authorize'  # URL de autorización
TOKEN_URL = 'https://accounts.spotify.com/api/token'  # URL de obtención de token
API_BASE_URL = 'https://api.spotify.com/v1/'  # URL base de la API de Spotify

playlists = Blueprint('playlists_operations', __name__, url_prefix='/playlists_operations')  


# Obtener las playlist de un usuario en concreto
@playlists.route('/playlists/<user_id>')
def get_playlists_by_user(user_id):
    base_manager = BaseManager()
    token = base_manager._obtain_user_token(user_id)

    if base_manager._check_token_expired(user_id):
        refresh_token_obteined = base_manager._obtain_user_refresh_token(user_id)
        orginial_params = request.view_args.copy()
        return redirect(url_for('refresh_token', rute_back='playlists_operations.playlists', refresh_token=refresh_token_obteined, id=user_id, original_params=orginial_params))

    headers = {
        'Authorization': f'Bearer {token}'
    }

    response = requests.get(API_BASE_URL + 'me/playlists', headers=headers)
    if response.status_code != 200:
        return f"Error al obtener las playlists {response.text}" , 500
    playlists = response.json()

    return jsonify(playlists)


#Comprobar si un usuario tiene una playlist colaborativa

"""
Endpoint to check if a user has collaborative playlists.
Args:
    user_id (str): The ID of the user to check for collaborative playlists.
    playlist_id (str): The ID of the playlist (not used in the current implementation).
Returns:
    Response: 
        - If the user's token is expired, redirects to the token refresh endpoint with the necessary parameters.
        - If the user does not have collaborative playlists, returns a 500 status code with an error message.
        - If the user has collaborative playlists, returns a 200 status code with a success message.
Raises:
    None
"""
@playlists.route('/check_collaborative_playlist/<user_id>')
def check_collaborative_playlist(user_id):
    base_manager = BaseManager()
    token = base_manager._obtain_user_token(user_id)

    if base_manager._check_token_expired(user_id):
        refresh_token_obteined = base_manager._obtain_user_refresh_token(user_id)
        orginial_params = request.view_args.copy()
        return redirect(url_for('refresh_token', rute_back='playlists_operations.check_collaborative_playlist', refresh_token=refresh_token_obteined, id=user_id, original_params=orginial_params))

    if(base_manager._user_has_coop_playlists(user_id) == False):
        return "El usuario no tiene playlists colaborativas", 500
    else:
        coops_data : list = base_manager._obtain_coop_playlists(user_id)
        return jsonify({
            "message": "El usuario tiene playlists colaborativas",
            "playlists": coops_data
        }), 200
    


"""
Creates a Spotify playlist for a user.
This endpoint allows a user to create a new playlist on their Spotify account. 
The playlist can be public, private, or collaborative based on the provided parameters.
Args:
    user_id (str): The ID of the user in the application.
    playlist_name (str): The name of the playlist to be created.
    playlist_description (str): A description for the playlist.
    is_public (str): A string representation of whether the playlist is public ('True' or 'False').
    is_collaborative (str): A string representation of whether the playlist is collaborative ('True' or 'False').
Returns:
    Response: A JSON response containing the created playlist details if successful.
    Tuple: An error message and HTTP status code if an error occurs during the process.
Raises:
    Redirect: Redirects to the token refresh endpoint if the user's token is expired.
Notes:
    - If the playlist is collaborative, it will automatically be set to private.
    - The user's Spotify ID is retrieved using the Spotify API before creating the playlist.
    - The created playlist is added to the user's collaborative playlists in the application's database.
"""
@playlists.route('/create_playlist/<user_id>/<playlist_name>/<playlist_description>/<is_public>/<is_collaborative>')
def create_playlist(user_id, playlist_name, playlist_description, is_public, is_collaborative):
    base_manager = BaseManager()
    token = base_manager._obtain_user_token(user_id)
    print(type(is_collaborative))
    if is_collaborative == 'True':
        is_collaborative = True
        is_public = False
    else:
        is_collaborative = False
        is_public = True


    if base_manager._check_token_expired(user_id):
        refresh_token_obteined = base_manager._obtain_user_refresh_token(user_id)
        orginial_params = request.view_args.copy()
        return redirect(url_for('refresh_token', rute_back='playlists_operations.playlists', refresh_token=refresh_token_obteined, id=user_id, original_params=orginial_params))
    
    # Debemos obtener el ID  de spotify del usuario para crear la playlist
    headers = {
        'Authorization': f'Bearer {token}'
    }

    response = requests.get(API_BASE_URL + 'me', headers=headers)
    if response.status_code != 200:
        return f"Error al obtener el ID de usuario {response.text}" , 500
    user_info = response.json()
    spotify_user_id = user_info['id']
    # Crear la playlist
    headers = {
        'Authorization': f'Bearer {token}'
    }

    data = {
        'name': playlist_name,
        'description': playlist_description,
        'public': is_public,
        'collaborative': is_collaborative
    }

    response = requests.post(API_BASE_URL + 'users/' + spotify_user_id + '/playlists', headers=headers, json=data)
    if response.status_code != 201:
        return f"Error al crear la playlist {response.text}" , 500
    playlist = response.json()


    # Añadir la playlist colaborativa a la base de datos del usuario
    base_manager._add_coop_playlists(user_id, [playlist['id']])
    

    return jsonify(playlist)

#Añadir canciones a una playlist
"""
Adds a song to a specified playlist for a given user.
This endpoint allows adding a track to a Spotify playlist by providing the user ID, playlist ID, 
and track URI. It handles token validation and refresh if necessary.
Args:
    user_id (str): The ID of the user whose playlist will be modified.
    playlist_id (str): The ID of the playlist to which the song will be added.
    track_uri (str): The Spotify URI of the track to be added.
Returns:
    Response: A JSON response indicating success or failure.
        - On success: A JSON object with a success message and HTTP status code 200.
        - On failure: An error message and HTTP status code 500.
Raises:
    Redirect: If the user's token is expired, redirects to the token refresh endpoint with 
              the necessary parameters to retry the operation after refreshing the token.
"""
@playlists.route('/add_song_to_playlist/<user_id>/<playlist_id>/<track_uri>')
def add_songs_to_playlist(user_id, playlist_id, track_uri):
    base_manager = BaseManager()
    token = base_manager._obtain_user_token(user_id)

    if base_manager._check_token_expired(user_id):
        refresh_token_obteined = base_manager._obtain_user_refresh_token(user_id)
        orginial_params = request.view_args.copy()
        return redirect(url_for('refresh_token', rute_back='playlists_operations.add_songs_to_playlist', refresh_token=refresh_token_obteined, id=user_id, original_params=orginial_params))

    headers = {
        'Authorization': f'Bearer {token}'
    }


    # Añadir las canciones a la playlist
    data = {
        'uris': [track_uri],
        'position': 0
    }

    response = requests.post(API_BASE_URL + f'playlists/{playlist_id}/tracks', headers=headers, json=data)
    if response.status_code != 201:
        return f"Error al añadir canciones a la playlist {response.text}" , 500

    return jsonify({"message": "Canciones añadidas a la playlist correctamente"}), 200
