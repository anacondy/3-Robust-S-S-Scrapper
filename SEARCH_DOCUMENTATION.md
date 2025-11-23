# Advanced Search and Fast PDF Viewing Documentation

## Overview

This document describes the advanced search functionality and fast PDF viewing features added to the Subodh Student Hub.

## Features

### 1. SQLite Database with Full-Text Search (FTS5)

#### Automatic Metadata Extraction

The system automatically extracts metadata from document titles:

- **Years**: Detects formats like `2024`, `2024-25`, `2024-2025`
- **Semesters**: Recognizes `I`, `II`, `III`, `IV`, `V`, `VI`, `1st`, `2nd`, etc.
- **Subjects**: Physics, Chemistry, Mathematics, Biology, Computer Science, English, Hindi, Commerce, Economics, History, Geography, Political Science, Sociology, Psychology, Statistics, Botany, Zoology, Microbiology, Biotechnology
- **Months**: January through December
- **Course Levels**: UG (Undergraduate), PG (Postgraduate)

#### Example Extractions

| Title | Extracted Metadata |
|-------|-------------------|
| "Academic Calendar 2024-25" | Year: 2024 |
| "Physics Syllabus Semester II" | Subject: Physics, Semester: II |
| "October 2024 Newsletter" | Month: October, Year: 2024 |
| "U.G. Courses 2022-23" | Course Level: UG, Year: 2022 |
| "P.G. Chemistry Semester III" | Course Level: PG, Subject: Chemistry, Semester: III |

### 2. Search API Endpoints

#### `/api/search` - Advanced Search

Search through all content with multiple filters.

**Query Parameters:**
- `q` (string, optional): Search query text
- `type` (string, optional): Filter by content type (`pdf` or `link`)
- `section` (string, optional): Filter by section name
- `year` (integer, optional): Filter by year
- `semester` (string, optional): Filter by semester (I, II, III, IV, V, VI)
- `subject` (string, optional): Filter by subject name
- `limit` (integer, default: 100): Maximum number of results

**Examples:**

```bash
# Search for "exam" in all content
GET /api/search?q=exam

# Find PDFs from 2024
GET /api/search?year=2024&type=pdf

# Search for Physics semester II materials
GET /api/search?q=physics&semester=II

# Find all content in Exam Notices section
GET /api/search?section=Exam%20Notices

# Combined filters: PDFs from 2024 containing "calendar"
GET /api/search?q=calendar&year=2024&type=pdf
```

**Response Format:**

```json
{
  "status": "success",
  "count": 5,
  "results": [
    {
      "id": 123,
      "title": "Academic Calendar 2024-25",
      "url": "https://...",
      "content_type": "pdf",
      "section": "Exam Notices",
      "year": 2024,
      "semester": null,
      "subject": null,
      "month": null,
      "course_level": null
    }
  ]
}
```

#### `/api/filters` - Get Available Filters

Returns all available filter options.

**Response:**

```json
{
  "status": "success",
  "filters": {
    "sections": ["Exam Notices", "Syllabus (UG)", ...],
    "years": [2025, 2024, 2023, ...],
    "semesters": ["I", "II", "III", "IV"],
    "subjects": ["Physics", "Chemistry", ...],
    "content_types": ["pdf", "link"]
  }
}
```

#### `/api/pdf/view` - Optimized PDF Viewer

View PDFs with automatic optimization for fast web viewing.

**Query Parameters:**
- `url` (string, required): URL of the PDF to view

**Example:**

```bash
GET /api/pdf/view?url=https://www.subodhpgcollege.com/pdf/example.pdf
```

**Features:**
- Automatic PDF linearization (fast web viewing)
- Stream compression
- Caching for repeated requests
- Progressive loading (first page displays before full download)

#### `/api/pdf/info` - PDF Metadata

Get metadata about a PDF without downloading the entire file.

**Query Parameters:**
- `url` (string, required): URL of the PDF

**Response:**

```json
{
  "status": "success",
  "info": {
    "pages": 45,
    "linearized": true,
    "encrypted": false,
    "title": "Academic Calendar",
    "author": "Subodh College"
  }
}
```

### 3. Frontend Usage

#### Basic Search

```javascript
// Simple text search
const response = await fetch('/api/search?q=physics');
const data = await response.json();
console.log(data.results);
```

#### Advanced Search with Filters

```javascript
// Search with multiple filters
const params = new URLSearchParams({
  q: 'syllabus',
  type: 'pdf',
  year: '2024',
  semester: 'II'
});

const response = await fetch(`/api/search?${params}`);
const data = await response.json();
```

