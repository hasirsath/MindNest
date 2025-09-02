from googleapiclient.discovery import build
import random
import os
from urllib.parse import urlparse, parse_qs

# Load API key
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")


def extract_youtube_id(url: str):
    """Extracts YouTube video ID from a full YouTube URL."""
    if not url:
        return None
    if "youtube.com/watch" in url:
        query = urlparse(url)
        return parse_qs(query.query).get("v", [None])[0]
    elif "youtu.be" in url:
        return url.split("/")[-1].split("?")[0]
    return url  # Assume it's already an ID


def extract_video_id(raw_id):
    """Handles both dicts and plain strings from YouTube API responses."""
    if isinstance(raw_id, dict):
        return raw_id.get("videoId")
    return raw_id


def get_trending_videos(region="US", max_results=10):
    """Fetch trending videos from YouTube by region."""
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    request = youtube.videos().list(
        part="snippet",
        chart="mostPopular",
        maxResults=max_results,
        regionCode=region
    )
    response = request.execute()

    videos = []
    for item in response.get("items", []):
        video_id = extract_video_id(item.get("id"))
        if not video_id:
            continue
        videos.append({
            "id": video_id,
            "title": item["snippet"]["title"],
            "thumbnail": item["snippet"]["thumbnails"]["medium"]["url"],
            "url": f"https://www.youtube.com/watch?v={video_id}"
        })
    return videos


def get_emotion_videos(emotion):
    """Fetch videos based on detected emotion."""
    emotion_map = {
        "happy": ["upbeat music", "funny videos", "motivational speech"],
        "sad": ["relaxing music", "inspirational talk", "uplifting songs"],
        "angry": ["calming meditation", "peaceful nature sounds"],
        "anxious": ["guided meditation", "soothing music", "yoga"],
        "neutral": ["trending news", "popular playlists"]
    }
    query = random.choice(emotion_map.get(emotion, ["popular music"]))

    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    request = youtube.search().list(
        part="snippet",
        q=query,
        type="video",
        maxResults=5
    )
    response = request.execute()

    videos = []
    for item in response.get("items", []):
        video_id = extract_video_id(item.get("id"))
        if not video_id:
            continue
        videos.append({
            "id": video_id,
            "title": item["snippet"]["title"],
            "thumbnail": item["snippet"]["thumbnails"]["medium"]["url"],
            "url": f"https://www.youtube.com/watch?v={video_id}"
        })
    return videos


def get_media_recommendations(emotion: str, region: str = "IN"):
    """Combine trending and emotion-based videos."""
    trending = get_trending_videos(region=region, max_results=2)
    emotion_based = get_emotion_videos(emotion)

    combined = [
        {
            "id": extract_youtube_id(video.get("id")),
            "title": video.get("title", ""),
            "thumbnail": video.get("thumbnail"),
            "url": video.get("url")
        }
        for video in (trending + emotion_based)
        if video.get("id")
    ]

    random.shuffle(combined)
    return combined
