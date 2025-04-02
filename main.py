from flask import Flask, redirect, request, jsonify,  render_template, url_for
from flask import session
from tracks.tracks_operations import track as tracks_operations
from playlist.playlist_operatiosn import playlists as playlist_operations
from player.player_operations import player as player_operations
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

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Crear la app de Flask
app = Flask(__name__)
# Generar una clave secreta para la app
app.secret_key = secrets.token_hex(16)
#Registrar los blueprints
app.register_blueprint(tracks_operations)
app.register_blueprint(playlist_operations)
app.register_blueprint(player_operations)

# Datos de la app de Spotify
CLIENT_ID =  os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = 'http://localhost:5000/callback'
MASTER_KEY: Final[str] = os.getenv('MASTER_KEY')



# URLs de Spotify
AUTH_URL = 'https://accounts.spotify.com/authorize'  # URL de autorización
TOKEN_URL = 'https://accounts.spotify.com/api/token'  # URL de obtención de token
API_BASE_URL = 'https://api.spotify.com/v1/'  # URL base de la API de Spotify

encripter = Encripter(MASTER_KEY.encode())

# Rutas de la app
"""
Handles the index route for the web application.
This function processes both GET and POST requests to the root URL ('/'). 
For POST requests, it checks if the user is logged in using the provided ID. 
If the user is not logged in, it retrieves the ID and Key from the form data, 
validates the credentials, and sets the session variables if the credentials are valid. 
If the credentials are invalid, it redirects to the '/incorrect' page. 
For GET requests, it renders the 'index.html' template.
Returns:
    Response: A redirect to the 'login' route with the user's ID and Key if the credentials are valid.
    Response: A redirect to the '/incorrect' page if the credentials are invalid.
    Response: Renders the 'index.html' template for GET requests.
"""
@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST' and not BaseManager()._check_user_is_login(request.form.get('ID')):
        Id = request.form.get('ID')
        Key = request.form.get('Key')

        base_manager = BaseManager()
        if base_manager._check_credentials_exists(Id, Key):
            session['ID_DS'] = Id
            session['Key_DS'] = Key
            return redirect(url_for('login', Id=Id, Key=Key))
            
        else:
            return redirect('/incorrect')

    return render_template('index.html')

# Ruta de credenciales incorrectas
@app.route('/incorrect')
def incorrect():
    return render_template("nocredentials.html")

# Ruta de login
"""
Handles the login route for the application.
This function retrieves the 'Id' and 'Key' parameters from the request arguments.
If either parameter is missing, it redirects the user to the home page ('/').
Otherwise, it encrypts the 'Id' and 'Key' values and constructs an authorization URL
with the necessary parameters for the Spotify API, then redirects the user to this URL.
Returns:
    Response: A redirect response to the home page if 'Id' or 'Key' is missing,
              or a redirect response to the Spotify authorization URL.
"""
@app.route('/login')
def login():
    id = request.args.get('Id')
    key = request.args.get('Key')

    if not id or not key:
        return redirect('/')
    
    scopes = 'user-read-private user-read-email playlist-modify-public playlist-modify-private user-read-playback-state user-modify-playback-state user-read-playback-state user-top-read playlist-modify-public playlist-modify-private user-read-currently-playing user-follow-read user-follow-modify user-library-read user-library-modify'

    # Encriptar el valor del parámetro state
    state = encripter._encript(f'{id}:{key}')

    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': REDIRECT_URI,
        'scope': scopes,
        'show_dialog': True,
        'state': state
    }

    auth_url = f'{AUTH_URL}?{urllib.parse.urlencode(params)}'
    return redirect(auth_url)

