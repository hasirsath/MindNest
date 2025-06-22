from textblob import TextBlob # type: ignore
from transformers import pipeline

emotion_classifier = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base", top_k=1)


def analyze_text(text):
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity

    if polarity > 0.1:
        mood = "Positive"
    elif polarity < -0.1:
        mood = "Negative"
    else:
        mood = "Neutral"

    emotion_result = emotion_classifier(text)
    print("DEBUG >>>", type(emotion_result), emotion_result)
    emotion = emotion_result[0][0]['label']  # Extract the top predicted emotion


    return {
        'polarity': polarity,
        'mood': mood,
        'emotion': emotion,
        'suggestion': get_suggestion(mood)
    }

def get_suggestion(mood):
    suggestions = {
        "Positive": "Keep up the good vibes! Maybe share your joy with a friend.",
        "Negative": "Take a deep breath. Consider a short walk or journaling your thoughts.",
        "Neutral": "A quiet moment or a short meditation could help you reflect."
    }

    return suggestions.get(mood, "Take care of yourself!")

def get_suggestion(emotion):
    suggestions = {
        "joy": "Celebrate your wins! Keep doing what you love.",
        "sadness": "Take a break and do something comforting. Maybe journal more.",
        "anger": "Try a breathing exercise or a quick walk to release tension.",
        "fear": "You're not alone — talk to a friend or write your thoughts down.",
        "love": "Express it! Connect with someone or share kind words.",
        "surprise": "Channel the surprise into curiosity. What can you learn from this?",
        "neutral": "Reflect calmly. A clear mind is a powerful tool."
    }
    return suggestions.get(emotion.lower(), "Take care of your emotional well-being.")