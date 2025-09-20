import os
import uuid
import requests
import feedparser
from datetime import datetime, date
from urllib.parse import urlparse
from werkzeug.utils import secure_filename
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
from flask import Flask, request, render_template, redirect, url_for, session, jsonify, flash
from google import genai
from models import db, ResearchSession, Summary, Citation, Document, QASession, RSSFeed, RSSEntry, UsageStats

# IMPORTANT: KEEP THIS COMMENT
# Referenced from python_database integration blueprint

# Configure Gemini API
client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'))

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")
if not app.secret_key:
    raise ValueError("SESSION_SECRET environment variable is required for security")

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize database
db.init_app(app)

with app.app_context():
    db.create_all()

def is_safe_url(url):
    """Validate URL for security - prevent SSRF attacks"""
    try:
        parsed = urlparse(url)
        # Block private IP ranges and localhost
        if parsed.hostname:
            import ipaddress
            try:
                ip = ipaddress.ip_address(parsed.hostname)
                if ip.is_private or ip.is_loopback or ip.is_link_local:
                    return False
            except ValueError:
                # Not an IP address, continue with hostname validation
                pass
            
            # Block localhost variations
            if parsed.hostname.lower() in ['localhost', '127.0.0.1', '0.0.0.0']:
                return False
        
        # Only allow HTTP and HTTPS
        if parsed.scheme not in ['http', 'https']:
            return False
            
        return True
    except Exception:
        return False

def get_or_create_session():
    """Get or create a research session for the user"""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    session_id = session['session_id']
    user_ip = request.remote_addr
    
    research_session = ResearchSession.query.filter_by(session_id=session_id).first()
    if not research_session:
        research_session = ResearchSession(session_id=session_id, user_ip=user_ip)
        db.session.add(research_session)
        db.session.commit()
    
    return research_session

def update_usage_stats():
    """Update daily usage statistics"""
    today = date.today()
    usage_stat = UsageStats.query.filter_by(date=today).first()
    
    if not usage_stat:
        usage_stat = UsageStats(date=today)
        db.session.add(usage_stat)
    
    # Update stats
    usage_stat.total_sessions = ResearchSession.query.filter(
        ResearchSession.created_at >= datetime.combine(today, datetime.min.time())
    ).count()
    
    usage_stat.total_summaries = Summary.query.filter(
        Summary.created_at >= datetime.combine(today, datetime.min.time())
    ).count()
    
    usage_stat.total_documents = Document.query.filter(
        Document.upload_date >= datetime.combine(today, datetime.min.time())
    ).count()
    
    usage_stat.total_qa_queries = QASession.query.filter(
        QASession.created_at >= datetime.combine(today, datetime.min.time())
    ).count()
    
    db.session.commit()

@app.route('/')
def index():
    research_session = get_or_create_session()
    recent_summaries = Summary.query.filter_by(session_id=research_session.session_id)\
                                   .order_by(Summary.created_at.desc())\
                                   .limit(3).all()
    return render_template('index.html', recent_summaries=recent_summaries)

