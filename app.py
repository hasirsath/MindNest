from flask import Flask, render_template, request
from extensions import db
from datetime import datetime
from models.nlp_analysis import analyze_text
from models.db_models import db, JournalEntry
import csv

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///journal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key_here'  # Change this to a strong secret in production

db.init_app(app)

# Simple user credentials (for demo; use a database in production)
USERNAME = 'user'
PASSWORD = 'pass123'

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    entry = request.form['entry']
    result = analyze_text(entry)

    new_entry = JournalEntry(
        text=entry,
        sentiment=result['mood'],
        emotion=result.get('emotion', 'N/A'),  # Add emotion later
        suggestion=result['suggestion']
    )

    db.session.add(new_entry)
    db.session.commit()

    return render_template('result.html', result=result, text=entry)

@app.route('/history')
def history():
    entries = JournalEntry.query.order_by(JournalEntry.date.desc()).all()
    return render_template('history.html', entries=entries)

@app.route('/dashboard')
def dashboard():
    entries = JournalEntry.query.all()

    # Count frequency of each emotion
    from collections import Counter
    emotion_counts = Counter(entry.emotion for entry in entries)

    labels = list(emotion_counts.keys())
    values = list(emotion_counts.values())
    dates = [entry.date.strftime('%Y-%m-%d') for entry in entries]
    moods = [entry.sentiment for entry in entries]
    emotions = [entry.emotion for entry in entries]

    return render_template('dashboard.html', labels=labels, values=values, dates=dates, moods=moods, emotions=emotions)

if __name__ == '__main__':
    app.run(debug=True)
