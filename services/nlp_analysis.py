# nlp_analysis.py

import random
from transformers import pipeline

# ---------------------- 1. Initialize Models ----------------------
print("Initializing NLP models... This may take a moment on first startup.")

sentiment_analyzer = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
emotion_classifier = pipeline("text-classification", model="SamLowe/roberta-base-go_emotions", top_k=None)
# We now call this 'topic_extractor' to better reflect its new job.
topic_extractor = pipeline("text2text-generation", model="google/flan-t5-base")

print("NLP models initialized successfully.")


# ---------------------- 2.Logic Core ----------------------

SUGGESTION_MAP = {
    "sadness": {
        "empathetic_text": [
            "It sounds like you're going through a really tough time. It's completely okay to feel this way, and thank you for sharing it.",
            "Reading this, it's clear you're carrying a heavy weight right now. Thank you for trusting this space with your feelings.",
            "It takes courage to write about feelings like this. Please know that it's valid to feel exactly as you do."
        ],
        "actionable_suggestion": [
            "Try a self-compassion exercise, like writing down one kind thing about yourself or placing a hand on your heart and taking three deep breaths.",
            "Engage with something comforting, like wrapping yourself in a warm blanket or listening to a favorite album.",
            "Consider reaching out to a friend or family member you trust, even just to say hello."
        ]
    },
    "nervousness": {
        "empathetic_text": [
            "It sounds like there's a lot on your mind right now. That feeling of anxiety is tough, but let's try to find a moment of calm.",
            "These feelings of worry are completely understandable. Let's work through them together.",
            "It's clear you're dealing with a lot of pressure. Let's try a small exercise to ground ourselves."
        ],
        "actionable_suggestion": [
            "Try the 5-4-3-2-1 grounding method: name 5 things you can see, 4 you can touch, 3 you can hear, 2 you can smell, and 1 you can taste.",
            "Try 'Box Breathing' for one minute: Inhale for 4 seconds, hold for 4, exhale for 4, and hold for 4. This can help regulate your nervous system.",
            "Write down all your worries on a piece of paper. Getting them out of your head can make them feel more manageable."
        ]
    },
    "joy": {
        "empathetic_text": [
            "This is wonderful to read! It's so important to acknowledge and celebrate these moments of happiness.",
            "Thank you for sharing this bright spot! Let's hold onto this wonderful feeling.",
            "Reading this brought a smile to my face. It's fantastic that you had this positive experience."
        ],
        "actionable_suggestion": [
            "Take a minute to really savor this feeling. What does it feel like in your body? Try to remember it for later.",
            "Share this good news with someone! Spreading joy often amplifies it for everyone.",
            "Capture this moment. Write down a few more details about why it feels so good, or take a picture related to the happy event."
        ]
    },
    "default": {
        "empathetic_text": ["Thank you for sharing your thoughts today. Taking the time to journal is a wonderful act of self-care."],
        "actionable_suggestion": ["As you reflect, consider one small thing you're looking forward to this week."]
    }
}

# Aliases
SUGGESTION_MAP["disappointment"] = SUGGESTION_MAP["sadness"]
SUGGESTION_MAP["anger"] = SUGGESTION_MAP["nervousness"]
SUGGESTION_MAP["fear"] = SUGGESTION_MAP["nervousness"]
SUGGESTION_MAP["excitement"] = SUGGESTION_MAP["joy"]
SUGGESTION_MAP["gratitude"] = SUGGESTION_MAP["joy"]
SUGGESTION_MAP["love"] = SUGGESTION_MAP["joy"]
SUGGESTION_MAP["neutral"] = SUGGESTION_MAP["default"]

# ---------------------- 3.Robust Functions ----------------------

def extract_topic(journal_text):
    """
    Uses a generative model to extract the main topic in a few words.
    This is more reliable than asking for a full sentence.
    """
    
    prompt = f"""
    Read the following journal entry and summarize the main topic or event in 2-5 words.

    ENTRY: "{journal_text}"

    TOPIC:
    """
    try:
        outputs = topic_extractor(prompt, max_new_tokens=10, num_beams=5, early_stopping=True)
        return outputs[0]['generated_text'].strip()
    except Exception as e:
        print(f"Topic extraction failed: {e}")
        return ""

def get_empathetic_suggestion(emotion, personalized_snippet):
    """
    Selects the appropriate suggestion and combines it with the personalized snippet.
    """
    suggestion_data = SUGGESTION_MAP.get(emotion, SUGGESTION_MAP["default"])
    
    
    chosen_intro = random.choice(suggestion_data['empathetic_text'])
    chosen_action = random.choice(suggestion_data['actionable_suggestion'])
    
    full_suggestion = f"{chosen_intro} {personalized_snippet} {chosen_action}"
    
    return full_suggestion

def analyze_text(text):
    """
    Function to analyze text using the final hybrid approach.
    """
    if not text or not text.strip():
        # Logic for empty input remains the same
        default_suggestion_data = SUGGESTION_MAP["default"]
        chosen_intro = random.choice(default_suggestion_data['empathetic_text'])
        chosen_action = random.choice(default_suggestion_data['actionable_suggestion'])
        return {
            "text": text, "mood": "Neutral", "sentiment": "NEUTRAL",
            "suggestion": f"{chosen_intro} {chosen_action}"
        }

    # Step 1: Core analysis
    sentiment_label = sentiment_analyzer(text)[0]['label']
    emotion_result = emotion_classifier(text)

    if emotion_result and emotion_result[0]:
        primary_emotion = emotion_result[0][0]['label']
    else:
        primary_emotion = "neutral"

    # Step 2: Extract a topic and format it into a safe, controlled snippet.
    topic = extract_topic(text)
    formatted_snippet = ""
    # Safety Check: only use the topic if it's short and seems valid.
    if topic and len(topic.split()) < 8:
        formatted_snippet = f"It sounds like you're dealing with {topic}."

    # Step 3: Get the full suggestion
    suggestion = get_empathetic_suggestion(primary_emotion, formatted_snippet)

    # Step 4: Return the final dictionary
    return {
        "text": text,
        "mood": primary_emotion.capitalize(),
        "sentiment": sentiment_label,
        "suggestion": suggestion
    }