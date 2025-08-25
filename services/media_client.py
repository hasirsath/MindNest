# services/media_client.py
from .local_recs import LOCAL_VIDEO_RECS # Import from our local database


# In services/music_client.py

EMOTION_ALIAS_MAP = {
    # Sadness Aliases
    "disappointment": "sadness",
    "grief": "sadness",
    "remorse": "sadness",
    "embarrassment": "sadness",
    
    # Joy Aliases
    "excitement": "joy",
    "gratitude": "joy",
    "love": "joy",
    "optimism": "joy",
    "admiration": "joy",
    "approval": "joy",
    "caring": "joy",
    "pride": "joy",
    "relief": "joy",
    "amusement": "joy",
    "surprise": "joy",
    
    # Nervousness Aliases
    "fear": "nervousness",
    "annoyance": "nervousness",
    
    # Anger Aliases
    "disgust": "anger",
    "disapproval": "anger",
    
    # Desire Alias (already has its own category, but good to keep consistent)
    "desire": "desire",

    # Default/Neutral Aliases
    "neutral": "default",
    "curiosity": "default",
    "realization": "default",
    "confusion": "default"
}

def get_media_recommendations(emotion):
    """
    Gets video recommendations from our local database file.
    """
    recs = LOCAL_VIDEO_RECS.get(emotion.lower(), LOCAL_VIDEO_RECS["default"])
    return recs