"""
PDF Handler Module for Fast PDF Viewing
Uses pikepdf for PDF optimization and fast loading
"""

import os
import io
import hashlib
import ipaddress
import requests
from typing import Optional, Dict, Any
from pathlib import Path
from urllib.parse import urlparse


try:
    import pikepdf
    PIKEPDF_AVAILABLE = True
except ImportError:
    PIKEPDF_AVAILABLE = False
    print("Warning: pikepdf not installed. PDF optimization disabled.")


ALLOWED_DOMAINS = {'subodhpgcollege.com', 'www.subodhpgcollege.com'}


def _is_safe_url(url: str) -> bool:
    """
    Defense-in-depth URL validation. Must be called before any server-side HTTP request.
    - HTTP/HTTPS only.
    - No auth fragments.
    - Host must be in the allowed whitelist.
    - Host must not be a private/link-local/reserved IP literal.
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

    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            return False
    except ValueError:
        pass

    return True


class PDFHandler:
    """Handler for PDF optimization and caching"""

    def __init__(self, cache_dir: str = "pdf_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def get_cache_path(self, url: str) -> Path:
        """Generate cache file path from URL hash"""
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return self.cache_dir / f"{url_hash}.pdf"

    def download_pdf(self, url: str) -> Optional[bytes]:
        """
        Download PDF from URL.

        SECURITY NOTE: SSL verification is disabled (verify=False) because the target
        college website has known SSL certificate issues. This is only used for
        read-only downloading of public PDFs from whitelisted domains.
        """
        if not _is_safe_url(url):
            print(f"Blocked unsafe PDF URL: {url}")
            return None

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30, verify=False)
            response.raise_for_status()
            return response.content
        except Exception as e:
            print(f"Error downloading PDF from {url}: {e}")
            return None

    def optimize_pdf(self, pdf_bytes: bytes) -> Optional[bytes]:
        """
        Optimize PDF for faster loading using pikepdf
        - Linearize for fast web viewing
        - Compress streams
        """
        if not PIKEPDF_AVAILABLE:
            return pdf_bytes

        try:
            pdf_input = io.BytesIO(pdf_bytes)
            pdf = pikepdf.open(pdf_input)

            output = io.BytesIO()
            pdf.save(
                output,
                linearize=True,
                compress_streams=True,
                stream_decode_level=pikepdf.StreamDecodeLevel.generalized
            )

            pdf.close()
            optimized_bytes = output.getvalue()
            output.close()
            return optimized_bytes

        except Exception as e:
            print(f"Error optimizing PDF: {e}")
            return pdf_bytes

    def get_pdf(self, url: str, optimize: bool = True) -> Optional[bytes]:
        """Get PDF either from cache or download and optimize"""
        cache_path = self.get_cache_path(url)

        if cache_path.exists():
            try:
                with open(cache_path, 'rb') as f:
                    return f.read()
            except Exception as e:
                print(f"Error reading cached PDF: {e}")

        pdf_bytes = self.download_pdf(url)
        if not pdf_bytes:
            return None

        if optimize and PIKEPDF_AVAILABLE:
            pdf_bytes = self.optimize_pdf(pdf_bytes)

        try:
            with open(cache_path, 'wb') as f:
                f.write(pdf_bytes)
        except Exception as e:
            print(f"Error caching PDF: {e}")

        return pdf_bytes

    def get_pdf_info(self, url: str) -> Optional[Dict[str, Any]]:
        """Get PDF metadata information"""
        if not PIKEPDF_AVAILABLE:
            return None

        try:
            pdf_bytes = self.get_pdf(url, optimize=False)
            if not pdf_bytes:
                return None

            pdf_input = io.BytesIO(pdf_bytes)
            pdf = pikepdf.open(pdf_input)

            info = {
                'pages': len(pdf.pages),
                'linearized': pdf.is_linearized,
                'encrypted': pdf.is_encrypted,
            }

            if pdf.docinfo:
                try:
                    info['title'] = str(pdf.docinfo.get('/Title', ''))
                    info['author'] = str(pdf.docinfo.get('/Author', ''))
                    info['subject'] = str(pdf.docinfo.get('/Subject', ''))
                except Exception:
                    pass

            pdf.close()
            return info

        except Exception as e:
            print(f"Error getting PDF info: {e}")
            return None

    def clear_cache(self):
        """Clear all cached PDFs"""
        for file in self.cache_dir.glob("*.pdf"):
            try:
                file.unlink()
            except Exception as e:
                print(f"Error deleting cache file {file}: {e}")


# Singleton instance
_pdf_handler = None


def get_pdf_handler() -> PDFHandler:
    """Get PDF handler singleton instance"""
    global _pdf_handler
    if _pdf_handler is None:
        _pdf_handler = PDFHandler()
    return _pdf_handler
