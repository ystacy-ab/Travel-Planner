from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    start_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.Enum('planning', 'completed', name='project_status'), default='planning')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    places = db.relationship('ProjectPlace', backref='project', lazy=True, cascade="all, delete-orphan")

class ProjectPlace(db.Model):
    __tablename__ = 'project_places'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    external_id = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    visited = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)