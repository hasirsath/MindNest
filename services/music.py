# services/music_client.py
import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# --- Initialize the Spotify Client ---
# ✨ FIX: Using a more robust initialization method for the client.
try:
    auth_manager = SpotifyClientCredentials(
        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")
    )
    sp = spotipy.Spotify(auth_manager=auth_manager)
    print("Spotify client initialized successfully.")
except Exception as e:
    sp = None
    print(f"Could not initialize Spotify client: {e}")


# --- Music Recommendation Logic (No changes below this line) ---
MUSIC_RECOMMENDATION_MAP = {
    "sadness": {
        "seed_genres": ["ambient", "chill", "classical", "instrumental"],
        "target_valence": 0.4, # Valence is musical positiveness (0.0-1.0)
        "target_energy": 0.3,  # Energy is intensity and activity (0.0-1.0)
        "limit": 3 # Number of tracks to recommend
    },
    "nervousness": {
        "seed_genres": ["ambient", "lo-fi", "minimal-techno", "chill"],
        "target_valence": 0.5,
        "target_energy": 0.2,
        "limit": 3
    },
    "anger": {
        "seed_genres": ["metal", "rock", "industrial"], # For catharsis
        "target_valence": 0.3,
        "target_energy": 0.9,
        "limit": 3
    },
    "joy": {
        "seed_genres": ["pop", "happy", "dance", "summer"], # For amplification
        "target_valence": 0.8,
        "target_energy": 0.8,
        "limit": 3
    },
    "excitement": {
        "seed_genres": ["dance", "electronic", "funk", "pop"],
        "target_valence": 0.9,
        "target_energy": 0.9,
        "limit": 3
    },
    "default": {
        "seed_genres": ["chill", "instrumental", "lo-fi"],
        "target_valence": 0.6,
        "target_energy": 0.4,
        "limit": 3
    }
}
MUSIC_RECOMMENDATION_MAP["disappointment"] = MUSIC_RECOMMENDATION_MAP["sadness"]
MUSIC_RECOMMENDATION_MAP["fear"] = MUSIC_RECOMMENDATION_MAP["nervousness"]
MUSIC_RECOMMENDATION_MAP["gratitude"] = MUSIC_RECOMMENDATION_MAP["joy"]
MUSIC_RECOMMENDATION_MAP["love"] = MUSIC_RECOMMENDATION_MAP["joy"]
MUSIC_RECOMMENDATION_MAP["neutral"] = MUSIC_RECOMMENDATION_MAP["default"]

def get_music_recommendations(emotion):
    """
    Gets music recommendations from Spotify based on a detected emotion.
    """
    if not sp:
        return []

    print("Attempting to get recommendations from Spotify...")
    params = MUSIC_RECOMMENDATION_MAP.get(emotion.lower(), MUSIC_RECOMMENDATION_MAP["default"])

    try:
        results = sp.recommendations(**params)
        recommendations = []
        for track in results.get('tracks', []):
            recommendations.append({
                "name": track['name'],
                "artist": track['artists'][0]['name'],
                "url": track['external_urls']['spotify'],
                "id": track['id']
            })
        return recommendations
    except Exception as e:
        print(f"Error fetching Spotify recommendations: {e}")
        return []