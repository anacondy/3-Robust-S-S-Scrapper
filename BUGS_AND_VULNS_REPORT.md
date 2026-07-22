# Subodh Student Hub — Code Review Report

**Project:** `3-Robust-S-S-Scrapper`  
**Reviewed:** 2026-06-22  
**Scope:** `app.py`, `scraper.py`, `database.py`, `pdf_handler.py`, `templates/index.html`, `docs/index.html`, deployment configs, tests.

---

## Executive Summary

The app is a functional Flask + BeautifulSoup scraper with an FTS5-backed search API and a Tailwind UI. It works, but it is **not production-safe** as-is. The most serious issues are **stored XSS via scraped HTML titles**, **SSRF in the PDF proxy**, **Flask debug mode enabled**, and **unsafe SQLite connection sharing across threads**. These can lead to code execution, internal network scanning, and data corruption.

Fixes are grouped into three phases. Phase 1 is mandatory before any public deployment.

---

## Phase 1 — Critical (Deploy Blockers)

| # | Severity | File | Issue | Impact | Fix |
|---|----------|------|-------|--------|-----|
| 1 | **P0** | `templates/index.html`, `docs/index.html`, `SmartSearchDATEfixed.html`, `UpdatedIndexWithSysRegistry.html` | Rendered scraped content (`item.text`, `pdf.title`, `link.title`) is injected via `innerHTML` without HTML escaping. If the college site serves a malicious `<script>` in a title/marquee, every visitor executes it. | Stored XSS → session hijacking, defacement, keylogging, malware delivery. | Escape HTML before DOM insertion; never use `innerHTML` with untrusted text. Use `textContent` or a small escape helper. |
| 2 | **P0** | `app.py` / `pdf_handler.py` | `/api/pdf/view` and `/api/pdf/info` only validate the URL in `app.py`. The actual `requests.get(..., verify=False)` happens in `pdf_handler.download_pdf()` with no secondary validation. Bypass techniques (open redirects, DNS rebinding, `@` auth tricks) can turn this into an internal network scanner or file:// fetcher. | SSRF → internal network scanning, cloud metadata theft, credential exfiltration. | Validate the URL **inside** `pdf_handler.download_pdf()` as well; block private/reserved IPs, non-HTTP schemes, and auth fragments. |
| 3 | **P0** | `app.py` | `app.run(debug=True, port=5000)` runs the Werkzeug debug console. In production this gives anyone an interactive Python shell. | RCE → full server compromise. | Bind `debug` to an environment variable and default to `False`; use `host='0.0.0.0'` and the `PORT` env var. |
| 4 | **P0** | `database.py` | `sqlite3.connect(self.db_path, check_same_thread=False)` returns a single connection used globally by Flask's threaded server. SQLite connections are not thread-safe; this causes `SIGSEGV`/corruption and `sqlite3.ProgrammingError` under concurrent requests. | Crash / data corruption / undefined behavior. | Create a connection per request/thread, or use a connection pool / `LocalProxy` pattern. |
| 5 | **P1** | `app.py`, `scraper.py`, `pdf_handler.py` | `requests.get(..., verify=False)` disables TLS verification everywhere. Combined with SSRF, this makes MITM trivial. | Data tampering, credential sniffing on downstream calls. | Pin the target's certificate fingerprint or use a custom CA bundle; keep `verify=False` only as a last resort and document it. |

---

## Phase 2 — High (Stability & Abuse)

| # | Severity | File | Issue | Impact | Fix |
|---|----------|------|-------|--------|-----|
| 6 | **P1** | `app.py` | Every route returns raw exception strings: `return jsonify({"message": str(e)}), 500`. This leaks internal paths, SQL queries, and stack details. | Information disclosure aids further attacks. | Log the traceback server-side; return generic `{"message": "Internal server error"}`. |
| 7 | **P1** | `app.py` | No rate limiting on `/api/refresh`, `/api/pdf/view`, `/api/search`. An attacker can abuse the PDF proxy to burn bandwidth or the refresh endpoint to hammer the college site from your server. | Resource exhaustion, IP reputation damage, cost. | Add Flask-Limiter or simple per-IP memory-based rate limits. |
| 8 | **P1** | `database.py` | FTS5 query sanitization removes only `"`, `(`, `)`, `*`. Terms like `NOT`, `OR`, `AND`, `-`, `^` are still passed, allowing FTS5 syntax injection and unexpected MATCH behavior. | Query manipulation, possible errors/denial. | Strip all FTS5 operators and normalize to plain terms; fallback to `LIKE` if no valid terms remain. |
| 9 | **P1** | `app.py` | `limit` query param has no upper bound; a value like `limit=2147483647` can be passed to SQLite and downstream rendering. | CPU/memory DoS. | Cap `limit` to a reasonable max (e.g., 500). |
| 10 | **P1** | `app.py` `pdf_info()` | Dead/unreachable code after the `return ... 403` block. | Maintenance confusion; unreachable branch is misleading. | Remove the unreachable `return`. |
| 11 | **P1** | `database.py` | Subject filter uses `subject LIKE ?` with `%subject%`. This is safe from SQLi but allows very broad/expensive wildcard matches. | Performance degradation. | Use exact-match or prefix index; keep `LIKE` only if substring search is required. |
| 12 | **P1** | `templates/index.html`, `docs/index.html` | `refreshData()` triggers an alert on failure and does not reset the spinner if the fetch throws before `finally`. | Minor UX / possible stuck UI. | Ensure `finally` always removes the spinner; replace `alert()` with inline error message. |

