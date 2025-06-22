from flask import Flask, render_template, request, redirect, url_for, session, Response
from flask_sqlalchemy import SQLAlchemy
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

@app.route('/dashboard')
def dashboard():
    entries = JournalEntry.query.order_by(JournalEntry.timestamp).all()
    dates = [entry.timestamp.strftime('%Y-%m-%d') for entry in entries]
    moods = [entry.sentiment for entry in entries]
    emotions = [entry.emotion for entry in entries]
    return render_template('dashboard.html', dates=dates, moods=moods, emotions=emotions)

@app.route('/history')
def history():
    entries = JournalEntry.query.order_by(JournalEntry.timestamp.desc()).all()
    return render_template('history.html', entries=entries)

@app.route('/delete/<int:entry_id>', methods=['POST'])
def delete_entry(entry_id):
    entry = JournalEntry.query.get_or_404(entry_id)
    db.session.delete(entry)
    db.session.commit()
    return ('', 204)

@app.route('/edit/<int:entry_id>', methods=['GET', 'POST'])
def edit_entry(entry_id):
    entry = JournalEntry.query.get_or_404(entry_id)
    if request.method == 'POST':
        entry.text = request.form['entry']
        # Re-analyze the updated text
        from models.nlp_analysis import analyze_text
        result = analyze_text(entry.text)
        entry.sentiment = result['mood']
        entry.emotion = result.get('emotion', 'N/A')
        entry.suggestion = result['suggestion']
        db.session.commit()
        return render_template('result.html', result=result, text=entry.text)
    return render_template('edit.html', entry=entry)

@app.route('/export')
def export_csv():
    entries = JournalEntry.query.order_by(JournalEntry.timestamp.desc()).all()
    def generate():
        data = [['Date', 'Entry', 'Mood', 'Emotion', 'Suggestion']]
        for e in entries:
            data.append([
                e.timestamp.strftime('%Y-%m-%d %H:%M'),
                e.text,
                e.sentiment,
                e.emotion,
                e.suggestion
            ])
        for row in data:
            yield ','.join('"' + str(item).replace('"', '""') + '"' for item in row) + '\n'
    return Response(generate(), mimetype='text/csv', headers={"Content-Disposition": "attachment;filename=journal_entries.csv"})

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] == USERNAME and request.form['password'] == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('home'))
        else:
            error = 'Invalid username or password.'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

# Decorator to require login
from functools import wraps
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Protect routes
app.route = lambda rule, **options: (lambda f: Flask.route(app, rule, **options)(login_required(f)) if rule not in ['/login', '/logout'] else Flask.route(app, rule, **options)(f))


if __name__ == '__main__':
    app.run(debug=True)
