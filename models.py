from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


# ============================
# PAPERS (unchanged)
# ============================

class Paper(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255))
    content = db.Column(db.Text)


# ============================
# THREADS
# ============================

class Thread(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.String(100), nullable=True)

    messages = db.relationship("Message", backref="thread", lazy=True)


# ============================
# MESSAGES
# ============================

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    thread_id = db.Column(
        db.Integer,
        db.ForeignKey("thread.id"),
        nullable=False
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    role = db.Column(db.String(50))  # user | assistant
    content = db.Column(db.Text)