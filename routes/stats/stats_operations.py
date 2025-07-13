from collections import Counter
from fastapi import APIRouter, Query
from fastapi.responses import RedirectResponse, JSONResponse
import requests
import urllib.parse
from managers.BaseManager import BaseManager
from core.config import API_BASE_URL
import datetime



router = APIRouter(prefix="/stats", tags=["stast"])


@router.get('/tops_genders/{user_id}', description="Get top genders of a user")
async def get_top_genders(user_id: str):
    base_manager = BaseManager()
    
    if base_manager._check_token_expired(user_id):
        refresh_token_obteined = base_manager._obtain_user_refresh_token(user_id)
        original_params = {"user_id": user_id}
        params = {
            "rute_back": "stats/top_genders",
            "refresh_token": refresh_token_obteined,
            "id": user_id,
            "original_params": str(original_params)
        }
        return RedirectResponse(f"/refresh_token?{urllib.parse.urlencode(params)}")
    
    token = base_manager._obtain_user_token(user_id)

    request_params = {"time_range": "long_term", "limit": 50}
    
    headers = {"Authorization": f"Bearer {token}"}


    url = f"{API_BASE_URL}me/top/artists"

    response = requests.get(url, headers=headers, params=request_params)
    
    if response.status_code != 200:
        return JSONResponse({"error": "Failed to fetch top genders"}, status_code=response.status_code)
    
    information = response.json()

    genres_count = Counter()

    for item in information['items']:
        for genres in item['genres']:
            genres_count[genres] = genres_count.get(genres, 0) + 1

    top_genres = genres_count.most_common(10)

    return JSONResponse (content=top_genres)

    
            
    

    