# ---------------------- Imports ----------------------
import os
from functools import wraps
from collections import Counter
from flask import Flask, render_template, request, redirect, url_for, session, abort, Response, flash
from dotenv import load_dotenv
#---------change------------
import base64
from io import BytesIO
from PIL import Image
from deepface import DeepFace
#------------------change over-------------------------------

# Google Sign-In verification
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

# Local project imports
from extensions import db
from services.nlp_analysis import analyze_text, get_detailed_suggestion
from models.db_models import JournalEntry
from models.db_models import User

#export
import csv
import io

#encryption
from cryptography.fernet import Fernet
import os

print("Loading DeepFace model... (this may take 20s the first time)")
deepface_model = DeepFace.build_model("VGG-Face")
print("DeepFace model loaded!")

load_dotenv()

FERNET_MASTER_KEY = os.getenv("FERNET_MASTER_KEY")
if not FERNET_MASTER_KEY:
    raise ValueError("FERNET_MASTER_KEY not set in environment variables!")
fernet = Fernet(FERNET_MASTER_KEY)


# Flask app setup
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///journal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv("FLASK_SECRET_KEY")
db.init_app(app)



# USERNAME = 'user'
# PASSWORD = 'pass123'

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

from werkzeug.security import generate_password_hash, check_password_hash

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not name or not email or not password or not confirm_password:
            error = "Please fill in all fields."
        elif password != confirm_password:
            error = "Passwords do not match."
        else:
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                error = "Email already registered."
            else:
                new_user = User(
                    name=name,
                    email=email,
                    is_google_user=False,
                    password=generate_password_hash(password)  # hashed
                )
                db.session.add(new_user)
                db.session.commit()
                return redirect(url_for('login'))

    return render_template('signup.html', error=error)


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            session.clear()
            session['logged_in'] = True
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['user_email'] = user.email
            session['user_picture'] = None
            return redirect(url_for('home'))
        else:
            error = 'Invalid email or password.'

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

@app.route('/profile')
@login_required
def profile():
    user = {
        "name": session.get('user_name'),
        "email": session.get('user_email'),
        "picture": session.get('user_picture')
    }
    return render_template('profile.html', user=user)

@app.route('/verify-google-token', methods=['POST'])
def verify_google_token():
    """Receives an ID token from the client, verifies it, and manages the user session."""
    try:
        token = request.json.get('token')
        if not token:
            return {"success": False, "message": "Token is missing"}, 400

        google_client_id = os.getenv("GOOGLE_CLIENT_ID")

        # Verify the token with Google
        id_info = id_token.verify_oauth2_token(
            token, 
            google_requests.Request(),
            google_client_id,
            clock_skew_in_seconds=10
        )

        # Check if user exists in our database
        user = User.query.filter_by(email=id_info.get('email')).first()

        if not user:
            # User does not exist, create a new one
            print(f"Creating new user for email: {id_info.get('email')}")
            user = User(
                name=id_info.get('name'),
                email=id_info.get('email'),
                picture=id_info.get('picture'), # Corrected field name
                is_google_user=True
            )
            db.session.add(user)
            db.session.commit()
        else:
            # User exists, ensure they are marked as a Google user
            if not user.is_google_user:
                user.is_google_user = True
                db.session.commit()
        
        # Create a new session for the user
        session.clear()
        session['logged_in'] = True
        session['user_id'] = user.id  # This is your app's local user ID
        session['user_name'] = user.name
        session['user_email'] = user.email
        session['user_picture'] = user.picture
        
        return {"success": True}
    
    except ValueError as e:
        print(f"TOKEN VERIFICATION FAILED: {e}")
        return {"success": False, "message": "Invalid or expired token", "details": str(e)}, 401
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return {"success": False, "message": "An internal error occurred"}, 500

# ---------------------- Journal Feature Routes (Corrected) ----------------------

from services.media_client import get_media_recommendations
from services.music import get_music_recommendations


@app.route('/analyze', methods=['POST'])
@login_required
def analyze():
    entry_text = request.form['entry']
    if not entry_text.strip():
        return redirect(url_for('home'))

    # 🧠 Run NLP analysis
    result = analyze_text(entry_text)
    detected_mood = result['mood']

    # 🎶 Get Spotify playlists dynamically
    music_recs = get_music_recommendations(detected_mood)

    # 🎥 Get YouTube video recommendations
    video_recs = get_media_recommendations(detected_mood, region="IN")[:2] 

    # 🔒 Encrypt text before saving
    encrypted_text = fernet.encrypt(entry_text.encode()).decode()

    new_entry = JournalEntry(
        text=encrypted_text,
        user_id=session['user_id'],
        sentiment=result['sentiment'],
        emotion=result['mood'],
        suggestion=result['suggestion']
    )
    db.session.add(new_entry)
    db.session.commit()
    
    return render_template(
        'result.html',
        result=result,
        text=entry_text,  # show decrypted/original text in UI
        music_recs=music_recs,
        video_recs=video_recs
    )



