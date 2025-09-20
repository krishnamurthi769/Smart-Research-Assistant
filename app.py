import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, render_template
from google import genai

# Configure Gemini API
client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'))

# Initialize Flask app
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/summarize', methods=['POST'])
def summarize():
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
    
    for url in url_list:
        try:
            # Add protocol if missing
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Make request with headers to avoid blocking
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
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
                combined_text += f"\n\nContent from {url}:\n{text[:5000]}"  # Limit per URL
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
        prompt = f"Generate a concise professional summary in bullet points of the following content:\n\n{combined_text[:15000]}"  # Limit total content
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        if response.text:
            # Format bullet points for HTML display
            summary = response.text.replace('\n', '<br>')
            
            # Add scraping warnings if any
            if scraping_errors:
                summary += "<br><br><em>Note: Some URLs had issues: " + "; ".join(scraping_errors) + "</em>"
            
            return render_template('index.html', summary=summary)
        else:
            return render_template('index.html', error="Failed to generate summary from Gemini API.", original_urls=urls)
            
    except Exception as e:
        return render_template('index.html', error=f"Error calling Gemini API: {str(e)}", original_urls=urls)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)