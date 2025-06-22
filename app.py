from flask import Flask, render_template, request
from extensions import db
from datetime import datetime
from models.nlp_analysis import analyze_text
from models.db_models import db, JournalEntry

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///journal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

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
    entries = JournalEntry.query.order_by(JournalEntry.timestamp.desc()).all()
    return render_template('history.html', entries=entries)

@app.route('/dashboard')
def dashboard():
    entries = JournalEntry.query.all()

    # Count frequency of each emotion
    from collections import Counter
    emotion_counts = Counter(entry.emotion for entry in entries)

    labels = list(emotion_counts.keys())
    values = list(emotion_counts.values())

    return render_template('dashboard.html', labels=labels, values=values)

if __name__ == '__main__':
    app.run(debug=True)
