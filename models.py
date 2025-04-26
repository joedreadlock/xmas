from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    role = Column(String(20), nullable=False, default='member')

    gifts_entered = relationship('Gift', back_populates='entered_by_user')
    claims = relationship('Claim', back_populates='claimed_by_user')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Gift(db.Model):
    __tablename__ = 'gifts'
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description_or_url = Column(Text)
    preview_image_url = Column(String(500), nullable=True)
    date_entered = Column(DateTime, default=datetime.utcnow)
    parents_only = Column(Boolean, default=False)
    entered_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    entered_by_user = relationship('User', back_populates='gifts_entered')
    claims = relationship('Claim', back_populates='gift', uselist=True)

class Claim(db.Model):
    __tablename__ = 'claims'
    id = Column(Integer, primary_key=True)
    gift_id = Column(Integer, ForeignKey('gifts.id'), nullable=False)
    claimed_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    date_claimed = Column(DateTime, default=datetime.utcnow)

    gift = relationship('Gift', back_populates='claims')
    claimed_by_user = relationship('User', back_populates='claims')

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    gift_id = Column(Integer, ForeignKey('gifts.id'), nullable=True)
    type = Column(String(50), nullable=False)
    date_sent = Column(DateTime, default=datetime.utcnow)