# Ruta de callback es decir, la que se ejecuta después de que el usuario se loguea en Spotify
"""
Callback route for handling Spotify's authorization response.
This route is called by Spotify after the user authorizes the application. It handles the response from Spotify, 
extracts the authorization code, exchanges it for an access token, and stores the necessary information in the session 
and database.
Returns:
    JSON response with error message if there's an error in the request.
    Redirects to the home page if the state parameter is invalid.
    Redirects to the playlist page after successfully obtaining and storing the access token.
Raises:
    KeyError: If the response from Spotify does not contain the expected keys.
"""
@app.route('/callback')
def callback():
    # Si hay un error en la respuesta de Spotify, lo mostramos en formato JSON, si no, obtenemos el código de autorización
    if 'error' in request.args:
        return jsonify({'error': request.args['error']})

    #Verificar que el ID y la Key lleguen a la ruta
    # Recuperar id y key del parámetro state
    state = encripter._decript(request.args['state'])
    id, key = state.split(':')

    if not id or not key:
        return redirect('/')

    # Obtenemos el código de autorización y hacemos una petición POST a Spotify para obtener el token de acceso
    # El token de acceso es necesario para hacer peticiones a la API de Spotify
    if 'code' in request.args:
        req_body = {
            'grant_type': 'authorization_code',
            'code': request.args['code'],
            'redirect_uri': REDIRECT_URI,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

        response = requests.post(TOKEN_URL, data=req_body)
        token_info = response.json()

        # Este es el token que vamos a necesitar para hacer nuestras llamadas a la API de Spotify
        session['acces_token'] = token_info['access_token']
        token_encrypt = encripter._encript(session['acces_token'])
        # Este es el token que vamos a necesitar para refrescar el token de acceso, este token dura 1 día (el acces_token)
        session['refresh_token'] = token_info['refresh_token']
        refresh_token_encrypt = encripter._encript(session['refresh_token'])
        # Este es el tiempo que dura el token de acceso
        session['expires_in'] = datetime.datetime.now().timestamp() + token_info['expires_in']
        # Creamos un usuario para introducirlo en la base de datos
        user = User(
            id=id,
            authenticated_at=datetime.datetime.now(),
            spotify_expires_at=datetime.datetime.now() + datetime.timedelta(seconds=token_info['expires_in']),
            spotify_token=token_encrypt,
            refresh_token=refresh_token_encrypt,
            key=key
        )
        BaseManager()._add_user(user)

        return redirect('/playlist')

# Esta es la ruta que se ejecuta después de que el usuario se loguea en Spotify y mostrará las playlist del usuario
@app.route('/playlist')
def get_playlists():
    # Si no hay un token de acceso en la sesión, redirigimos al usuario a la ruta de login
    if 'acces_token' not in session:
        return redirect('/login')

    # Calculamos si el token de acceso ha expirado si es así redirigimos al usuario a la ruta de refrescar token
    if datetime.datetime.now().timestamp() > session['expires_in']:
        return redirect('/refresh_token')

    headers = {
        'Authorization': f'Bearer {session["acces_token"]}'
    }

    response = requests.get(API_BASE_URL + 'me/playlists', headers=headers)
    playlists = response.json()

    return jsonify(playlists)

# Añadir la canción que estas escuchando a una playlist
@app.route('/add_song_to_playlist/<user_id>/<playlist_id>/')
def add_song_to_playlist(user_id, playlist_id):
    base_manager = BaseManager()
    token = base_manager._obtain_user_token(user_id)

    if base_manager._check_token_expired(user_id):
        refresh_token_obteined = base_manager._obtain_user_refresh_token(user_id)
        return redirect(url_for('refresh_token', rute_back=f'/add_song_to_playlist/{user_id}/{playlist_id}', refresh_token=refresh_token_obteined, id=user_id))
    
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
            return f"Error al añadir la canción a la playlist: {response.text}", 500
        
        return jsonify({
            "message": "Canción añadida a la playlist correctamente",
            "track_id": id_actual_track,
            "track_name": name_actual_track,
            "track_uri": uri_actual_track
        }), 200
    except Exception as e:
        return "Error al añadir la canción a la playlist", 500
    


# Ruta para refrescar el token de acceso
"""
Endpoint to refresh the Spotify access token.
This endpoint is used to refresh the Spotify access token using the provided refresh token.
It updates the user's token information in the database and redirects to the specified route.
Args:
    rute_back (str): The route to redirect back to after refreshing the token.
    refresh_token (str): The refresh token to use for obtaining a new access token.
    id (str): The user ID.
    original_params (str): The original parameters to pass back to the redirect route.
Returns:
    Response: A redirect response to the specified route with the new access token and other parameters.
    If no refresh token is provided, returns a 400 error.
    If there is an error updating the user, returns a 500 error.
"""
@app.route('/refresh_token')
def refresh_token():
    rute_back = request.args.get('rute_back')
    refresh_token = request.args.get('refresh_token')
    id = request.args.get('id')
    original_params = request.args.get('original_params')
    original_params = eval(original_params) if original_params else {}
    

    if not refresh_token:
        return "No refresh token provided", 400
        

    
    req_body = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }

    response = requests.post(TOKEN_URL, data=req_body)
    new_token_info = response.json()


    new_user = User(
        id=id,
        authenticated_at=datetime.datetime.now(),
        spotify_expires_at=datetime.datetime.now() + datetime.timedelta(seconds=new_token_info['expires_in']),
        spotify_token=encripter._encript(new_token_info['access_token']),
        #El refresh token antorior se puede utlizar cada vez que se refresca el token asi que no es necesario actualizarlo
        refresh_token=refresh_token,
        key=None
    )

    try:
        BaseManager()._update_user_for_refresh(new_user)
    except Exception as e:
        print(f"Error al actualizar el usuario: {e}")
        return "Error al actualizar el usuario", 500
    
    
    return redirect(url_for(rute_back, **original_params, acces_token = new_token_info['access_token'], refresh_token = refresh_token, expires_in = datetime.datetime.now().timestamp() + new_token_info['expires_in']))

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)