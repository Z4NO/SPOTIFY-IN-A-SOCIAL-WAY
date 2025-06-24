from flask import Flask, redirect, request, jsonify,  render_template, url_for, Blueprint
from flask import session
from cache_app import cache
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

player = Blueprint('player_operations', __name__, url_prefix='/player_operations')


# Obtener tu 10 mejores canciones o artistas
"""
Endpoint to get the top items (artists or tracks) for a user.
Args:
    user_id (str): The ID of the user.
    type (str): The type of top items to retrieve ('artists' or 'tracks').
Returns:
    Response: A JSON response containing the top items (artists or tracks) for the user.
Raises:
    Redirect: If the user's token is expired, redirects to the token refresh endpoint.
    HTTPException: If there is an error in the request to the Spotify API.
"""
@player.route('/top/<user_id>/<type>')
@cache.cached(timeout=50)
def get_top_items(user_id, type):
    base_manager = BaseManager()
    token = base_manager._obtain_user_token(user_id)

    if base_manager._check_token_expired(user_id):
        refresh_token_obteined = base_manager._obtain_user_refresh_token(user_id)
        orginial_params = request.view_args.copy()
        return redirect(url_for('refresh_token', rute_back='player_operations.get_top_items', refresh_token=refresh_token_obteined, id=user_id, original_params=orginial_params))

    headers = {
        'Authorization': f'Bearer {token}'
    }

    params = {
        'type': type,
        'time_range': 'long_term',
        'limit': 10
    }

    response = requests.get(API_BASE_URL + f'me/top/{type}', headers=headers, params=params)
    if response.status_code != 200:
        return f"Error al obtener las canciones/artista {response.text}" , 500
    top_items = response.json()
    if type == 'artists' or type == 'tracks':
        artists_names = [artist['name'] for artist in top_items['items']]
        return jsonify(artists_names)

    return jsonify(top_items)

#Añadir a una playlist la cancion que esta escuchando otro usuario
"""
Adds the currently playing song of a target user to a specified playlist.
Args:
    user_id (str): The ID of the user making the request.
    target_id (str): The ID of the target user whose currently playing song is to be added.
    playlist_id (str): The ID of the playlist to which the song will be added.
Returns:
    Response: A Flask response object with a success message and song details if the song is added successfully.
              If the target user is not logged in, returns a 500 error with a message.
              If no song is currently playing, returns a 500 error with a message.
              If there is an error adding the song to the playlist, returns a 500 error with a message.
"""
@player.route('/add_target_song_to_playlist/<user_id>/<target_id>/<playlist_id>')
def add_song_to_playlist(user_id, target_id, playlist_id):
    base_manager = BaseManager()
    token = base_manager._obtain_user_token(user_id)

    if base_manager._check_token_expired(user_id):
        refresh_token_obteined = base_manager._obtain_user_refresh_token(user_id)
        orginial_params = request.view_args.copy()
        return redirect(url_for('refresh_token', rute_back='player_operations.add_target_song_to_playlist', refresh_token=refresh_token_obteined, id=user_id, original_params=orginial_params))
    
    #Necesitamos saber el token del otro usuario y se eesta logeuado en la app
    if base_manager._check_user_is_login(target_id) == False:
        return "El usuario target no está logueado en la aplicación", 500
    
    target_token = base_manager._obtain_user_token(target_id)

    

    # debemos obtener la canción que está escuchando el usuario

    headers = {
        'Authorization': f'Bearer {target_token}'
    }

    # Obtenemos la canción que está escuchando el usuario y guaradamos los id de los artistas
    response = requests.get(API_BASE_URL + 'me/player', headers=headers)
    if response.status_code != 200:
        return f"Error al obtener las canciones/artista o no esta escuchando ninguna canción el usuario target" , 500
    song = response.json()
    if 'item' in song:
        track_uri = song['item']['uri']
        track_id = song['item']['id']
        track_name = song['item']['name']

        #artists_list_id = [artist['id'] for artist in song['item']['artists']]
        #return jsonify(artists_list_id), 200
    else:
        return "No track is currently playing:" + {song}, 500
    
    # solo nos queda añadir la canción a la playlist
    # Ahora con la uri obtenida de la canción que está escuchando el usuario, la añadimos a la playlist
    
    headers = {
        "Content-Type": "application/json",
        'Authorization': f'Bearer {token}'
    }

    req_body = {
        'uris': [track_uri],
        'position': 0
    }

    try:
        response = requests.post(API_BASE_URL + f'playlists/{playlist_id}/tracks', headers=headers, json=req_body)
        if response.status_code != 201:
            return f"Error al añadir la canción a la playlist: {response.text}", 500
        
        return jsonify({
            "message": "Canción añadida a la playlist correctamente",
            "track_id": track_id ,
            "track_name": track_name,
            "track_uri": track_uri
        }), 200
    except Exception as e:
        return "Error al añadir la canción a la playlist", 500
    