---

## Phase 3 — Medium/Low (Hardening & Cleanup)

| # | Severity | File | Issue | Impact | Fix |
|---|----------|------|-------|--------|-----|
| 13 | **P2** | `app.py` | No `SECRET_KEY`, no CORS, no CSP, no CSRF, no `Content-Type`/`X-Content-Type-Options` headers. | XSS impact amplified; clickjacking possible. | Set `SECRET_KEY`, add CSP, `X-Frame-Options`, `X-Content-Type-Options: nosniff`. |
| 14 | **P2** | `app.py`, `scraper.py` | `fetch_soup`, `full_url`, `save_data`, and scraping logic are duplicated between `app.py` and `scraper.py`. | Bugs fixed in one place persist in the other. | Move shared scraper code into `scraper.py` and import it from `app.py`. |
| 15 | **P2** | `Dockerfile` | `gunicorn --timeout 0` disables request timeout; long scrapes can hang workers indefinitely. | Worker exhaustion / DoS. | Set a sensible timeout (e.g., 60s) and run the scraper outside the request cycle. |
| 16 | **P2** | `requirements.txt` | No `Werkzeug` pin. Flask 3.0.0 requires `Werkzeug>=3.0`; uncontrolled upgrades can break the app. | Build / runtime breakage. | Pin `Werkzeug==3.0.1` and `MarkupSafe>=2.1.3`. |
| 17 | **P2** | `templates/index.html` | `normalizeSearchText()` is defined but never used in the Flask template; the client-side search logic does not normalize Roman numerals. | Search UX misses valid permutations. | Use the normalizer in `performSearch()` / `matchesFilters()` or remove the dead code. |
| 18 | **P2** | `database.py` | `populate_from_json` does `DELETE FROM content` then re-inserts; concurrent searches can return empty results mid-populate. | Transient data loss for readers. | Wrap in a transaction or use `INSERT OR REPLACE`/`UPSERT`. |
| 19 | **P2** | `test_search.py` | Removes the test DB unconditionally; if the test fails, the DB cleanup may leave `test_pdf_cache` behind. | Test pollution. | Use `try/finally` or `tempfile` for cleanup. |
| 20 | **P3** | `app.py` | `from urllib.parse import urlparse` is imported inside two functions instead of the module top. | Minor style / performance. | Move import to module top. |
| 21 | **P3** | `README.md`, `SECURITY.md` | Claims CodeQL scan is clean and SSRF is a "false positive". The current validation is not sufficient for a public deployment. | False confidence. | Update docs to reflect real risk and required mitigations. |
| 22 | **P3** | `.github/workflows/` | Workflow file was excluded from the bundle, so I cannot review the Actions cron job, token permissions, or branch rules. | Potential over-privileged tokens or secret leaks. | Re-bundle including `.github/workflows/*.yml` for review. |

---

## Immediate Action Plan

1. **Apply Phase 1 patches before any public URL or GitHub Pages deploy.**
2. **Run `python test_search.py` and manual XSS/SSRF tests** after patching.
3. **Deploy behind HTTPS** and re-enable TLS verification as soon as the college cert is fixed.
4. **Re-bundle with `.github/workflows/`** so the CI/CD pipeline can be reviewed.

---

## Testing Checklist After Patching

- [ ] Inject `<script>alert(1)</script>` into a mock `data.json` title and confirm it renders as literal text, not JS.
- [ ] Request `/api/pdf/view?url=http://169.254.169.254/latest/meta-data/` and get `403`.
- [ ] Request `/api/pdf/view?url=http://subodhpgcollege.com@evil.com/...` and get `403`.
- [ ] Verify `app.run(debug=False)` is active in production.
- [ ] Hit `/api/search` concurrently with 10+ requests and confirm no `sqlite3` thread errors.
- [ ] Verify `limit=9999999` is capped.
- [ ] Verify FTS5 query `"NOT OR AND --` returns empty results gracefully, not an error.

---

*Report generated by code review. Next step: Phase 1 patches.*
