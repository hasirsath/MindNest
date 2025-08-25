# services/music_client.py
from .local_recs import LOCAL_MUSIC_RECS # Import our local database

# ✨ NEW: An alias map to group specific emotions into our main categories
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