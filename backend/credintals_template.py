from spotipy.oauth2 import SpotifyOAuth

class Credintals:
    OAuth = SpotifyOAuth(
                client_id="client_id",
                client_secret="client_secret",
                redirect_uri="http://127.0.0.1:8888/callback",
                scope="user-modify-playback-state user-read-playback-state",
                cache_path=".spotify_cache"
            )
    

    # Change name to credintals.py