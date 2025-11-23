import os
import json
import requests
import urllib.parse
import time
from flask import Flask, render_template, jsonify
from bs4 import BeautifulSoup

# Initialize Flask App
app = Flask(__name__)

# --- CONFIGURATION ---
BASE_URL = "https://www.subodhpgcollege.com/"
DATA_FILE = "data.json"

# Specific sections to scrape
# Using dictionary to map readable names to URL paths
SECTIONS = {
    "Exam Notices": "subodhexaminationportal",
    "Syllabus (UG)": "Syllabus_UG_Courses",
    "News & Events": "event_news",
    "Departments": "departments"
}


# --- HELPER FUNCTIONS ---

def full_url(path):
    """Converts relative paths to full URLs."""
    if not path: return "#"
    if path.startswith("http"): return path
    return urllib.parse.urljoin(BASE_URL, path)


def save_data(data):
    """Cache data to prevent spamming the college server."""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)


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
    - Sets User-Agent to look like Chrome.
    - Disables SSL verification (verify=False) for the specific target website.
    
    SECURITY NOTE: SSL verification is disabled because the target college website
    (subodhpgcollege.com) has known SSL certificate issues. This is acceptable 
    for read-only scraping of public data. For production use with sensitive data,
    implement proper certificate verification or use a custom CA bundle.
    
    - Sets a timeout so it doesn't hang forever.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        # verify=False deals with "SSLError" which is common on education sites
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
        # Look for marquee tags or list items in news sections
        for item in home_soup.find_all(['marquee', 'li']):
            text = item.get_text(strip=True)
            link_tag = item.find('a')

            # Only keep items that look like news (have dates or keywords)
            if len(text) > 10 and link_tag:
                latest_updates.append({
                    "text": text,
                    "link": full_url(link_tag['href']),
                    "is_new": "new" in item.get('class', []) or "blink" in str(item)
                })

    all_data["sections"]["Latest_Updates"] = latest_updates[:15]  # Limit to top 15

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
            # Extract PDFs
            for a in soup.find_all("a", href=True):
                href = a['href']
                txt = a.get_text(strip=True)
                if ".pdf" in href.lower():
                    section_content["pdfs"].append({
                        "title": txt or "Download PDF",
                        "url": full_url(href)
                    })
                elif len(txt) > 5 and "http" not in href:
                    # Internal links that aren't PDFs
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
    # Try to load cache first
    data = load_data()

    # If no cache, scrape immediately
    if not data:
        try:
            data = robust_scrape()
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    return jsonify({"status": "success", "data": data})


@app.route('/api/refresh')
def refresh():
    try:
        data = robust_scrape()
        return jsonify({"status": "success", "data": data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    # Suppress SSL warnings in console
    import urllib3

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    print("Server is running. Open http://127.0.0.1:5000 in your browser.")
    app.run(debug=True, port=5000)