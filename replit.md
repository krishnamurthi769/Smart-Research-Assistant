# Smart Research Assistant

## Overview

The Smart Research Assistant is a comprehensive Flask-based web application that provides AI-powered research capabilities across multiple content sources. The application enables users to analyze web content through URL scraping, upload and query PDF documents with Q&A functionality, monitor live RSS feeds for real-time insights, and access a comprehensive dashboard for usage analytics. This advanced research tool leverages Google's Gemini AI to generate professional summaries, answer questions, and provide evidence-based reports with proper citations.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Template Engine**: Flask's Jinja2 templating system with comprehensive UI components
- **Multi-page Interface**: Navigation-based application with dedicated sections for different features
- **Responsive Design**: Bootstrap-inspired CSS with grid layouts and mobile-friendly design
- **Interactive Components**: JavaScript-powered Q&A interface with async functionality
- **Security Features**: XSS protection through content sanitization and safe HTML rendering

### Backend Architecture
- **Web Framework**: Flask (Python) with SQLAlchemy ORM for database operations
- **Session Management**: User session tracking with unique session IDs for personalized experiences
- **Multi-source Processing**: Handles URLs, PDF documents, and RSS feeds through unified processing pipeline
- **Database Integration**: PostgreSQL database with comprehensive schema for analytics and citations
- **Security Hardening**: URL validation, file type enforcement, and CSRF protection

### Database Schema
- **ResearchSession**: User session tracking with statistics and metadata
- **Summary**: AI-generated summaries with source tracking and analytics
- **Citation**: Comprehensive source citations with relevance scoring
- **Document**: PDF document storage with metadata and content extraction
- **QASession**: Question-answer pairs linked to documents with confidence scoring
- **RSSFeed**: RSS feed management with update tracking and scheduling
- **RSSEntry**: Individual RSS entries with processing status and content
- **UsageStats**: Daily usage analytics and trend tracking

### Core Features

#### URL Research & Analysis
- **Web Scraping**: Intelligent content extraction from multiple URLs with bot detection avoidance
- **Security Validation**: SSRF protection through URL validation and private IP blocking
- **Content Processing**: HTML parsing, text extraction, and content normalization
- **Citation Generation**: Automatic source tracking with title extraction and relevance scoring

#### PDF Document Q&A System
- **File Upload Security**: PDF-only uploads with MIME type validation and secure filename handling
- **Content Extraction**: PyPDF2-based text extraction with page counting and metadata preservation
- **AI-Powered Q&A**: Context-aware question answering using document content and Gemini AI
- **Session Persistence**: Document storage linked to user sessions with access controls

#### Live RSS Feed Integration
- **Feed Management**: RSS feed addition, validation, and update scheduling
- **Content Aggregation**: Automatic parsing and storage of RSS entries with deduplication
- **Live Summarization**: Real-time summary generation from multiple RSS sources
- **Trend Analysis**: Cross-source analysis for emerging topics and key insights

#### Analytics Dashboard
- **Usage Tracking**: Comprehensive statistics on summaries, documents, Q&A queries, and citations
- **Visual Analytics**: Statistical cards, activity timelines, and citation relevance displays
- **Global Insights**: Platform-wide usage statistics and trend identification
- **Performance Metrics**: Session analytics, source diversity tracking, and engagement metrics

### Security Implementation
- **Input Validation**: Comprehensive URL validation with private IP and localhost blocking
- **File Security**: PDF-only uploads with MIME type verification and secure file handling
- **XSS Protection**: Content sanitization for AI-generated summaries with script tag filtering
- **Session Security**: Mandatory SESSION_SECRET environment variable for cryptographic security
- **Database Security**: SQLAlchemy ORM with parameterized queries and injection protection

### AI Integration
- **Provider**: Google Gemini AI (gemini-2.5-flash model) for high-quality text processing
- **Use Cases**: URL summarization, document Q&A, RSS feed analysis, and trend identification
- **Error Handling**: Comprehensive error management for API failures and rate limiting
- **Content Optimization**: Intelligent content truncation and context preservation for API efficiency

### External Dependencies

#### Core Libraries
- **Flask**: Web framework with SQLAlchemy integration
- **flask-sqlalchemy**: Database ORM with PostgreSQL support
- **psycopg2-binary**: PostgreSQL database adapter
- **requests**: HTTP client for web scraping and RSS feeds
- **beautifulsoup4**: HTML parsing and content extraction
- **PyPDF2**: PDF text extraction and metadata processing
- **feedparser**: RSS/Atom feed parsing and content normalization
- **google-genai**: Google Gemini AI API integration

#### External Services
- **Google Gemini AI**: Requires GEMINI_API_KEY for text processing and Q&A
- **PostgreSQL Database**: Requires DATABASE_URL for comprehensive data persistence
- **Target Websites**: Secure web scraping from user-provided URLs
- **RSS Feeds**: Real-time content aggregation from news sources and blogs

#### Environment Configuration
- **GEMINI_API_KEY**: Required for AI functionality and content processing
- **SESSION_SECRET**: Mandatory for session security and user authentication
- **DATABASE_URL**: PostgreSQL connection string for data persistence
- **Upload Security**: Configured file size limits and secure upload directory management

## Target Users

### Primary Audiences
- **Students**: Research paper writing, source compilation, and academic citation management
- **Teachers**: Course material preparation, trend monitoring, and educational content curation
- **Startup Founders**: Market research, competitive analysis, and industry trend tracking
- **Analysts**: Data compilation, source verification, and comprehensive report generation

### Key Differentiators
- **Multi-source Context**: Unified analysis across URLs, documents, and live feeds
- **Evidence-based Reports**: Automatic citation generation with source verification
- **Structured Analytics**: Professional reporting with relevance scoring and trend analysis
- **Real-time Intelligence**: Live RSS feed monitoring for emerging insights and breaking developments