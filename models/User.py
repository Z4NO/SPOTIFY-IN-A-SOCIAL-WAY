import datetime
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore import FieldFilter
import datetime
import os

class User:
    def __init__(
            self, 
            id, 
            authenticated_at: datetime,
            spotify_expires_at: datetime,
            spotify_token,
            refresh_token,
            key
        ):
        self.id = id
        self.authenticated_at = authenticated_at
        self.spotify_expires_at = spotify_expires_at
        self.spotify_token = spotify_token
        self.key = key
        self.refresh_token = refresh_token