#Añadir a una playlist la cancion que esta escuchando otro usuario
"""
Adds the currently playing song of a target user to the queue of another user.
Args:
    user_id (str): The ID of the user who wants to add the song to their queue.
    target_id (str): The ID of the target user whose currently playing song will be added to the queue.
Returns:
    Response: A Flask response object indicating the result of the operation.
Raises:
    500: If the target user is not logged in, if there is an error obtaining the song/artist, or if no track is currently playing.
    501: If the user is not a premium user and cannot add songs to the queue.
"""
@player.route('/add_target_song_to_queue/<user_id>/<target_id>/')
def add_target_song_to_queue(user_id, target_id):
    base_manager = BaseManager()
    token = base_manager._obtain_user_token(user_id)

    if base_manager._check_token_expired(user_id):
        refresh_token_obteined = base_manager._obtain_user_refresh_token(user_id)
        orginial_params = request.view_args.copy()
        return redirect(url_for('refresh_token', rute_back='player_operations.add_target_song_to_queue', refresh_token=refresh_token_obteined, id=user_id, original_params=orginial_params))
    
    #Necesitamos saber el token del otro usuario y se eesta logeuado en la app y si su token no ha caducado en ese lugar debemos refrescarlo
    if base_manager._check_user_is_login(target_id) == False:
        return "El usuario target no está logueado en la aplicación", 500
    
    target_token = base_manager._obtain_user_token(target_id)

    if base_manager._check_token_expired(target_id):
        refresh_token_obteined = base_manager._obtain_user_refresh_token(target_id)
        orginial_params = request.view_args.copy()
        return redirect(url_for('refresh_token', rute_back='player_operations.add_target_song_to_queue', refresh_token=refresh_token_obteined, id=target_id, original_params=orginial_params))

    #Necesitamos saber si el usuario es premium
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = requests.get(API_BASE_URL + 'me', headers=headers)
    is_premiun = response.json()
    if is_premiun['product'] == 'free':
        print(is_premiun['product'])
        return "El usuario no es premium, por lo que no puede añadir canciones a la cola", 501
    

    # debemos obtener la canción que está escuchando el usuario

    headers = {
        'Authorization': f'Bearer {target_token}'
    }

    # Obtenemos la canción que está escuchando el usuario y guaradamos los id de los artistas
    response = requests.get(API_BASE_URL + 'me/player', headers=headers)
    if response.status_code != 200:
        return f"Error al obtener las canciones/artista o no esta escuchando ninguna canción el usuario target" , 500
    song = response.json()
    if 'item' in song:
        track_uri = song['item']['uri']
        track_id = song['item']['id']
        track_name = song['item']['name']

        #artists_list_id = [artist['id'] for artist in song['item']['artists']]
        #return jsonify(artists_list_id), 200
    else:
        return "No track is currently playing:" + {song}, 500
    
    # solo nos queda añadir la canción a la cola
    # Ahora con la uri obtenida de la canción que está escuchando el usuario, la añadimos a la cola
    
    headers = {
        'Authorization': f'Bearer {token}',
    }

    
    try:
        params = { 'uri': track_uri }
        response = requests.post(API_BASE_URL + 'me/player/queue', headers=headers, params=params)

        return jsonify({
            "message": "Canciones añadidas a la cola correctamente",
            "tracks_uri": track_uri,
            "track_name": track_name,
            "track_id": track_id
        }), 200
    except Exception as e:
        return "Error al añadir las canciones a la cola", 500
    

    
