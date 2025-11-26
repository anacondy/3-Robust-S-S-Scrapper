# Security Summary

## Overview

This document summarizes the security considerations and mitigations implemented in the advanced search and PDF viewing features.

## Security Measures Implemented

### 1. SSRF (Server-Side Request Forgery) Prevention

**Issue**: The PDF viewer endpoints accept URLs as parameters, which could potentially be exploited to access internal resources.

**Mitigation**: 
- URL validation implemented in `app.py` (lines 262-270, 295-303)
- Only allows URLs from trusted domains: `subodhpgcollege.com` and `www.subodhpgcollege.com`
- Returns HTTP 403 error for untrusted domains
- Domain validation happens BEFORE making any HTTP requests

**Code Location**: `app.py` - `view_pdf()` and `pdf_info()` functions

**Status**: ✅ Mitigated

### 2. SQL Injection Prevention

**Issue**: User-provided search queries could potentially contain malicious SQL.

**Mitigation**:
- All database queries use parameterized statements
- SQLite's parameter binding (`?` placeholders) prevents SQL injection
- No string concatenation of user input into SQL queries

**Code Location**: `database.py` - All SQL queries in `search()` method

**Status**: ✅ Mitigated

### 3. FTS5 Query Injection

**Issue**: SQLite FTS5 has special characters that could cause query errors or unexpected behavior if not properly handled.

**Mitigation**:
- Input sanitization removes FTS5 special characters: `"`, `(`, `)`, `*`
- Empty queries are handled gracefully
- FTS5 MATCH queries still use parameterized binding

**Code Location**: `database.py` - Lines 271-281

**Status**: ✅ Mitigated

### 4. SSL Certificate Verification

**Issue**: SSL verification is disabled for PDF downloads from the college website.

**Rationale**: 
- The target college website (subodhpgcollege.com) has SSL certificate configuration issues
- This is a common issue with educational institution websites in India
- Data being accessed is public and read-only
- No sensitive data is transmitted

**Mitigation**:
- SSL verification is disabled ONLY for the specific college domain
- URL validation ensures only trusted domains are accessed
- Comprehensive documentation of the security trade-off

**Code Location**: `pdf_handler.py` - Line 48

**Status**: ⚠️ Documented Trade-off (Acceptable for this use case)

### 5. Null Pointer/Attribute Errors

**Issue**: Regex pattern matching could fail and cause AttributeError.

**Mitigation**:
- Added null checks in year extraction logic
- Defensive programming with nested if statements
- Graceful degradation if metadata extraction fails

**Code Location**: `database.py` - Lines 115-121

**Status**: ✅ Mitigated

### 6. XSS (Cross-Site Scripting) Prevention

**Issue**: User input displayed in the frontend could contain malicious scripts.

**Mitigation**:
- Frontend properly encodes URLs using `encodeURIComponent()`
- Search results are properly escaped by the browser
- No direct HTML injection from user input

**Code Location**: `templates/index.html` - Line 457

**Status**: ✅ Mitigated

## CodeQL Analysis Results

### Alert: Full SSRF (py/full-ssrf)

**Location**: `pdf_handler.py:48`

**Description**: The URL in `requests.get()` depends on user-provided value.

**Assessment**: False positive / Acceptable risk
- URL validation happens in calling code (`app.py`) before this function is invoked
- The `download_pdf()` method is a private implementation detail
- Public API endpoints (`/api/pdf/view`, `/api/pdf/info`) validate URLs first
- This is an example of defense in depth where validation occurs at the API boundary

**Action**: No changes required. Security controls are properly implemented at the API layer.

## Best Practices Followed

1. ✅ **Parameterized Queries**: All SQL queries use parameter binding
2. ✅ **Input Validation**: URLs validated against whitelist before processing
3. ✅ **Input Sanitization**: FTS5 special characters removed from search queries
4. ✅ **Error Handling**: Exceptions caught and generic error messages returned
5. ✅ **Least Privilege**: Database has minimal permissions (read-only for search)
6. ✅ **Documentation**: All security trade-offs documented in code comments

## Recommendations for Production Deployment

If deploying to production with sensitive data, consider:

1. **SSL Certificates**: Work with college IT to fix SSL certificate issues, then re-enable verification
2. **Rate Limiting**: Add rate limiting to search and PDF endpoints to prevent abuse
3. **Logging**: Add security event logging for suspicious URL access attempts
4. **Content Security Policy**: Add CSP headers to prevent XSS attacks
5. **HTTPS Only**: Ensure the application is served over HTTPS
6. **Authentication**: Add authentication if the data becomes non-public

## Security Testing

All security measures have been validated through:
- Manual testing of URL validation
- Unit tests for database operations
- FTS5 query sanitization testing
- CodeQL static analysis

## Conclusion

The implementation follows security best practices appropriate for a public-facing read-only application. The identified SSRF risk is mitigated through URL validation at the API boundary. All other potential security issues have been addressed through proper input validation, parameterized queries, and defensive programming.

**Overall Security Status**: ✅ Secure for intended use case (public college resource portal)
