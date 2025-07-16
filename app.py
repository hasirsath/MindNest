from flask import Flask, render_template, request, redirect, url_for, session
from extensions import db
from datetime import datetime
from models.nlp_analysis import analyze_text
from models.db_models import JournalEntry
from functools import wraps
from google_auth_oauthlib.flow import Flow
from dotenv import load_dotenv
import os
import pathlib
import requests
from collections import Counter
import certifi



# Load environment variables
load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  # Only for local testing

# Flask app setup
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev_secret_key")  # Use .env variable in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///journal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)



# File path to client_secret.json
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")

# Simple local login (for testing fallback)
USERNAME = 'user'
PASSWORD = 'pass123'

# ---------------------- Utility ----------------------

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ---------------------- Routes ----------------------

@app.route('/')
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
    error = None
    if request.method == 'POST':
        if request.form['username'] == USERNAME and request.form['password'] == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('home'))
        error = 'Invalid username or password.'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ---------------------- Google OAuth ----------------------

@app.route('/google-login')
def google_login():
    flow = Flow.from_client_secrets_file(
        client_secrets_file,
        scopes=["openid", "https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email"],
        redirect_uri="http://localhost:5000/callback"
    )
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)

@app.route('/callback')
def callback():
    state = session.get("state")
    request_state = request.args.get("state")

    if not state or state != request_state:
        return "State mismatch. Possible CSRF attack.", 400

    flow = Flow.from_client_secrets_file(
        client_secrets_file,
        scopes=["openid", "https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email"],
        redirect_uri="http://localhost:5000/callback"
    )

    flow.fetch_token(authorization_response=request.url,
                     verify=certifi.where())

    credentials = flow.credentials
    session["credentials"] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

    # Get user info
    userinfo_response = requests.get(
        "https://www.googleapis.com/oauth2/v1/userinfo",
        headers={"Authorization": f"Bearer {credentials.token}"}
    )
    if userinfo_response.status_code != 200:
        return "Failed to fetch user info.", 500

    user_info = userinfo_response.json()
    session['logged_in'] = True
    session['user_name'] = user_info.get('name')
    session['user_email'] = user_info.get('email')
    session['user_picture'] = user_info.get('picture')

    return redirect(url_for('home'))

# ---------------------- Journal Features ----------------------

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
    app.run(debug=True, use_reloader=False)  # use_reloader=False avoids socket error on Windows