@app.route('/history')
@login_required
def history():
    entries = JournalEntry.query.filter_by(user_id=session['user_id']).order_by(JournalEntry.date.desc()).all()

    # 🔓 Decrypt before rendering
    for entry in entries:
        entry.text = fernet.decrypt(entry.text.encode()).decode()

    return render_template('history.html', entries=entries)


@app.route('/edit/<int:entry_id>', methods=['GET', 'POST'])
@login_required
def edit_entry(entry_id):
    entry = JournalEntry.query.get_or_404(entry_id)
    if entry.user_id != session['user_id']:
        abort(403) 

    if request.method == 'POST':
        updated_text = request.form['entry']
        encrypted_text = fernet.encrypt(updated_text.encode()).decode()

        entry.text = encrypted_text
        result = analyze_text(updated_text)
        entry.sentiment = result['sentiment']
        entry.emotion = result['mood']
        entry.suggestion = result['suggestion']
        db.session.commit()
        return redirect(url_for('history'))

    # 🔓 Decrypt before rendering edit form
    entry.text = fernet.decrypt(entry.text.encode()).decode()
    return render_template('edit.html', entry=entry)

@app.route('/delete/<int:id>', methods=['POST'])
def delete_entry(id):
    entry = JournalEntry.query.get(id)
    if entry:
        db.session.delete(entry)
        db.session.commit()
    return redirect(url_for('history'))


@app.route('/dashboard')
@login_required
def dashboard():
    entries = JournalEntry.query.filter_by(
        user_id=session['user_id']
    ).order_by(JournalEntry.date.asc()).all()

    # 🔓 Decrypt for charts if needed
    for entry in entries:
        entry.text = fernet.decrypt(entry.text.encode()).decode()

    dates = [entry.date.strftime('%Y-%m-%d') for entry in entries]
    moods = [entry.sentiment for entry in entries]
    emotions = [entry.emotion for entry in entries]
    
    return render_template('dashboard.html', dates=dates, moods=moods, emotions=emotions)


@app.route('/users')
@login_required
def users():
    google_users = User.query.filter_by(is_google_user=True).order_by(User.created_at.desc()).all()
    local_users = User.query.filter_by(is_google_user=False).order_by(User.created_at.desc()).all()
    return render_template('users.html', google_users=google_users, local_users=local_users)


@app.route('/export/csv')
@login_required
def export_csv():
    entries = JournalEntry.query.filter_by(user_id=session['user_id']).order_by(JournalEntry.date.asc()).all()

    string_io = io.StringIO()
    csv_writer = csv.writer(string_io)

    csv_writer.writerow(['Date', 'Sentiment', 'Emotion', 'Text', 'Suggestion'])

    for entry in entries:
        decrypted_text = fernet.decrypt(entry.text.encode()).decode()
        csv_writer.writerow([
            entry.date.strftime('%Y-%m-%d %H:%M:%S'),
            entry.sentiment,
            entry.emotion,
            decrypted_text,
            entry.suggestion
        ])

    output = string_io.getvalue()
    string_io.close()

    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=journal_history.csv"}
    )

@app.route('/about')
def about():
    return render_template('About.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

# ---------------------- Face Detection ----------------------
@app.route('/analyze_face', methods=['GET', 'POST'])
@login_required
def analyze_face():
    emotion, suggestion = None, None
    upload_folder = os.path.join('static', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)

    try:
        if request.method == 'POST':
            # Webcam input
            if 'webcam_image' in request.form and request.form['webcam_image']:
                img_data = request.form['webcam_image']
                header, encoded = img_data.split(',', 1)
                img_bytes = base64.b64decode(encoded)
                filepath = os.path.join(upload_folder, 'webcam_capture.png')
                Image.open(BytesIO(img_bytes)).save(filepath)

            # File upload
            elif 'face_image' in request.files:
                file = request.files['face_image']
                if not file.filename:
                    flash('No selected file')
                    return redirect(request.url)
                filepath = os.path.join(upload_folder, file.filename)
                file.save(filepath)

            else:
                flash('No image provided')
                return redirect(request.url)

            # Run DeepFace
            result = DeepFace.analyze(
                img_path=filepath,
                actions=['emotion'],
                enforce_detection=False,
                model=deepface_model
            )

            if isinstance(result, list):
                emotion = result[0].get('dominant_emotion', 'No face detected')
            else:
                emotion = result.get('dominant_emotion', 'No face detected')

            if emotion and emotion != 'No face detected':
                suggestion = get_detailed_suggestion('Neutral', emotion)

                # Save to history (webcam only, optional)
                if 'webcam_image' in request.form:
                    new_entry = JournalEntry(
                        text='Webcam Entry',
                        user_id=session['user_id'],
                        sentiment='N/A',
                        emotion=emotion,
                        suggestion=suggestion
                    )
                    db.session.add(new_entry)
                    db.session.commit()

        return render_template('analyze_face.html', emotion=emotion, suggestion=suggestion)

    except Exception as e:
        flash(f'Error analyzing image: {e}')
        return redirect(request.url)
    finally:
        if 'filepath' in locals() and os.path.exists(filepath):
            os.remove(filepath)


# ---------------------- Run App ----------------------

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)