# IMPORTANT: KEEP THIS COMMENT
# Referenced from python_database integration blueprint
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


class ResearchSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), unique=True, nullable=False)
    user_ip = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    summary_count = db.Column(db.Integer, default=0)
    sources_processed = db.Column(db.Integer, default=0)
    
    # Relationships
    summaries = db.relationship('Summary', backref='session', lazy=True)
    citations = db.relationship('Citation', backref='session', lazy=True)


class Summary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), db.ForeignKey('research_session.session_id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    source_type = db.Column(db.String(20), nullable=False)  # 'url', 'pdf', 'rss'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    word_count = db.Column(db.Integer, default=0)
    key_takeaways = db.Column(db.Text, nullable=True)
    
    # Relationships
    citations = db.relationship('Citation', backref='summary', lazy=True)


class Citation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), db.ForeignKey('research_session.session_id'), nullable=False)
    summary_id = db.Column(db.Integer, db.ForeignKey('summary.id'), nullable=False)
    source_url = db.Column(db.String(500), nullable=True)
    source_title = db.Column(db.String(200), nullable=True)
    source_type = db.Column(db.String(20), nullable=False)  # 'url', 'pdf', 'rss'
    excerpt = db.Column(db.Text, nullable=True)
    relevance_score = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    original_filename = db.Column(db.String(200), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    content = db.Column(db.Text, nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    session_id = db.Column(db.String(100), nullable=False)
    file_size = db.Column(db.Integer, default=0)
    page_count = db.Column(db.Integer, default=0)


class QASession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), nullable=False)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    confidence_score = db.Column(db.Float, default=0.0)
    
    # Relationships
    document = db.relationship('Document', backref='qa_sessions', lazy=True)


class RSSFeed(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False, unique=True)
    title = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    update_frequency = db.Column(db.Integer, default=60)  # minutes
    
    # Relationships
    entries = db.relationship('RSSEntry', backref='feed', lazy=True)


class RSSEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    feed_id = db.Column(db.Integer, db.ForeignKey('rss_feed.id'), nullable=False)
    title = db.Column(db.String(300), nullable=False)
    link = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text, nullable=True)
    published_date = db.Column(db.DateTime, nullable=True)
    content = db.Column(db.Text, nullable=True)
    guid = db.Column(db.String(200), unique=True, nullable=False)
    is_processed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class UsageStats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, unique=True)
    total_summaries = db.Column(db.Integer, default=0)
    total_sessions = db.Column(db.Integer, default=0)
    total_documents = db.Column(db.Integer, default=0)
    total_qa_queries = db.Column(db.Integer, default=0)
    total_rss_entries = db.Column(db.Integer, default=0)
    avg_sources_per_session = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)