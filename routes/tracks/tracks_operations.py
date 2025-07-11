import secrets
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, JSONResponse
import requests
from managers.BaseManager import BaseManager
from models.User import User


router = APIRouter(prefix="/tracks", tags=["tracks"])

API_BASE_URL = 'https://api.spotify.com/v1/'
#Añadir a la cola mas canciones del mismo artista de la canción que se está escuchando
"""
Adds the top songs of the artists of the currently playing track to the user's playback queue.
This endpoint retrieves the currently playing track for a user, extracts the artists associated with the track, 
fetches their top songs, and adds a random top song from each artist to the user's playback queue. 
The user must have a premium Spotify account for this operation.
Args:
    user_id (str): The ID of the user for whom the operation is performed.
Returns:
    Response: 
        - If the user's token is expired, redirects to the token refresh endpoint.
        - If the user is not a premium user, returns a 501 error with a message.
        - If no track is currently playing, returns a 500 error with a message.
        - If successful, returns a JSON response with a success message and the URIs of the added tracks.
        - If an error occurs while fetching artist songs or adding tracks to the queue, returns a 500 error with a message.
Raises:
    Exception: If there is an error while fetching artist songs or adding tracks to the queue.
Notes:
    - The function checks if the user's token is expired and refreshes it if necessary.
    - The function only works for premium Spotify users.
    - The function uses the Spotify Web API to fetch user and track information.
"""
@router.get('/add_artist_songs_to_queue/{user_id}')
def add_artist_songs_to_queue(user_id):
    base_manager = BaseManager()
    token = base_manager._obtain_user_token(user_id)

    if base_manager._check_token_expired(user_id):
        refresh_token_obteined = base_manager._obtain_user_refresh_token(user_id)
        orginial_params = {"user_id": user_id}
        return RedirectResponse(
            url=f"/refresh_token?rute_back=tracks/add_artist_songs_to_queue&refresh_token={refresh_token_obteined}&id={user_id}&original_params={orginial_params}"
        )
    
    #Antes de comenzar a añadir canciones a la cola, debemos saber si el usuario es premiun o no
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = requests.get(API_BASE_URL + 'me', headers=headers)
    is_premiun = response.json()
    if is_premiun['product'] == 'free':
        return "El usuario no es premium, por lo que no puede añadir canciones a la cola", 501

    # Primero antes de nada debemos obtener la canción que está escuchando el usuario
    headers = {
        'Authorization': f'Bearer {token}'
    }

    # Obtenemos la canción que está escuchando el usuario y guaradamos los id de los artistas
    response = requests.get(API_BASE_URL + 'me/player', headers=headers)
    song = response.json()
    if song['is_playing'] == False:
        return JSONResponse(content={"error": "No hay canción en reproducción"})
    if 'item' in song:
        artists_list_id = [artist['id'] for artist in song['item']['artists']]
    else:
       return JSONResponse(content={"error": "No hay canción en reproducción"})
    
    # Obtenemos las canciones de los artistas
    tracks_uris = []

    headers = {
        'Authorization': f'Bearer {token}',
    }
    try:
        for artist_id in artists_list_id:
            response = requests.get(API_BASE_URL + f'artists/{artist_id}/top-tracks', headers=headers)
            tracks = response.json()
            #necesito saber cuantas canciones tiene el artista para elegir una al azar
            num_tracks = len(tracks['tracks'])
            if num_tracks > 1:
                track_index = secrets.randbelow(num_tracks)
                tracks_uris.append(tracks['tracks'][track_index]['uri'])
            else:
                #Añadimos solo el primer album de cada artista
                tracks_uris.append(tracks['tracks'][0]['uri'])
    except Exception as e:
        return JSONResponse(content={"error": f"Error al obtener las canciones de los artistas: {e}"}, status_code=500)
    
    # Solo nos queda añadir las canciones a la cola
    headers = {
        'Authorization': f'Bearer {token}',
    }

    
    try:
        for track_uri in tracks_uris:
            params = { 'uri': track_uri }
            response = requests.post(API_BASE_URL + 'me/player/queue', headers=headers, params=params)

        return JSONResponse(content={"message": "Canciones añadidas a la cola correctamente", "tracks_uris": tracks_uris})
    except Exception as e:
        return "Error al añadir las canciones a la cola", 500
    

