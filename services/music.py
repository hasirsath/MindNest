# services/music_client.py
from .local_recs import LOCAL_MUSIC_RECS # Import our local database

# ✨ NEW: An alias map to group specific emotions into our main categories
EMOTION_ALIAS_MAP = {
    # Sadness Aliases
    "disappointment": "sadness",
    "grief": "sadness",
    "remorse": "sadness",
    
    # Joy Aliases
    "excitement": "joy",
    "gratitude": "joy",
    "love": "joy",
    "optimism": "joy",
    "admiration": "joy",
    "approval": "joy",
    "caring": "joy",
    
    # Nervousness Aliases
    "fear": "nervousness",

    # Default/Neutral Aliases
    "neutral": "default",
    "curiosity": "default",
    "realization": "default"
}

def get_music_recommendations(emotion):
    """
    Gets music recommendations from our local database file.
    """
    emotion_lower = emotion.lower()
    
    # ✨ NEW: First, check if the specific emotion is an alias for a broader category.
    # For example, if the emotion is 'optimism', this will map it to 'joy'.
    # If the emotion is already 'joy', it will just return 'joy'.
    mapped_emotion = EMOTION_ALIAS_MAP.get(emotion_lower, emotion_lower)
    
    # Now, get the recommendations for the correctly mapped category.
    recs = LOCAL_MUSIC_RECS.get(mapped_emotion, LOCAL_MUSIC_RECS["default"])
    return recs