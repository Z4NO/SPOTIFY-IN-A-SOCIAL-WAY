# app/core/auth.py

from ast import literal_eval
from fastapi import APIRouter, Request, Form, Query
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from templates import templates
from managers.BaseManager import BaseManager
from managers.Encripter import Encripter
from models.User import User
from core.config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, AUTH_URL, TOKEN_URL, API_BASE_URL, MASTER_KEY
import datetime, urllib.parse, requests

router = APIRouter()
encripter = Encripter(MASTER_KEY.encode())

@router.get("/", response_class=HTMLResponse)
async def index_get(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.post("/", response_class=HTMLResponse)
async def index_post(request: Request, ID: str = Form(...), Key: str = Form(...)):
    base_manager = BaseManager()
    if base_manager._check_user_is_login(ID):
        return RedirectResponse(url="/playlist", status_code=302)
    
    if base_manager._check_credentials_exists(ID, Key):
        request.session["ID_DS"] = ID
        request.session["Key_DS"] = Key
        return RedirectResponse(url=f"/login?Id={ID}&Key={Key}", status_code=302)
    else:
        return RedirectResponse(url="/incorrect", status_code=302)

@router.get("/incorrect", response_class=HTMLResponse)
async def incorrect(request: Request):
    return templates.TemplateResponse("nocredentials.html", {"request": request})

@router.get("/login")
async def login(Id: str, Key: str):
    if not Id or not Key:
        return RedirectResponse(url="/")

    scopes = "user-read-private user-read-email playlist-modify-public playlist-modify-private " \
             "user-read-playback-state user-modify-playback-state user-top-read " \
             "user-read-currently-playing user-follow-read user-follow-modify user-library-read user-library-modify user-read-recently-played"

    state = encripter._encript(f"{Id}:{Key}")

    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": scopes,
        "show_dialog": True,
        "state": state
    }

    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    return RedirectResponse(auth_url)

@router.get("/callback")
async def callback(request: Request, code: str = None, state: str = None, error: str = None):
    if error:
        return JSONResponse({"error": error})

    id, key = encripter._decript(state).split(":")
    if not id or not key:
        return RedirectResponse("/")

    req_body = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }

    response = requests.post(TOKEN_URL, data=req_body)
    token_info = response.json()

    request.session["acces_token"] = token_info["access_token"]
    request.session["refresh_token"] = token_info["refresh_token"]
    request.session["expires_in"] = datetime.datetime.now().timestamp() + token_info["expires_in"]

    user = User(
        id=id,
        authenticated_at=datetime.datetime.now(),
        spotify_expires_at=datetime.datetime.now() + datetime.timedelta(seconds=token_info["expires_in"]),
        spotify_token=encripter._encript(token_info["access_token"]),
        refresh_token=encripter._encript(token_info["refresh_token"]),  # Encriptar, no desencriptar
        key=key
    )
    BaseManager()._add_user(user)
    return RedirectResponse("/playlist")






@router.get("/refresh_token")
async def refresh_token(request: Request):
    rute_back = request.query_params.get("rute_back")
    refresh_token = request.query_params.get("refresh_token")
    id = request.query_params.get("id")
    original_params_raw = request.query_params.get("original_params")
    original_params = literal_eval(original_params_raw) if original_params_raw else {}

    if not refresh_token:
        return HTMLResponse("No refresh token provided", status_code=400)

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
        spotify_token=Encripter(MASTER_KEY)._encript(new_token_info['access_token']),
        refresh_token=refresh_token,
        key=None
    )

    try:
        BaseManager()._update_user_for_refresh(new_user)
    except Exception as e:
        print(f"Error al actualizar el usuario: {e}")
        return HTMLResponse("Error al actualizar el usuario", status_code=500)

    # reconstruimos la ruta final
    path = f"/{rute_back}/" + "/".join([original_params[k] for k in original_params])
    query_str = urllib.parse.urlencode({
        **original_params,
        "acces_token": new_token_info['access_token'],
        "refresh_token": refresh_token,
        "expires_in": int(datetime.datetime.now().timestamp() + new_token_info['expires_in'])
    })

    print(f"Nuevo token para el usuario {id}: {new_token_info['access_token']}")

    return RedirectResponse(f"{path}?{query_str}")