# Añadir la canción que estas escuchando a una playlist
"""
Adds the currently playing song of a user to a specified playlist.
This function interacts with the Spotify API to retrieve the song that the user is currently listening to
and adds it to the specified playlist. If the user's token is expired, it redirects to a token refresh endpoint.
Args:
    user_id (str): The ID of the user whose currently playing song is to be added.
    playlist_id (str): The ID of the playlist to which the song will be added.
Returns:
    Response: A JSON response with the details of the added track if successful, or an error message otherwise.
Raises:
    Exception: If there is an error while adding the song to the playlist.
Notes:
    - The function checks if the user's token is expired and refreshes it if necessary.
    - If no track is currently playing, it returns an error message with a 500 status code.
    - The function uses the Spotify API endpoints `me/player` to get the currently playing track
      and `playlists/{playlist_id}/tracks` to add the track to the playlist.
"""
@router.get('/add_song_to_playlist/<user_id>/<playlist_id>/')
def add_song_to_playlist(user_id, playlist_id):
    base_manager = BaseManager()
    token = base_manager._obtain_user_token(user_id)

    if base_manager._check_token_expired(user_id):
        refresh_token_obteined = base_manager._obtain_user_refresh_token(user_id)
        orginial_params = {"user_id": user_id, "playlist_id": playlist_id}

        return RedirectResponse(
            url=f"/refresh_token?rute_back=tracks/add_song_to_playlist&refresh_token={refresh_token_obteined}&id={user_id}&original_params={orginial_params}"
        )
    
    # Primero antes de nada debemos obtener la canción que está escuchando el usuario
    headers = {
        'Authorization': f'Bearer {token}'
    }

    response = requests.get(API_BASE_URL + 'me/player', headers=headers)
    song = response.json()
    if 'item' in song:
        uri_actual_track = song['item']['uri']
        id_actual_track = song['item']['id']
        name_actual_track = song['item']['name']
    else:
        return "No track is currently playing:" + {song}, 500


    # Ahora con la uri obtenida de la canción que está escuchando el usuario, la añadimos a la playlist
    
    headers = {
        "Content-Type": "application/json",
        'Authorization': f'Bearer {token}'
    }

    req_body = {
        'uris': [uri_actual_track],
        'position': 0
    }

    try:
        response = requests.post(API_BASE_URL + f'playlists/{playlist_id}/tracks', headers=headers, json=req_body)
        if response.status_code != 201:
            return JSONResponse(content={"error": response.text}, status_code=500)
        

        return JSONResponse(content={
            "message": "Canción añadida a la playlist correctamente",
            "track_id": id_actual_track,
            "track_name": name_actual_track,
            "track_uri": uri_actual_track
        })
        
    except Exception as e:
        return "Error al añadir la canción a la playlist", 500
    
# Buscar una canción en la api de spotify según el nombre de la canción
"""
Search for a song on Spotify based on the song name, artist name, and user ID.
This function interacts with the Spotify API to search for a specific song. It first retrieves
the user's access token and checks if it has expired. If the token is expired, the user is redirected
to refresh their token. Once a valid token is obtained, the function sends a request to the Spotify
API to search for the song and returns the song's URI, name, and ID.
Args:
    song_name (str): The name of the song to search for.
    artist_name (str): The name of the artist of the song.
    user_id (str): The ID of the user making the request.
Returns:
    Response: A JSON response containing the song's URI, name, and ID if the search is successful.
              If the token is expired, redirects the user to refresh their token.
              If an error occurs during the search, returns an error message with a 500 status code.
Raises:
    Exception: If an unexpected error occurs during the search process.
Notes:
    - The function uses the `BaseManager` class to handle token retrieval and validation.
    - The Spotify API endpoint used is `search`, and the query parameters include the song name
      and artist name.
    - The function assumes the presence of a valid `API_BASE_URL` constant and the `requests` library.
"""
@router.get('/search_song/<song_name>/<artist_name>/<user_id>/')
def search_song(song_name, artist_name,user_id):
    base_manager = BaseManager()
    token = base_manager._obtain_user_token(user_id)

    if base_manager._check_token_expired(user_id):
        refresh_token_obteined = base_manager._obtain_user_refresh_token(user_id)
        orginial_params = {
            "user_id": user_id,
            "song_name": song_name,
            "artist_name": artist_name
        }
        
        return RedirectResponse(
            url=f"/refresh_token?rute_back=tracks/search_song&refresh_token={refresh_token_obteined}&id={user_id}&original_params={orginial_params}"
        )
    
    headers = {
        'Authorization': f'Bearer {token}'
    }

    params = {
        'q': f'track:{song_name} artist:{artist_name}',
        'type': 'track'
    }

    try:
        response = requests.get(API_BASE_URL + 'search', headers=headers, params=params)
        if response.status_code != 200:
           return JSONResponse(content={"error": response.text}, status_code=500)
        song = response.json()
        #devolvemos solo el uri de la cancion para poder añadirla a la cola y el nombre de la cancion y el id de la cancion
        return JSONResponse(content={
            "uri": song['tracks']['items'][0]['uri'],
            "name": song['tracks']['items'][0]['name'],
            "id": song['tracks']['items'][0]['id']
        })
    except Exception as e:
        return JSONResponse(content={"error": f"Error al buscar la canción: {e}"}, status_code=500)
    


