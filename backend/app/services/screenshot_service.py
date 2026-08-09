import os
import re
import time
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

SCREENSHOTS_DIR = Path(__file__).parent.parent.parent / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)

class WebsiteUnreachableError(Exception):
    """Raised when the website cannot be reached or times out."""
    pass

class InvalidURLError(Exception):
    """Raised when the URL is malformed."""
    pass

def _sanitize_domain(url: str) -> str:
    """Extract and sanitize domain name for file saving."""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc if parsed.netloc else parsed.path.split('/')[0]
        # Remove any non-alphanumeric chars for safe filesystem
        safe_domain = re.sub(r'[^a-zA-Z0-9\.\-]', '_', domain)
        return safe_domain
    except Exception:
        return "unknown_domain"

async def capture_screenshot(url: str, full_page: bool = True) -> str:
    """
    Captures a screenshot of the given URL.
    Returns the absolute path to the saved screenshot.
    """
    if not url or not isinstance(url, str):
        raise InvalidURLError("URL must be a non-empty string.")
        
    if not url.startswith('http'):
        url = 'http://' + url

    safe_domain = _sanitize_domain(url)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    file_name = f"{safe_domain}_{timestamp}.png"
    file_path = SCREENSHOTS_DIR / file_name

    async with async_playwright() as p:
        browser = None
        try:
            # Launch chromium headless
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            # Set a 15-second timeout for navigation and waiting
            try:
                # networkidle is preferred, but we use a short timeout so we don't hang
                await page.goto(url, wait_until="networkidle", timeout=15000)
            except Exception as e:
                # If networkidle times out, but the page loaded something, we can still try to capture.
                # However, if it's a DNS error or connection refused, we catch it here.
                err_str = str(e).lower()
                if "net::err" in err_str or "dns" in err_str or "unreachable" in err_str:
                    raise WebsiteUnreachableError(f"Could not reach {url}: {str(e)}")
                # If it's just a timeout, we proceed to try taking a screenshot anyway.

            # Take screenshot
            await page.screenshot(path=str(file_path), full_page=full_page)
            return str(file_path)

        except WebsiteUnreachableError:
            raise
        except Exception as e:
            if "net::err" in str(e).lower() or "unreachable" in str(e).lower():
                raise WebsiteUnreachableError(f"Could not reach {url}: {str(e)}")
            raise WebsiteUnreachableError(f"Failed to capture screenshot for {url}: {str(e)}")
        finally:
            if browser:
                await browser.close()

async def capture_full_page(url: str) -> str:
    """Thin wrapper around capture_screenshot for full page."""
    return await capture_screenshot(url, full_page=True)

def delete_old_images(max_age_hours: int = 24) -> int:
    """
    Deletes screenshots older than max_age_hours.
    Returns the number of deleted files.
    """
    deleted_count = 0
    now = time.time()
    max_age_seconds = max_age_hours * 3600

    for file_path in SCREENSHOTS_DIR.glob("*.png"):
        if file_path.is_file():
            file_age = now - file_path.stat().st_mtime
            if file_age > max_age_seconds:
                try:
                    file_path.unlink()
                    deleted_count += 1
                except Exception as e:
                    print(f"Failed to delete {file_path}: {e}")

    return deleted_count
