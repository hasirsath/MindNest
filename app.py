# ---------------------- Imports ----------------------
import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, abort
from dotenv import load_dotenv

# Google Sign-In verification
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

# Local project imports
from extensions import db
from services.nlp_analysis import analyze_text
from models.db_models import JournalEntry


# ---------------------- Configuration ----------------------

# Load environment variables from .env file
load_dotenv()

# Flask app setup
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///journal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv("FLASK_SECRET_KEY")
db.init_app(app)


USERNAME = 'user'
PASSWORD = 'pass123'

# ---------------------- Utility ----------------------

def login_required(f):
    """Decorator to ensure a user is logged in before accessing a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ---------------------- Core Routes ----------------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        # This block handles the simple username/password form
        if request.form.get('username') == USERNAME and request.form.get('password') == PASSWORD:
            session.clear()
            session['logged_in'] = True
            session['user_name'] = 'Local Test User'
            # Adds the required user_id to the session for the local user
            session['user_id'] = 'local_test_user_01'
            print("SESSION AFTER LOGIN:", session)
            return redirect(url_for('home'))
        else:
            error = 'Invalid username or password.'

    google_client_id = os.getenv("GOOGLE_CLIENT_ID")
    return render_template('login.html', error=error, google_client_id=google_client_id)



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



@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/verify-google-token', methods=['POST'])
def verify_google_token():
    """Receives the ID token from the client-side and creates a user session."""
    try:
        token = request.json['token']
        google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        id_info = id_token.verify_oauth2_token(
            token, google_requests.Request(), google_client_id
        )
        session.clear()
        session['logged_in'] = True
        session['user_id'] = id_info.get('sub') # Google's unique user ID
        session['user_name'] = id_info.get('name')
        session['user_email'] = id_info.get('email')
        session['user_picture'] = id_info.get('picture')
        return {"success": True}
    except Exception as e:
        return {"success": False, "message": str(e)}, 401

# ---------------------- Journal Feature Routes (Corrected) ----------------------
from services.music import get_music_recommendations
from services.media_client import get_media_recommendations

@app.route('/analyze', methods=['POST'])
@login_required
def analyze():
    entry_text = request.form['entry']
    if not entry_text.strip():
        return redirect(url_for('home'))

    result = analyze_text(entry_text)
    detected_mood = result['mood']
    music_recs = get_music_recommendations(detected_mood)
    video_recs = get_media_recommendations(detected_mood)
    
    new_entry = JournalEntry(
        text=entry_text,
        user_id=session['user_id'],     
        sentiment=result['sentiment'],  
        emotion=result['mood'],         
        suggestion=result['suggestion']
    )
    db.session.add(new_entry)
    db.session.commit()
    return render_template('result.html', result=result, text=entry_text, music_recs=music_recs, video_recs=video_recs)

@app.route('/history')
@login_required
def history():
    entries = JournalEntry.query.filter_by(user_id=session['user_id']).order_by(JournalEntry.date.desc()).all()
    return render_template('history.html', entries=entries)

@app.route('/delete/<int:entry_id>', methods=['POST'])
@login_required
def delete_entry(entry_id):
    entry = JournalEntry.query.get_or_404(entry_id)
    if entry.user_id != session['user_id']:
        abort(403) # Forbidden
        
    db.session.delete(entry)
    db.session.commit()
    return '', 204

@app.route('/edit/<int:entry_id>', methods=['GET', 'POST'])
@login_required
def edit_entry(entry_id):
    entry = JournalEntry.query.get_or_404(entry_id)
    if entry.user_id != session['user_id']:
        abort(403) # Forbidden

    if request.method == 'POST':
        entry.text = request.form['entry']
        result = analyze_text(entry.text)
        entry.sentiment = result['sentiment']
        entry.emotion = result['mood']
        entry.suggestion = result['suggestion']
        db.session.commit()
        return redirect(url_for('history'))
        
    return render_template('edit.html', entry=entry)

@app.route('/dashboard')
@login_required
def dashboard():
    print("SESSION BEFORE DASHBOARD:", session)
    entries = JournalEntry.query.filter_by(
        user_id=session['user_id']
    ).order_by(JournalEntry.date.asc()).all()

    dates = [entry.date.strftime('%Y-%m-%d') for entry in entries]
    moods = [entry.sentiment for entry in entries]
    emotions = [entry.emotion for entry in entries]
    
    return render_template('dashboard.html', dates=dates, moods=moods, emotions=emotions)

# ---------------------- Run App ----------------------

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)