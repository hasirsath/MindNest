# services/music.py
import requests

# Netlify proxy endpoint
PROXY_URL = "https://your-app.netlify.app/.netlify/functions/getMusic"

# Emotion → playlist keyword
EMOTION_KEYWORDS = {
    "joy": ["happy upbeat songs", "summer vibes playlist", "dance hits"],
    "sadness": ["sad acoustic songs", "heartbreak indie", "mellow chill"],
    "anger": ["rock workout songs", "metal rage playlist"],
    "fear": ["calm piano", "soothing acoustic", "relaxing ambient"],
    "neutral": ["focus study music", "chill lofi beats", "background vibes"]
}

def get_music_recommendations(emotion: str):
    """Get Spotify playlist recs via Netlify proxy."""
    keywords = EMOTION_KEYWORDS.get(emotion.lower(), ["chill vibes"])
    query = keywords[0]  # pick first keyword for now

    try:
        resp = requests.get(PROXY_URL, params={"query": query})
        resp.raise_for_status()
        data = resp.json()
        print(f"[Music API] Retrieved {len(data)} tracks for emotion '{emotion}' with query '{query}'")
        return data if isinstance(data, list) else []
    except Exception as e:
        print(f"[Music API Error] {e}")
        return []
