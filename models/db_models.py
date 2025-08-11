from datetime import datetime
from extensions import db

class JournalEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    sentiment = db.Column(db.String(50))
    emotion = db.Column(db.String(50))
    suggestion = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow)


    def __repr__(self):
        return f'<JournalEntry {self.id}>'
