# ---------------------- Imports ----------------------
import os
from functools import wraps
from collections import Counter

from flask import Flask, render_template, request, redirect, url_for, session
from dotenv import load_dotenv

# Google Sign-In verification
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

# Local project imports
from extensions import db
from models.nlp_analysis import analyze_text
from models.db_models import JournalEntry

# ---------------------- Configuration ----------------------

# Load environment variables from .env file
load_dotenv()

# Flask app setup
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///journal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Set a secret key for session management
app.secret_key = os.getenv("FLASK_SECRET_KEY")

# Initialize the database with the Flask app
db.init_app(app)

# Simple local login (for testing fallback)
USERNAME = 'user'
PASSWORD = 'pass123'

# ---------------------- Utility ----------------------

def login_required(f):
    """
    Decorator to ensure a user is logged in before accessing a route.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ---------------------- Core Routes ----------------------

@app.route('/')
@app.route('/home')
@login_required
def home():
    user = {
        "name": session.get('user_name'),
        "email": session.get('user_email'),
        "picture": session.get('user_picture')
    }
    return render_template('index.html', user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    # This now serves as a fallback login and the page with the Google Sign-In button
    error = None
    if request.method == 'POST':
        if request.form['username'] == USERNAME and request.form['password'] == PASSWORD:
            session['logged_in'] = True
            session['user_name'] = 'Local User'
            return redirect(url_for('home'))
        error = 'Invalid username or password.'
    
    # Pass the Google Client ID to the login template
    google_client_id = os.getenv("GOOGLE_CLIENT_ID")
    return render_template('login.html', error=error, google_client_id=google_client_id)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ---------------------- New Google Sign-In Route ----------------------

@app.route('/verify-google-token', methods=['POST'])
def verify_google_token():
    """
    Receives the ID token from the client-side, verifies it with Google,
    and creates a user session.
    """
    try:
        token = request.json['token']
        google_client_id = os.getenv("GOOGLE_CLIENT_ID")

        # Verify the token against Google's public keys
        id_info = id_token.verify_oauth2_token(
            token, 
            google_requests.Request(), 
            google_client_id
        )

        # Token is valid, create a session for the user
        session.clear()
        session['logged_in'] = True
        session['user_id'] = id_info.get('sub') # Google's unique user ID
        session['user_name'] = id_info.get('name')
        session['user_email'] = id_info.get('email')
        session['user_picture'] = id_info.get('picture')

        return {"success": True}

    except ValueError as e:
        # Invalid token
        return {"success": False, "message": f"Invalid token: {e}"}, 401
    except Exception as e:
        # Other errors
        return {"success": False, "message": f"An unexpected error occurred: {e}"}, 500

# ---------------------- Journal Feature Routes ----------------------

@app.route('/analyze', methods=['POST'])
@login_required
def analyze():
    entry = request.form['entry']
    result = analyze_text(entry)
    new_entry = JournalEntry(
        text=entry,
        sentiment=result['mood'],
        emotion=result.get('emotion', 'N/A'),
        suggestion=result['suggestion']
    )
    db.session.add(new_entry)
    db.session.commit()
    return render_template('result.html', result=result, text=entry)

@app.route('/history')
@login_required
def history():
    entries = JournalEntry.query.order_by(JournalEntry.date.desc()).all()
    return render_template('history.html', entries=entries)

@app.route('/delete/<int:entry_id>', methods=['POST'])
@login_required
def delete_entry(entry_id):
    entry = JournalEntry.query.get_or_404(entry_id)
    db.session.delete(entry)
    db.session.commit()
    return '', 204

@app.route('/edit/<int:entry_id>', methods=['GET', 'POST'])
@login_required
def edit_entry(entry_id):
    entry = JournalEntry.query.get_or_404(entry_id)
    if request.method == 'POST':
        entry.text = request.form['entry']
        result = analyze_text(entry.text)
        entry.sentiment = result['mood']
        entry.emotion = result.get('emotion', 'N/A')
        entry.suggestion = result['suggestion']
        db.session.commit()
        return render_template('result.html', result=result, text=entry.text)
    return render_template('edit.html', entry=entry)

@app.route('/dashboard')
@login_required
def dashboard():
    entries = JournalEntry.query.all()
    emotion_counts = Counter(entry.emotion for entry in entries)
    labels = list(emotion_counts.keys())
    values = list(emotion_counts.values())
    dates = [entry.date.strftime('%Y-%m-%d') for entry in entries]
    moods = [entry.sentiment for entry in entries]
    emotions = [entry.emotion for entry in entries]
    return render_template('dashboard.html', labels=labels, values=values, dates=dates, moods=moods, emotions=emotions)

# ---------------------- Run App ----------------------

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)