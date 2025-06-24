import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore import FieldFilter
import datetime
from User import User
from Encripter import Encripter
import os

class BaseManager:
    def __init__(self):
        try:
            self.cred = credentials.Certificate(os.path.join(os.path.dirname(__file__), "better-discord-spotify-firebase-adminsdk-fbsvc-afe93f23d7.json"))
            if not firebase_admin._apps:
                firebase_admin.initialize_app(self.cred)
            self.db = firestore.client()
            self.encripter = Encripter(os.getenv('MASTER_KEY').encode())
        except Exception as e:
            print(f"Error al iniciar la base de datos: {e}")
            self.db = None

    def _add_user(self, user: User):
        doc_ref = self.db.collection("users")

        doc_ref.add({
            "Id": user.id,
            "authenticated_at": user.authenticated_at,
            "refresh_token": user.refresh_token,
            "spotify_token": user.spotify_token,
            "spotify_expires_at": user.spotify_expires_at,
            "spotify_expires_at": user.spotify_expires_at,
            "key": user.key
        })

    def _update_user_for_refresh(self, user: User):
        user_ref = self.db.collection("users").where("Id", "==", user.id).stream()
        for doc in user_ref:
            doc_ref = self.db.collection("users").document(doc.id)
            doc_ref.update(
                {
                    "Id": user.id,
                    "spotify_token": user.spotify_token,
                    "spotify_expires_at": user.spotify_expires_at,
                    "authenticated_at": user.authenticated_at,
                }
            )
            
    def _check_user_is_login(self, id) -> bool:
        print(f"Checking if user with ID {id} is logged in...")
        user_ref = self.db.collection("users")
        user_query = user_ref.where("Id", "==", id).stream()
        if len(list(user_query)) > 0:
            return True

    def _check_credentials_exists(self, id, key) -> bool:
        temp_data_ref= self.db.collection("tempDataLogin")
        temp_data_query = temp_data_ref.where("ID", "==", id).where("expires_at", ">", datetime.datetime.now(datetime.timezone.utc)).where("Key", "==", key).stream()

        if len(list(temp_data_query)) > 0:
            return True
        else:
            return False
        
    def _check_token_expired(self, id) -> bool:
        user_ref = self.db.collection("users")
        user_query = user_ref.where("Id", "==", id).stream()

        for user in user_query:
            expires_at = user.to_dict()['spotify_expires_at']
            if datetime.datetime.now(datetime.timezone.utc) > expires_at:
                return True
        return False
    
    def _obtain_user_token(self, id) -> str:
        user_ref = self.db.collection("users")
        user_query = user_ref.where("Id", "==", id).stream()
        user_list = list(user_query)
        
        if len(user_list) == 0:
            return "No users found"

        for user in user_list:
            return self.encripter._decript(user.to_dict()["spotify_token"])
        
    def _obtain_user_refresh_token(self, id) -> str:
        user_ref = self.db.collection("users")
        user_query = user_ref.where("Id", "==", id).stream()
        user_list = list(user_query)
        print("User query: ", user_query)

        if len(user_list) == 0:
            return "No users found"

        for user in user_list:
            refresh_token = user.to_dict()["refresh_token"]
            return self.encripter._decript(refresh_token)
        
    def _obtain_coop_playlists(self, id) -> list:
        user_ref = self.db.collection("users")
        user_query = user_ref.where("Id", "==", id).stream()
        user_list = list(user_query)

        if len(user_list) == 0:
            return "No users found"
        
        for user in user_list:
            playlists = user.to_dict()["coop_playlists"]
            return playlists
        
    def _user_has_coop_playlists(self, id) -> bool:
        user_ref = self.db.collection("users")
        user_query = user_ref.where("Id", "==", id).stream()
        user_list = list(user_query)

        if len(user_list) == 0:
            print(f"No users found with the given ID: {id}. Please check if the 'Id' field exists and matches the provided ID.")
            return False
        else:
            print(f"Found {len(user_list)} user(s) with the given ID: {id}.")

        for doc in user_list:
            playlists = doc.to_dict()["coop_playlists"]
            if len(playlists) > 0:
                return True
            else:
                return False
        
    def _add_coop_playlists(self, id, playlist_ids: list):
        user_ref = self.db.collection("users")
        user_query = user_ref.where("Id", "==", id).stream()
        user_list = list(user_query)

        if len(user_list) == 0:
            print(f"No users found with the given ID: {id}. Please check if the 'Id' field exists and matches the provided ID.")
            return
        else:
            print(f"Found {len(user_list)} user(s) with the given ID: {id}.")

        try:
            for doc in user_list:
                doc_ref = self.db.collection("users").document(doc.id)
                doc_ref.update(
                    {
                        "coop_playlists": firestore.ArrayUnion(playlist_ids)
                    }
                )
        except Exception as e:
            print(f"Error al añadir la playlist colaborativa: {e}")
            return
            


    def close(self):
        firebase_admin.delete_app(firebase_admin.get_app())

        

