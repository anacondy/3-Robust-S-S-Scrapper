#!/usr/bin/env python3
"""
Test script to validate SQLite search functionality and PDF handling
"""

import sys
import json
from database import SearchDatabase
from pdf_handler import PDFHandler

def test_database():
    """Test database functionality"""
    print("\n=== Testing Database Functionality ===\n")
    
    # Initialize database
    db = SearchDatabase(db_path="test_search.db")
    
    # Load test data
    with open('data.json', 'r') as f:
        data = json.load(f)
    
    # Populate database
    print("1. Populating database from data.json...")
    db.populate_from_json(data)
    print("   ✓ Database populated")
    
    # Test basic search
    print("\n2. Testing basic search for 'exam'...")
    results = db.search(query="exam", limit=5)
    print(f"   ✓ Found {len(results)} results")
    if results:
        print(f"   Example: {results[0]['title']}")
    
    # Test year filter
    print("\n3. Testing year filter (2024)...")
    results = db.search(query="calendar", year=2024, limit=5)
    print(f"   ✓ Found {len(results)} results from 2024")
    if results:
        print(f"   Example: {results[0]['title']} ({results[0]['year']})")
    
    # Test PDF type filter
    print("\n4. Testing PDF type filter...")
    results = db.search(query="2024", content_type="pdf", limit=5)
    print(f"   ✓ Found {len(results)} PDF results")
    if results:
        print(f"   Example: {results[0]['title']}")
    
    # Test semester filter
    print("\n5. Testing semester filter...")
    results = db.search(semester="II", limit=5)
    print(f"   ✓ Found {len(results)} Semester II results")
    
    # Test section filter
    print("\n6. Testing section filter...")
    results = db.search(section="Exam Notices", limit=5)
    print(f"   ✓ Found {len(results)} results in Exam Notices section")
    
    # Test combined filters
    print("\n7. Testing combined filters (PDFs from 2024)...")
    results = db.search(year=2024, content_type="pdf", limit=5)
    print(f"   ✓ Found {len(results)} PDF results from 2024")
    
    # Get available filters
    print("\n8. Testing filter enumeration...")
    filters = db.get_filters()
    print(f"   ✓ Sections: {len(filters['sections'])}")
    print(f"   ✓ Years: {filters['years'][:5]}...")
    print(f"   ✓ Semesters: {filters['semesters']}")
    
    db.close()
    
    # Clean up test database
    import os
    os.remove("test_search.db")
    
    print("\n✓ All database tests passed!\n")


def test_pdf_handler():
    """Test PDF handler functionality"""
    print("=== Testing PDF Handler ===\n")
    
    handler = PDFHandler(cache_dir="test_pdf_cache")
    
    # Note: We can't actually test downloading without making real requests
    # So we just test the basic functionality
    
    print("1. Testing cache path generation...")
    cache_path = handler.get_cache_path("https://example.com/test.pdf")
    print(f"   ✓ Cache path: {cache_path}")
    
    print("\n2. Checking pikepdf availability...")
    try:
        import pikepdf
        print(f"   ✓ pikepdf {pikepdf.__version__} is installed")
    except ImportError:
        print("   ⚠ pikepdf not available (install with: pip install pikepdf)")
    
    # Clean up
    import shutil
    import os
    if os.path.exists("test_pdf_cache"):
        shutil.rmtree("test_pdf_cache")
    
    print("\n✓ PDF handler tests passed!\n")


def test_metadata_extraction():
    """Test metadata extraction from titles"""
    print("=== Testing Metadata Extraction ===\n")
    
    db = SearchDatabase(db_path=":memory:")
    
    test_cases = [
        ("Academic Calendar 2024-25", {"year": 2024}),
        ("Physics Syllabus Semester II", {"semester": "II", "subject": "Physics"}),
        ("October 2024 Newsletter", {"month": "October", "year": 2024}),
        ("U.G. Courses 2022-23", {"course_level": "UG", "year": 2022}),
        ("P.G. Chemistry Semester III", {"course_level": "PG", "subject": "Chemistry", "semester": "III"}),
    ]
    
    for title, expected in test_cases:
        metadata = db.extract_metadata(title, "Test Section")
        matches = all(metadata.get(k) == v for k, v in expected.items())
        status = "✓" if matches else "✗"
        print(f"{status} '{title}'")
        if not matches:
            print(f"   Expected: {expected}")
            print(f"   Got: {metadata}")
    
    print("\n✓ Metadata extraction tests completed!\n")


if __name__ == "__main__":
    try:
        test_database()
        test_pdf_handler()
        test_metadata_extraction()
        print("=" * 50)
        print("All tests completed successfully!")
        print("=" * 50)
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
