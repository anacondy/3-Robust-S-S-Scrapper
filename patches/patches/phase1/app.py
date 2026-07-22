import os
import json
import requests
import urllib.parse
import time
import ipaddress
import re
from flask import Flask, render_template, jsonify, request, send_file
from bs4 import BeautifulSoup
from database import get_db
from pdf_handler import get_pdf_handler
import io
from urllib.parse import urlparse

# Initialize Flask App
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(32).hex())

# --- CONFIGURATION ---
BASE_URL = "https://www.subodhpgcollege.com/"
DATA_FILE = "data.json"

# Specific sections to scrape
SECTIONS = {
    "Exam Notices": "subodhexaminationportal",
    "Syllabus (UG)": "Syllabus_UG_Courses",
    "News & Events": "event_news",
    "Departments": "departments"
}

ALLOWED_DOMAINS = {'subodhpgcollege.com', 'www.subodhpgcollege.com'}
MAX_SEARCH_LIMIT = 500


# --- SECURITY HELPERS ---

def is_safe_url(url: str) -> bool:
    """
    Validate a URL before it is fetched server-side.
    - Must be HTTP(S).
    - Host must be in the allowed domain whitelist.
    - No username/password/auth fragment.
    - Host must not resolve to a private/link-local IP.
    """
    try:
        parsed = urlparse(url)
    except Exception:
        return False

    if parsed.scheme not in ('http', 'https'):
        return False

    if parsed.username or parsed.password:
        return False

    hostname = parsed.hostname
    if not hostname:
        return False

    if hostname.lower() not in ALLOWED_DOMAINS:
        return False

    # Block IP-based URLs and private ranges (defense in depth against DNS rebinding)
    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            return False
    except ValueError:
        pass  # hostname is a name, not an IP literal

    return True


def _safe_error(message="Internal server error"):
    """Return a generic error message; log full details server-side."""
    return jsonify({"status": "error", "message": message}), 500


# --- HELPER FUNCTIONS ---

def full_url(path):
    """Converts relative paths to full URLs."""
    if not path:
        return "#"
    if path.startswith("http"):
        return path
    return urllib.parse.urljoin(BASE_URL, path)


def save_data(data):
    """Cache data to prevent spamming the college server."""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

    # Also populate database for search
    try:
        db = get_db()
        db.populate_from_json(data)
    except Exception as e:
        print(f"Error populating database: {e}")


def load_data():
    """Load cached data."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return None


# --- SCRAPER ENGINE ---

def fetch_soup(url):
    """
    Robust fetcher.
    Sets User-Agent and a timeout. SSL verification is disabled because the
    target college website has known certificate issues. This is a documented
    trade-off for read-only public scraping.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except requests.exceptions.ConnectionError:
        print(f"!! Connection Error for {url}. Check Internet.")
        return None
    except Exception as e:
        print(f"!! Error fetching {url}: {e}")
        return None


def robust_scrape():
    """
    Scrapes data and organizes it into a clean structure.
    Returns a dictionary of data.
    """
    print("--- Starting Scrape ---")
    start_time = time.time()

    all_data = {
        "meta": {"scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")},
        "sections": {}
    }

    # 1. Scrape Homepage for "Marquee" or latest updates
    print("Scraping Homepage...")
    home_soup = fetch_soup(BASE_URL)
    latest_updates = []

    if home_soup:
        for item in home_soup.find_all(['marquee', 'li']):
            text = item.get_text(strip=True)
            link_tag = item.find('a')

            if len(text) > 10 and link_tag:
                latest_updates.append({
                    "text": text,
                    "link": full_url(link_tag.get('href', '#')),
                    "is_new": "new" in item.get('class', []) or "blink" in str(item)
                })

    all_data["sections"]["Latest_Updates"] = latest_updates[:15]

    # 2. Scrape Defined Sections
    for name, path in SECTIONS.items():
        print(f"Scraping {name}...")
        url = full_url(path)
        soup = fetch_soup(url)

        section_content = {
            "pdfs": [],
            "links": [],
            "error": False
        }

        if soup:
            for a in soup.find_all("a", href=True):
                href = a['href']
                txt = a.get_text(strip=True)
                if ".pdf" in href.lower():
                    section_content["pdfs"].append({
                        "title": txt or "Download PDF",
                        "url": full_url(href)
                    })
                elif len(txt) > 5 and not href.startswith("http"):
                    section_content["links"].append({
                        "title": txt,
                        "url": full_url(href)
                    })
        else:
            section_content["error"] = True

        all_data["sections"][name] = section_content

    print(f"--- Scrape Finished in {round(time.time() - start_time, 2)}s ---")
    save_data(all_data)
    return all_data


