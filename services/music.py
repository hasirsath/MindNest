# services/music_client.py
from .local_recs import LOCAL_MUSIC_RECS # Import from our local database

def get_music_recommendations(emotion):
    """
    Gets music recommendations from our local database file.
    """
    recs = LOCAL_MUSIC_RECS.get(emotion.lower(), LOCAL_MUSIC_RECS["default"])
    return recs