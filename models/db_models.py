from datetime import datetime
from extensions import db
from cryptography.fernet import Fernet
import os

# Load the encryption key from environment variables
FERNET_MASTER_KEY = os.getenv("FERNET_MASTER_KEY")
if not FERNET_MASTER_KEY:
    raise ValueError("FERNET_MASTER_KEY not set in environment variables!")

fernet = Fernet(FERNET_MASTER_KEY.encode())

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False) 
    picture = db.Column(db.String(255), nullable=True)
    is_google_user = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    entries = db.relationship('JournalEntry', back_populates='author', lazy=True)

    def __repr__(self):
        return f'<User {self.name}>'

class JournalEntry(db.Model):
    __tablename__ = 'journal_entries'

    id = db.Column(db.Integer, primary_key=True)
    _text = db.Column("text", db.LargeBinary, nullable=False)  # store encrypted text as bytes
    sentiment = db.Column(db.String(50))
    emotion = db.Column(db.String(50))
    suggestion = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    author = db.relationship('User', back_populates='entries')

    # ---- Properties for Encryption ----
    @property
    def text(self):
        """Decrypt text when accessed."""
        try:
            return fernet.decrypt(self._text).decode()
        except Exception:
            return "[Decryption Failed]"

    @text.setter
    def text(self, value):
        """Encrypt text before storing."""
        if value:
            self._text = fernet.encrypt(value.encode())
        else:
            self._text = None

    def __repr__(self):
        return f'<JournalEntry {self.id}>'
