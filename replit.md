# Smart Research Assistant

## Overview

The Smart Research Assistant is a Flask-based web application that allows users to input multiple URLs and receive AI-generated summaries of the content from those web pages. The application scrapes text content from provided URLs using web scraping techniques and leverages Google's Gemini AI to generate comprehensive summaries. This tool is designed to help users quickly digest information from multiple web sources without having to manually read through each page.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Template Engine**: Uses Flask's built-in Jinja2 templating system
- **User Interface**: Single-page application with a simple HTML form for URL input
- **Styling**: Inline CSS for basic styling and responsive design
- **Form Handling**: Standard HTML form submission with POST method

### Backend Architecture
- **Web Framework**: Flask (Python) - chosen for its simplicity and rapid development capabilities
- **Request Processing**: Single route handler for URL processing and summarization
- **Error Handling**: Basic error handling for invalid URLs and scraping failures
- **URL Processing**: Automatic protocol detection and addition (adds https:// if missing)

### Web Scraping Components
- **HTTP Client**: Uses `requests` library with custom headers to avoid bot detection
- **HTML Parsing**: BeautifulSoup for extracting text content from HTML pages
- **Timeout Management**: 10-second timeout for web requests to prevent hanging
- **User-Agent Spoofing**: Mimics browser requests to bypass basic bot protection

### AI Integration
- **AI Provider**: Google Gemini AI via the `google-genai` library
- **API Configuration**: Environment variable-based API key management
- **Content Processing**: Combines scraped text from multiple URLs for unified summarization

### Error Management
- **Input Validation**: Checks for empty or invalid URL inputs
- **Scraping Error Tracking**: Collects and reports scraping failures per URL
- **User Feedback**: Clear error messages displayed in the web interface

## External Dependencies

### Core Libraries
- **Flask**: Web framework for HTTP server and routing
- **requests**: HTTP client library for web scraping
- **beautifulsoup4**: HTML parsing and text extraction
- **google-genai**: Google Gemini AI integration

### External Services
- **Google Gemini AI**: Requires GEMINI_API_KEY environment variable for text summarization
- **Target Websites**: Scrapes content from user-provided URLs (external web pages)

### Environment Configuration
- **API Key Management**: Relies on environment variable `GEMINI_API_KEY` for authentication
- **Runtime Environment**: Designed to run in environments supporting Python Flask applications