@app.route('/summarize', methods=['POST'])
def summarize():
    research_session = get_or_create_session()
    
    # Get URLs from form
    urls = request.form.get('urls', '').strip()
    
    # Handle empty input errors
    if not urls:
        return render_template('index.html', error="Please enter at least one URL.")
    
    # Split URLs by lines and filter out empty lines
    url_list = [url.strip() for url in urls.split('\n') if url.strip()]
    
    if not url_list:
        return render_template('index.html', error="Please enter valid URLs.")
    
    # Scrape text from all URLs
    combined_text = ""
    scraping_errors = []
    citations = []
    
    for url in url_list:
        try:
            # Add protocol if missing
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Validate URL for security
            if not is_safe_url(url):
                scraping_errors.append(f"Invalid or unsafe URL: {url}")
                continue
            
            # Make request with headers to avoid blocking
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title = soup.find('title')
            title_text = title.get_text().strip() if title else url
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Add to combined text if substantial content found
            if len(text) > 100:  # Only add if substantial content
                content_excerpt = text[:5000]  # Limit per URL
                combined_text += f"\n\nContent from {url}:\n{content_excerpt}"
                
                # Create citation
                citations.append({
                    'source_url': url,
                    'source_title': title_text[:200],
                    'excerpt': content_excerpt[:500] + "..." if len(content_excerpt) > 500 else content_excerpt
                })
            else:
                scraping_errors.append(f"Little content found at {url}")
                
        except requests.exceptions.RequestException as e:
            scraping_errors.append(f"Error accessing {url}: {str(e)}")
        except Exception as e:
            scraping_errors.append(f"Error processing {url}: {str(e)}")
    
    # Handle scraping errors gracefully
    if not combined_text and scraping_errors:
        error_msg = "Could not extract content from any URLs. " + "; ".join(scraping_errors)
        return render_template('index.html', error=error_msg, original_urls=urls)
    
    if not combined_text:
        return render_template('index.html', error="No substantial content found in any of the URLs.", original_urls=urls)
    
    # Call Gemini API
    try:
        prompt = f"Generate a concise professional summary with key takeaways in bullet points of the following content:\n\n{combined_text[:15000]}"  # Limit total content
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        if response.text:
            # Format bullet points for HTML display
            summary_text = response.text.replace('\n', '<br>')
            
            # Add scraping warnings if any
            if scraping_errors:
                summary_text += "<br><br><em>Note: Some URLs had issues: " + "; ".join(scraping_errors) + "</em>"
            
            # Save summary to database
            summary = Summary(
                session_id=research_session.session_id,
                content=response.text,
                source_type='url',
                word_count=len(response.text.split()),
                key_takeaways=response.text[:1000]  # First 1000 chars as key takeaways
            )
            db.session.add(summary)
            db.session.flush()  # Get the summary ID
            
            # Save citations
            for cite_data in citations:
                citation = Citation(
                    session_id=research_session.session_id,
                    summary_id=summary.id,
                    source_url=cite_data['source_url'],
                    source_title=cite_data['source_title'],
                    source_type='url',
                    excerpt=cite_data['excerpt'],
                    relevance_score=0.8  # Default relevance score
                )
                db.session.add(citation)
            
            # Update session stats
            research_session.summary_count += 1
            research_session.sources_processed += len(citations)
            
            db.session.commit()
            update_usage_stats()
            
            return render_template('index.html', summary=summary_text, citations=citations)
        else:
            return render_template('index.html', error="Failed to generate summary from Gemini API.", original_urls=urls)
            
    except Exception as e:
        return render_template('index.html', error=f"Error calling Gemini API: {str(e)}", original_urls=urls)

@app.route('/upload', methods=['GET', 'POST'])
def upload_document():
    if request.method == 'GET':
        return render_template('upload.html')
    
    research_session = get_or_create_session()
    
    if 'file' not in request.files:
        flash('No file selected')
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected')
        return redirect(request.url)
    
    if file and file.filename.lower().endswith('.pdf'):
        # Additional security checks
        if file.content_type and not file.content_type.startswith('application/pdf'):
            flash('Invalid file type. Only PDF files are allowed.')
            return redirect(request.url)
        
        filename = secure_filename(file.filename)
        if not filename or not filename.lower().endswith('.pdf'):
            flash('Invalid filename. Please upload a valid PDF file.')
            return redirect(request.url)
        
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        try:
            # Extract text from PDF
            reader = PdfReader(file_path)
            text_content = ""
            for page in reader.pages:
                text_content += page.extract_text() + "\n"
            
            if not text_content.strip():
                flash('Could not extract text from PDF')
                os.remove(file_path)
                return redirect(request.url)
            
            # Save document to database
            document = Document(
                filename=unique_filename,
                original_filename=filename,
                file_path=file_path,
                content=text_content,
                session_id=research_session.session_id,
                file_size=os.path.getsize(file_path),
                page_count=len(reader.pages)
            )
            db.session.add(document)
            db.session.commit()
            
            flash('PDF uploaded and processed successfully!')
            return redirect(url_for('qa_interface', doc_id=document.id))
            
        except Exception as e:
            flash(f'Error processing PDF: {str(e)}')
            if os.path.exists(file_path):
                os.remove(file_path)
            return redirect(request.url)
    else:
        flash('Please upload a PDF file')
        return redirect(request.url)

