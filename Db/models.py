from . import db
from flask_login import UserMixin

class users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), nullable=False)
    password = db.Column(db.String(102), nullable=False)
    articles = db.relationship('articles', backref='user', lazy=True)

    def __repr__(self):
        return f'User id:{self.id}, username:{self.username}'

class articles(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    username = db.Column(db.String(30), nullable=False, unique=True)
    service_type = db.Column(db.String(50), nullable=False)
    experience = db.Column(db.Integer, nullable=False)
    hourly_rate = db.Column(db.Float, nullable=False)
    is_visible = db.Column(db.Boolean, nullable=False)
    
    
    
    def __repr__(self):
        return f'Article service_type:{self.service_type}, experience:{self.experience}, hourly_rate:{self.hourly_rate}'