#### Using Optimized PDF Viewer

```html
<!-- Instead of direct PDF link -->
<a href="https://example.com/document.pdf">View PDF</a>

<!-- Use optimized viewer -->
<a href="/api/pdf/view?url=https://example.com/document.pdf" target="_blank">
  View PDF (Fast)
</a>
```

### 4. Search Performance

The search system uses SQLite FTS5 (Full-Text Search 5) which provides:

- **Sub-millisecond search** on thousands of documents
- **Ranked results** by relevance
- **Prefix matching** (e.g., "phys" matches "physics")
- **Multiple term search** (e.g., "physics 2024" finds documents with both terms)

### 5. Database Schema

```sql
CREATE TABLE content (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    content_type TEXT NOT NULL,  -- 'pdf' or 'link'
    section TEXT NOT NULL,
    scraped_at TIMESTAMP,
    
    -- Extracted metadata
    year INTEGER,
    semester TEXT,
    subject TEXT,
    month TEXT,
    course_level TEXT,
    
    -- Full-text search
    search_text TEXT
);

-- FTS5 virtual table for fast search
CREATE VIRTUAL TABLE content_fts USING fts5(
    title, section, subject, semester, search_text
);
```

### 6. Configuration

#### Database Location

Default: `subodh_search.db` in the application root directory.

To change:
```python
from database import SearchDatabase
db = SearchDatabase(db_path="custom_path.db")
```

#### PDF Cache Location

Default: `pdf_cache/` directory in the application root.

To change:
```python
from pdf_handler import PDFHandler
handler = PDFHandler(cache_dir="custom_cache_dir")
```

#### Cache Management

Clear PDF cache:
```python
from pdf_handler import get_pdf_handler
handler = get_pdf_handler()
handler.clear_cache()
```

### 7. Performance Tips

1. **Use specific filters** when possible to reduce result set
2. **Combine filters** for precise results (e.g., year + type + section)
3. **Use the optimized PDF viewer** for faster PDF loading
4. **Keep the database updated** by running the scraper regularly

### 8. Testing

Run the test suite:

```bash
python test_search.py
```

This validates:
- Database population from JSON
- Basic search functionality
- Filter functionality (year, type, section, semester)
- Combined filters
- Metadata extraction
- PDF handler functionality

### 9. Troubleshooting

#### Search returns no results

- Check if the database is populated: `ls -lh subodh_search.db`
- Verify data.json exists and has content
- Try a broader search query

#### PDF viewer not working

- Ensure pikepdf is installed: `pip install pikepdf`
- Check PDF URL is accessible
- Verify SSL certificate issues are handled

#### Database not updating

- Run scraper to repopulate: `python scraper.py`
- Check database file permissions
- Restart the Flask app

### 10. Examples of Search Queries

| Search Query | URL | Description |
|--------------|-----|-------------|
| Find all exams | `/api/search?q=exam` | Search for "exam" in all fields |
| 2024 PDFs | `/api/search?year=2024&type=pdf` | All PDFs from 2024 |
| Physics materials | `/api/search?q=physics` | All physics-related content |
| Semester II syllabus | `/api/search?q=syllabus&semester=II` | Semester II syllabus documents |
| October events | `/api/search?q=october` | Events/documents from October |
| UG courses | `/api/search?q=ug%20courses` | Undergraduate course materials |
| Recent calendars | `/api/search?q=calendar&year=2024` | 2024 academic calendars |

## Architecture

```
┌─────────────────┐
│   Frontend      │
│  (HTML/JS)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────┐
│   Flask App     │─────▶│  Database    │
│   (app.py)      │      │  (SQLite)    │
└────────┬────────┘      └──────────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────┐
│  PDF Handler    │─────▶│  PDF Cache   │
│  (pikepdf)      │      │  (disk)      │
└─────────────────┘      └──────────────┘
```

## Dependencies

- **Flask 3.0.0**: Web framework
- **SQLite**: Built into Python (database)
- **pikepdf 8.7.1**: PDF optimization and linearization
- **requests**: HTTP client for PDF downloads
- **beautifulsoup4**: HTML parsing (for scraper)

## Security Considerations

1. **SQL Injection**: Prevented by using parameterized queries
2. **XSS**: Frontend properly escapes user input
3. **SSRF**: PDF handler only downloads from whitelisted domains
4. **File Storage**: PDF cache is separate from web-accessible directories

## Future Enhancements

Potential improvements:
- Add subject auto-detection using NLP
- Implement fuzzy search for typos
- Add search result highlighting
- Create search history feature
- Add bookmarking functionality
- Implement PDF text extraction for deeper search