@app.route('/qa/<int:doc_id>')
def qa_interface(doc_id):
    research_session = get_or_create_session()
    document = Document.query.filter_by(id=doc_id, session_id=research_session.session_id).first()
    
    if not document:
        flash('Document not found')
        return redirect(url_for('upload_document'))
    
    qa_history = QASession.query.filter_by(document_id=doc_id)\
                               .order_by(QASession.created_at.desc()).all()
    
    return render_template('qa.html', document=document, qa_history=qa_history)

@app.route('/ask_question', methods=['POST'])
def ask_question():
    research_session = get_or_create_session()
    doc_id = request.form.get('doc_id')
    question = request.form.get('question', '').strip()
    
    if not question:
        return jsonify({'error': 'Please enter a question'})
    
    document = Document.query.filter_by(id=doc_id, session_id=research_session.session_id).first()
    if not document:
        return jsonify({'error': 'Document not found'})
    
    try:
        # Use Gemini to answer the question based on document content
        prompt = f"""Based on the following document content, answer this question: {question}

Document content:
{document.content[:10000]}  # Limit content length

Please provide a detailed answer based on the document. If the information is not in the document, say so clearly."""
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        if response.text:
            # Save Q&A session
            qa_session = QASession(
                session_id=research_session.session_id,
                document_id=doc_id,
                question=question,
                answer=response.text,
                confidence_score=0.85  # Default confidence
            )
            db.session.add(qa_session)
            db.session.commit()
            
            update_usage_stats()
            
            return jsonify({
                'answer': response.text,
                'timestamp': qa_session.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        else:
            return jsonify({'error': 'Failed to generate answer'})
            
    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'})

@app.route('/feeds')
def manage_feeds():
    feeds = RSSFeed.query.filter_by(is_active=True).all()
    return render_template('feeds.html', feeds=feeds)

@app.route('/add_feed', methods=['POST'])
def add_feed():
    feed_url = request.form.get('feed_url', '').strip()
    
    if not feed_url:
        flash('Please enter a valid RSS feed URL')
        return redirect(url_for('manage_feeds'))
    
    # Check if feed already exists
    existing_feed = RSSFeed.query.filter_by(url=feed_url).first()
    if existing_feed:
        flash('Feed already exists')
        return redirect(url_for('manage_feeds'))
    
    try:
        # Parse feed to validate and get info
        feed = feedparser.parse(feed_url)
        
        if feed.bozo:
            flash('Invalid RSS feed URL')
            return redirect(url_for('manage_feeds'))
        
        # Create new feed
        rss_feed = RSSFeed(
            url=feed_url,
            title=feed.feed.get('title', 'Unknown Feed')[:200],
            description=feed.feed.get('description', '')[:500]
        )
        db.session.add(rss_feed)
        db.session.commit()
        
        # Parse initial entries
        update_feed_entries(rss_feed.id)
        
        flash('RSS feed added successfully!')
        
    except Exception as e:
        flash(f'Error adding feed: {str(e)}')
    
    return redirect(url_for('manage_feeds'))

def update_feed_entries(feed_id):
    """Update entries for a specific RSS feed"""
    rss_feed = RSSFeed.query.get(feed_id)
    if not rss_feed:
        return
    
    try:
        feed = feedparser.parse(rss_feed.url)
        
        for entry in feed.entries[:10]:  # Limit to latest 10 entries
            # Check if entry already exists
            existing_entry = RSSEntry.query.filter_by(guid=entry.get('id', entry.link)).first()
            if existing_entry:
                continue
            
            # Parse published date
            published_date = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published_date = datetime(*entry.published_parsed[:6])
            
            # Create new entry
            rss_entry = RSSEntry(
                feed_id=feed_id,
                title=entry.get('title', 'No Title')[:300],
                link=entry.get('link', ''),
                description=entry.get('description', '')[:1000],
                published_date=published_date,
                guid=entry.get('id', entry.link)
            )
            db.session.add(rss_entry)
        
        rss_feed.last_updated = datetime.utcnow()
        db.session.commit()
        
    except Exception as e:
        print(f"Error updating feed {feed_id}: {str(e)}")

@app.route('/dashboard')
def dashboard():
    research_session = get_or_create_session()
    
    # Get user statistics
    user_summaries = Summary.query.filter_by(session_id=research_session.session_id).count()
    user_documents = Document.query.filter_by(session_id=research_session.session_id).count()
    user_qa_queries = QASession.query.filter_by(session_id=research_session.session_id).count()
    
    # Get recent activity
    recent_summaries = Summary.query.filter_by(session_id=research_session.session_id)\
                                   .order_by(Summary.created_at.desc()).limit(5).all()
    
    recent_documents = Document.query.filter_by(session_id=research_session.session_id)\
                                    .order_by(Document.upload_date.desc()).limit(5).all()
    
    # Get global usage stats
    today_stats = UsageStats.query.filter_by(date=date.today()).first()
    
    # Get top citations
    top_citations = Citation.query.filter_by(session_id=research_session.session_id)\
                                 .order_by(Citation.relevance_score.desc()).limit(10).all()
    
    return render_template('dashboard.html',
                         user_summaries=user_summaries,
                         user_documents=user_documents,
                         user_qa_queries=user_qa_queries,
                         recent_summaries=recent_summaries,
                         recent_documents=recent_documents,
                         today_stats=today_stats,
                         top_citations=top_citations)

@app.route('/refresh_feeds')
def refresh_feeds():
    """Manually refresh all RSS feeds"""
    feeds = RSSFeed.query.filter_by(is_active=True).all()
    updated_count = 0
    
    for feed in feeds:
        try:
            update_feed_entries(feed.id)
            updated_count += 1
        except Exception as e:
            print(f"Error updating feed {feed.id}: {str(e)}")
    
    flash(f'Updated {updated_count} RSS feeds')
    return redirect(url_for('manage_feeds'))

@app.route('/live_summary')
def live_summary():
    """Generate summary from latest RSS entries"""
    research_session = get_or_create_session()
    
    # Get latest unprocessed RSS entries
    recent_entries = RSSEntry.query.filter_by(is_processed=False)\
                                  .order_by(RSSEntry.published_date.desc())\
                                  .limit(20).all()
    
    if not recent_entries:
        flash('No new RSS entries to process')
        return redirect(url_for('manage_feeds'))
    
    # Combine content from recent entries
    combined_content = ""
    sources = []
    
    for entry in recent_entries:
        content = f"Title: {entry.title}\nDescription: {entry.description or 'N/A'}\nLink: {entry.link}\n\n"
        combined_content += content
        sources.append({
            'title': entry.title,
            'link': entry.link,
            'published': entry.published_date.strftime('%Y-%m-%d %H:%M') if entry.published_date else 'Unknown'
        })
    
    try:
        # Generate summary using Gemini
        prompt = f"Generate a comprehensive news summary with key trends and insights from these recent RSS feed entries:\n\n{combined_content[:15000]}"
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        if response.text:
            # Save summary
            summary = Summary(
                session_id=research_session.session_id,
                content=response.text,
                source_type='rss',
                word_count=len(response.text.split()),
                key_takeaways=response.text[:1000]
            )
            db.session.add(summary)
            db.session.flush()
            
            # Mark entries as processed and create citations
            for entry in recent_entries:
                entry.is_processed = True
                citation = Citation(
                    session_id=research_session.session_id,
                    summary_id=summary.id,
                    source_url=entry.link,
                    source_title=entry.title,
                    source_type='rss',
                    excerpt=entry.description[:500] if entry.description else '',
                    relevance_score=0.7
                )
                db.session.add(citation)
            
            db.session.commit()
            update_usage_stats()
            
            summary_html = response.text.replace('\n', '<br>')
            return render_template('live_summary.html', summary=summary_html, sources=sources)
        else:
            flash('Failed to generate live summary')
            return redirect(url_for('manage_feeds'))
            
    except Exception as e:
        flash(f'Error generating live summary: {str(e)}')
        return redirect(url_for('manage_feeds'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)