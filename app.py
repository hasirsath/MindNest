from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
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

if __name__ == '__main__':
    app.run(debug=True)
