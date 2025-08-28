# services/media_client.py
from .local_recs import LOCAL_VIDEO_RECS # Import from our local database
import requests




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

# services/music_client.py
import requests
from services.emotion_map import EMOTION_ALIAS_MAP
from services.emotion_playlists import get_random_playlist_keyword

PROXY_URL = "https://prismatic-florentine-2b806d.netlify.app/.netlify/functions/getMusic"

def get_music_recommendations(emotion):
    """Fetch music recommendations for detected emotion."""
    try:
        # Normalize emotion
        canonical_emotion = EMOTION_ALIAS_MAP.get(emotion.lower(), "default")

        # Random keyword for variety
        keyword = get_random_playlist_keyword(canonical_emotion)

        # Always pass `query`
        response = requests.get(PROXY_URL, params={"query": keyword})
        response.raise_for_status()
        tracks = response.json()

        # Return usable results
        return [{"id": track['id'], "keyword": keyword} for track in tracks]

    except Exception as e:
        print(f"Error calling proxy function: {e}")
        return []



def get_media_recommendations(emotion):
    """Wrapper so app.py can call one function (future-proof if video is added)."""
    music = get_music_recommendations(emotion)
    return {
        "music": music,
        "videos": []  # placeholder, so no error if app expects videos
    }