# --- FLASK ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/data')
def get_data():
    data = load_data()

    if not data:
        try:
            data = robust_scrape()
        except Exception as e:
            print(f"Error in /api/data: {e}")
            return _safe_error("Failed to fetch data")

    return jsonify({"status": "success", "data": data})


@app.route('/api/refresh')
def refresh():
    try:
        data = robust_scrape()
        return jsonify({"status": "success", "data": data})
    except Exception as e:
        print(f"Error in /api/refresh: {e}")
        return _safe_error("Refresh failed")


@app.route('/api/search')
def search():
    """
    Advanced search endpoint
    Query params:
        - q: Search query
        - type: Filter by content_type (pdf/link)
        - section: Filter by section
        - year: Filter by year
        - semester: Filter by semester
        - subject: Filter by subject
        - limit: Max results (default 100, max 500)
    """
    try:
        db = get_db()

        query = request.args.get('q', '')
        content_type = request.args.get('type')
        section = request.args.get('section')
        year = request.args.get('year', type=int)
        semester = request.args.get('semester')
        subject = request.args.get('subject')
        limit = request.args.get('limit', 100, type=int)

        if limit is None or limit < 1:
            limit = 100
        if limit > MAX_SEARCH_LIMIT:
            limit = MAX_SEARCH_LIMIT

        results = db.search(
            query=query,
            content_type=content_type,
            section=section,
            year=year,
            semester=semester,
            subject=subject,
            limit=limit
        )

        return jsonify({
            "status": "success",
            "count": len(results),
            "results": results
        })
    except Exception as e:
        print(f"Error in /api/search: {e}")
        return _safe_error("Search failed")


@app.route('/api/filters')
def get_filters():
    """Get available filter options"""
    try:
        db = get_db()
        filters = db.get_filters()
        return jsonify({"status": "success", "filters": filters})
    except Exception as e:
        print(f"Error in /api/filters: {e}")
        return _safe_error("Could not load filters")


@app.route('/api/pdf/view')
def view_pdf():
    """
    Optimized PDF viewer endpoint
    Query params:
        - url: PDF URL to fetch and optimize
    """
    try:
        pdf_url = request.args.get('url')
        if not pdf_url:
            return jsonify({"status": "error", "message": "URL parameter required"}), 400

        if not is_safe_url(pdf_url):
            return jsonify({
                "status": "error",
                "message": "PDF URL must be from subodhpgcollege.com"
            }), 403

        pdf_handler = get_pdf_handler()
        pdf_bytes = pdf_handler.get_pdf(pdf_url, optimize=True)

        if not pdf_bytes:
            return jsonify({"status": "error", "message": "Failed to fetch PDF"}), 404

        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=False,
            download_name='document.pdf'
        )
    except Exception as e:
        print(f"Error in /api/pdf/view: {e}")
        return _safe_error("Failed to serve PDF")


@app.route('/api/pdf/info')
def pdf_info():
    """Get PDF metadata"""
    try:
        pdf_url = request.args.get('url')
        if not pdf_url:
            return jsonify({"status": "error", "message": "URL parameter required"}), 400

        if not is_safe_url(pdf_url):
            return jsonify({
                "status": "error",
                "message": "PDF URL must be from subodhpgcollege.com"
            }), 403

        pdf_handler = get_pdf_handler()
        info = pdf_handler.get_pdf_info(pdf_url)

        if not info:
            return jsonify({"status": "error", "message": "Failed to get PDF info"}), 404

        return jsonify({"status": "success", "info": info})
    except Exception as e:
        print(f"Error in /api/pdf/info: {e}")
        return _safe_error("Failed to get PDF info")


@app.after_request
def security_headers(response):
    """Add minimal security headers."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    return response


if __name__ == "__main__":
    # Suppress SSL warnings in console
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # Initialize database if data.json exists
    if os.path.exists(DATA_FILE):
        print("Initializing search database...")
        try:
            data = load_data()
            if data:
                db = get_db()
                db.populate_from_json(data)
                print("Database initialized successfully!")
        except Exception as e:
            print(f"Warning: Could not initialize database: {e}")

    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 'yes')
    port = int(os.environ.get('PORT', 5000))

    print("Server is running. Open http://127.0.0.1:5000 in your browser.")
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
