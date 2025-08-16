# services/media_client.py
from .local_recs import LOCAL_VIDEO_RECS # Import from our local database

def get_media_recommendations(emotion, media_type='video'):
    """
    Gets video recommendations from our local database file.
    """
    recs = LOCAL_VIDEO_RECS.get(emotion.lower(), LOCAL_VIDEO_RECS["default"])
    return recs