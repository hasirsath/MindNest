# services/media_client.py
import os
from googleapiclient.discovery import build

# --- Initialization ---
api_key = os.getenv("YOUTUBE_API_KEY")

# Initialize the variable to None before the try block for robustness
youtube = None
try:
    if api_key:
        youtube = build('youtube', 'v3', developerKey=api_key)
        print("YouTube client initialized successfully.")
    else:
        print("WARNING: YOUTUBE_API_KEY not found. Video recommendations will be disabled.")
except Exception as e:
    print(f"Could not initialize YouTube client: {e}")

# --- Recommendation Logic ---
# This map holds specific search queries for different genres for each mood.
MEDIA_RECOMMENDATION_MAP = {
    "sadness": {
        "therapy": "guided meditation for sadness and grief",
        "comedy": "funny animal videos compilation",
        "creative": "easy watercolor painting for beginners",
        "travel": "relaxing drone footage of mountains"
    },
    "joy": {
        "music": "happy upbeat music playlist",
        "comedy": "clean comedy stand up",
        "learning": "fascinating science facts you didn't learn in school",
        "fitness": "fun dance workout at home"
    },
    "nervousness": {
        "therapy": "calming breathing exercises for anxiety",
        "asmr": "calm rain sounds for sleeping",
        "creative": "simple zentangle art for beginners",
        "music": "ambient music for focus and calm"
    },
    "anger": {
        "therapy": "guided meditation for anger and frustration",
        "fitness": "high intensity workout to release energy",
        "music": "high energy rock music",
        "learning": "channeling anger into productivity ted talk"
    },
    "default": {
        "therapy": "5 minute mindfulness meditation",
        "travel": "4K walking tour of Tokyo at night",
        "music": "relaxing instrumental music",
        "learning": "learn a simple magic trick"
    }
}

# This alias map groups the 28 specific emotions from the NLP model into our main categories.
MEDIA_ALIAS_MAP = {
    "disappointment": "sadness", "grief": "sadness", "remorse": "sadness",
    "excitement": "joy", "gratitude": "joy", "love": "joy", "optimism": "joy",
    "fear": "nervousness", "neutral": "default", "curiosity": "default"
}

# --- Main Public Function ---
def get_media_recommendations(emotion):
    """
    Fetches one YouTube video for each genre category associated with the given emotion.
    """
    if not youtube:
        return []

    recommendations = []
    
    # Map the specific emotion (e.g., 'optimism') to a general category (e.g., 'joy')
    emotion_lower = emotion.lower()
    mapped_emotion = MEDIA_ALIAS_MAP.get(emotion_lower, emotion_lower)
    
    # Get the dictionary of categories for the mapped emotion (e.g., {"music": "...", "comedy": "..."})
    categories = MEDIA_RECOMMENDATION_MAP.get(mapped_emotion, MEDIA_RECOMMENDATION_MAP["default"])

    # Loop through each category and get the top video result for its query
    for category, query in categories.items():
        try:
            search_request = youtube.search().list(
                part='snippet',
                q=query,
                type='video',
                maxResults=1 # Get just the top result for this specific category
            )
            response = search_request.execute()
            
            if response.get('items'):
                item = response['items'][0]
                recommendations.append({
                    "title": item['snippet']['title'],
                    "id": item['id']['videoId']
                })
        except Exception as e:
            print(f"Error fetching YouTube category '{category}': {e}")
            continue # If one category fails, just skip it and try the next

    return recommendations