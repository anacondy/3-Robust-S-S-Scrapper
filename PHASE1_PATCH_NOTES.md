# Phase 1 — Critical Security Patches

These patches fix the four deploy-blocking issues found in the review:

1. **Stored XSS** in `templates/index.html` and `docs/index.html`
2. **SSRF** in the PDF proxy (`app.py` + `pdf_handler.py`)
3. **Flask debug mode** enabled in production (`app.py`)
4. **SQLite thread-unsafe connection sharing** (`database.py`)

## Files in this patch set

```
patches/phase1/
├── app.py              # SSRF validation, debug toggle, safe error messages, rate/cap inputs
├── database.py         # Thread-safe connections, atomic populate, improved FTS5 sanitization
├── pdf_handler.py      # Defense-in-depth URL validation inside PDF downloader
├── templates/
│   └── index.html      # Escapes all scraped text before DOM insertion
└── docs/
    └── index.html      # Same XSS fix for the static GitHub Pages version
```

## How to apply

1. **Back up your current files** (optional but recommended).
2. Download all files from `patches/phase1/` in the workspace.
3. Copy them into your project root, replacing the originals:
   ```powershell
   # In your project root
   cp patches/phase1/app.py .
   cp patches/phase1/database.py .
   cp patches/phase1/pdf_handler.py .
   cp patches/phase1/templates/index.html templates/
   cp patches/phase1/docs/index.html docs/
   ```
4. Install/verify updated dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
5. Run the scraper to regenerate the database with the new schema:
   ```powershell
   python scraper.py
   ```
6. Run the app locally and verify:
   ```powershell
   python app.py
   ```
   Open `http://127.0.0.1:5000`.

## Environment variables for production

Set these on your hosting platform (Render/Heroku/PythonAnywhere/etc.):

```bash
FLASK_DEBUG=False
PORT=5000          # platform usually overrides this
SECRET_KEY=<a-random-32-byte-hex-string>
```

On Windows PowerShell:
```powershell
$env:FLASK_DEBUG="False"
$env:PORT="5000"
$env:SECRET_KEY="your-random-hex-key"
python app.py
```

## What changed

### `app.py`
- Added `is_safe_url()` validator: blocks non-HTTP schemes, auth fragments, and private/reserved IPs.
- `FLASK_DEBUG` env var controls debug mode; defaults to `False`.
- Binds to `host='0.0.0.0'` and uses `PORT` env var.
- Caps `/api/search` `limit` to 500.
- Removes raw exception exposure from JSON error responses.
- Removes unreachable dead code in `pdf_info()`.
- Adds `X-Content-Type-Options` and `X-Frame-Options` headers.
- Sets a `SECRET_KEY`.

### `database.py`
- Creates a new SQLite connection per request/thread instead of sharing one global connection.
- Wraps `populate_from_json` in a transaction.
- Improves FTS5 query sanitization: strips all non-word characters, caps terms to 10.
- Changes `subject LIKE ?` to exact match `subject = ?` for performance/safety.

### `pdf_handler.py`
- Adds defense-in-depth URL validation inside `download_pdf()` so the PDF fetcher cannot be abused even if the API layer is bypassed.

### `templates/index.html` / `docs/index.html`
- Adds `escapeHtml()` helper.
- Escapes all scraped text, titles, and URLs before inserting into the DOM.
- Adds `rel="noopener noreferrer"` to external links.
- Adds `isSafeHref()` to block `javascript:` URLs in rendered links.
- Replaces `alert()` with proper error display in `refreshData()`.

## Verification checklist

- [ ] App starts with `python app.py` without errors.
- [ ] Search returns results.
- [ ] A malicious title like `"<script>alert(1)</script>"` renders as literal text, not a popup.
- [ ] `http://127.0.0.1:5000/api/pdf/view?url=http://169.254.169.254/latest/meta-data/` returns `403`.
- [ ] `http://127.0.0.1:5000/api/pdf/view?url=http://subodhpgcollege.com@evil.com/x.pdf` returns `403`.
- [ ] `http://127.0.0.1:5000/api/search?limit=9999999` still returns at most 500 results.

## Next steps

After Phase 1 is applied and verified, move to **Phase 2** (rate limiting, input validation hardening, dependency pinning, Dockerfile timeout, and scraper/app deduplication).

Also note: `SmartSearchDATEfixed.html` and `UpdatedIndexWithSysRegistry.html` contain the same XSS vulnerability. Either delete them if unused, or apply the same `escapeHtml()` pattern to their `render()` functions before deployment.
