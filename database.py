"""
SQLite Database Module for Subodh Student Hub
Provides advanced search functionality with full-text search,
filtering by content type, dates, semesters, and subjects.
"""

import sqlite3
import re
import json
from datetime import datetime
from typing import List, Dict, Any, Optional


class SearchDatabase:
    """Database handler for searchable content"""
    
    def __init__(self, db_path: str = "subodh_search.db"):
        self.db_path = db_path
        self.conn = None
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables and indexes"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Enable column access by name
        
        cursor = self.conn.cursor()
        
        # Create main content table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                content_type TEXT NOT NULL,  -- 'pdf' or 'link'
                section TEXT NOT NULL,       -- 'Exam Notices', 'Syllabus', etc.
                scraped_at TIMESTAMP,
                
                -- Extracted metadata for advanced search
                year INTEGER,                 -- Extracted year (e.g., 2024)
                semester TEXT,                -- 'I', 'II', 'III', etc.
                subject TEXT,                 -- Subject name if detected
                month TEXT,                   -- Month name if detected
                course_level TEXT,            -- 'UG', 'PG', etc.
                
                -- Full-text search
                search_text TEXT             -- Normalized text for searching
            )
        """)
        
        # Create full-text search virtual table
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS content_fts USING fts5(
                title,
                section,
                subject,
                semester,
                search_text,
                content='content',
                content_rowid='id'
            )
        """)
        
        # Create triggers to keep FTS index synchronized
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS content_ai AFTER INSERT ON content BEGIN
                INSERT INTO content_fts(rowid, title, section, subject, semester, search_text)
                VALUES (new.id, new.title, new.section, new.subject, new.semester, new.search_text);
            END
        """)
        
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS content_ad AFTER DELETE ON content BEGIN
                DELETE FROM content_fts WHERE rowid = old.id;
            END
        """)
        
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS content_au AFTER UPDATE ON content BEGIN
                DELETE FROM content_fts WHERE rowid = old.id;
                INSERT INTO content_fts(rowid, title, section, subject, semester, search_text)
                VALUES (new.id, new.title, new.section, new.subject, new.semester, new.search_text);
            END
        """)
        
        # Create indexes for faster filtering
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_content_type ON content(content_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_section ON content(section)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_year ON content(year)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_semester ON content(semester)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_subject ON content(subject)")
        
        self.conn.commit()
    
    def extract_metadata(self, title: str, section: str) -> Dict[str, Any]:
        """Extract metadata from title and section for better search"""
        metadata = {
            'year': None,
            'semester': None,
            'subject': None,
            'month': None,
            'course_level': None,
            'search_text': ''
        }
        
        title_lower = title.lower()
        
        # Extract year (4-digit or 2-digit academic year format)
        year_patterns = [
            r'20\d{2}',           # 2024
            r'\d{4}-\d{2}',       # 2024-25
            r'\d{4}-\d{4}',       # 2024-2025
        ]
        for pattern in year_patterns:
            match = re.search(pattern, title)
            if match:
                year_str = match.group()
                # Get first year from range (extract 4-digit year starting with 20)
                year_match = re.search(r'20\d{2}', year_str)
                if year_match:
                    metadata['year'] = int(year_match.group())
                    break
        
        # Extract semester (Roman numerals or text)
        semester_patterns = {
            r'\bI\b|\b1st\b|\bfirst\b': 'I',
            r'\bII\b|\b2nd\b|\bsecond\b': 'II',
            r'\bIII\b|\b3rd\b|\bthird\b': 'III',
            r'\bIV\b|\b4th\b|\bfourth\b': 'IV',
            r'\bV\b|\b5th\b|\bfifth\b': 'V',
            r'\bVI\b|\b6th\b|\bsixth\b': 'VI',
        }
        for pattern, sem_value in semester_patterns.items():
            if re.search(pattern, title, re.IGNORECASE):
                metadata['semester'] = sem_value
                break
        
        # Extract month names
        months = ['january', 'february', 'march', 'april', 'may', 'june',
                  'july', 'august', 'september', 'october', 'november', 'december']
        for month in months:
            if month in title_lower:
                metadata['month'] = month.capitalize()
                break
        
        # Extract course level
        if re.search(r'\bu\.?g\.?\b|\bundergraduate\b', title_lower):
            metadata['course_level'] = 'UG'
        elif re.search(r'\bp\.?g\.?\b|\bpostgraduate\b', title_lower):
            metadata['course_level'] = 'PG'
        
        # Extract subject names (common subjects)
        subjects = [
            'physics', 'chemistry', 'mathematics', 'biology', 'computer',
            'english', 'hindi', 'commerce', 'economics', 'history',
            'geography', 'political science', 'sociology', 'psychology',
            'statistics', 'botany', 'zoology', 'microbiology', 'biotechnology'
        ]
        for subject in subjects:
            if subject in title_lower:
                metadata['subject'] = subject.title()
                break
        
        # Create comprehensive search text
        search_parts = [
            title,
            section,
            metadata.get('subject', ''),
            metadata.get('semester', ''),
            metadata.get('month', ''),
            metadata.get('course_level', ''),
            str(metadata.get('year', ''))
        ]
        metadata['search_text'] = ' '.join(filter(None, search_parts)).lower()
        
        return metadata
    
    def populate_from_json(self, data: Dict[str, Any]):
        """Populate database from scraped JSON data"""
        cursor = self.conn.cursor()
        
        # Clear existing data
        cursor.execute("DELETE FROM content")
        
        scraped_at = data.get('meta', {}).get('scraped_at', datetime.now().isoformat())
        
        # Insert data from all sections
        for section_name, section_data in data.get('sections', {}).items():
            if section_name == 'Latest_Updates':
                # Handle updates differently
                for item in section_data:
                    metadata = self.extract_metadata(item['text'], section_name)
                    cursor.execute("""
                        INSERT INTO content 
                        (title, url, content_type, section, scraped_at, 
                         year, semester, subject, month, course_level, search_text)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        item['text'], item['link'], 'link', section_name, scraped_at,
                        metadata['year'], metadata['semester'], metadata['subject'],
                        metadata['month'], metadata['course_level'], metadata['search_text']
                    ))
            else:
                # Handle PDFs
                for pdf in section_data.get('pdfs', []):
                    metadata = self.extract_metadata(pdf['title'], section_name)
                    cursor.execute("""
                        INSERT INTO content 
                        (title, url, content_type, section, scraped_at,
                         year, semester, subject, month, course_level, search_text)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        pdf['title'], pdf['url'], 'pdf', section_name, scraped_at,
                        metadata['year'], metadata['semester'], metadata['subject'],
                        metadata['month'], metadata['course_level'], metadata['search_text']
                    ))
                
                # Handle Links
                for link in section_data.get('links', []):
                    metadata = self.extract_metadata(link['title'], section_name)
                    cursor.execute("""
                        INSERT INTO content 
                        (title, url, content_type, section, scraped_at,
                         year, semester, subject, month, course_level, search_text)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        link['title'], link['url'], 'link', section_name, scraped_at,
                        metadata['year'], metadata['semester'], metadata['subject'],
                        metadata['month'], metadata['course_level'], metadata['search_text']
                    ))
        
        self.conn.commit()
    
    def search(
        self,
        query: str = "",
        content_type: Optional[str] = None,
        section: Optional[str] = None,
        year: Optional[int] = None,
        semester: Optional[str] = None,
        subject: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Advanced search with multiple filters
        
        Args:
            query: Search query string
            content_type: Filter by 'pdf' or 'link'
            section: Filter by section name
            year: Filter by year
            semester: Filter by semester (I, II, III, etc.)
            subject: Filter by subject name
            limit: Maximum number of results
        
        Returns:
            List of matching items with relevance ranking
        """
        cursor = self.conn.cursor()
        
        # Build WHERE clause dynamically
        where_conditions = []
        params = []
        
        if query:
            # Use FTS5 for full-text search
            where_conditions.append("""
                id IN (
                    SELECT rowid FROM content_fts 
                    WHERE content_fts MATCH ?
                )
            """)
            # Sanitize FTS5 special characters to prevent query errors
            # FTS5 special chars: " ( ) - * AND OR NOT
            sanitized_query = query.replace('"', '').replace('(', '').replace(')', '').replace('*', '')
            # Create FTS5 query with OR terms for flexibility
            # Split on whitespace and filter empty strings
            terms = [term.strip() for term in sanitized_query.split() if term.strip()]
            if terms:
                fts_query = ' OR '.join(terms)
            else:
                # If no valid terms after sanitization, skip FTS search
                where_conditions.pop()
                fts_query = None
            
            if fts_query:
                params.append(fts_query)
        
        if content_type:
            where_conditions.append("content_type = ?")
            params.append(content_type)
        
        if section:
            where_conditions.append("section = ?")
            params.append(section)
        
        if year:
            where_conditions.append("year = ?")
            params.append(year)
        
        if semester:
            where_conditions.append("semester = ?")
            params.append(semester)
        
        if subject:
            where_conditions.append("subject LIKE ?")
            params.append(f"%{subject}%")
        
        # Construct query
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        sql = f"""
            SELECT 
                id, title, url, content_type, section,
                year, semester, subject, month, course_level
            FROM content
            WHERE {where_clause}
            ORDER BY 
                CASE 
                    WHEN year IS NOT NULL THEN year 
                    ELSE 0 
                END DESC,
                id DESC
            LIMIT ?
        """
        
        params.append(limit)
        
        cursor.execute(sql, params)
        
        # Convert to list of dicts
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row['id'],
                'title': row['title'],
                'url': row['url'],
                'content_type': row['content_type'],
                'section': row['section'],
                'year': row['year'],
                'semester': row['semester'],
                'subject': row['subject'],
                'month': row['month'],
                'course_level': row['course_level']
            })
        
        return results
    
    def get_filters(self) -> Dict[str, List[Any]]:
        """Get available filter options"""
        cursor = self.conn.cursor()
        
        filters = {
            'sections': [],
            'years': [],
            'semesters': [],
            'subjects': [],
            'content_types': ['pdf', 'link']
        }
        
        # Get unique sections
        cursor.execute("SELECT DISTINCT section FROM content ORDER BY section")
        filters['sections'] = [row[0] for row in cursor.fetchall()]
        
        # Get unique years
        cursor.execute("SELECT DISTINCT year FROM content WHERE year IS NOT NULL ORDER BY year DESC")
        filters['years'] = [row[0] for row in cursor.fetchall()]
        
        # Get unique semesters
        cursor.execute("SELECT DISTINCT semester FROM content WHERE semester IS NOT NULL ORDER BY semester")
        filters['semesters'] = [row[0] for row in cursor.fetchall()]
        
        # Get unique subjects
        cursor.execute("SELECT DISTINCT subject FROM content WHERE subject IS NOT NULL ORDER BY subject")
        filters['subjects'] = [row[0] for row in cursor.fetchall()]
        
        return filters
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


# Singleton instance
_db_instance = None

def get_db() -> SearchDatabase:
    """Get database singleton instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = SearchDatabase()
    return _db_instance
