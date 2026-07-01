"""Turn any URL into a PDF and drop it into the project's pdfs/ folder.

Single page:
    python scripts/url_to_pdf.py https://example.com
    python scripts/url_to_pdf.py https://example.com -o my_page.pdf

Whole site (follow all same-domain links):
    python scripts/url_to_pdf.py https://example.com --crawl
    python scripts/url_to_pdf.py https://example.com --crawl --max-pages 200 --max-depth 4

Requires Playwright + a Chromium build:
    pip install playwright
    playwright install chromium
"""
import argparse
import os
import re
import sys
from collections import deque
from datetime import datetime
from urllib.parse import urlparse, urldefrag

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_OUTDIR = os.path.join(PROJECT_ROOT, "pdfs")

SKIP_EXTENSIONS = (
    ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".ico",
    ".zip", ".gz", ".tar", ".mp4", ".mp3", ".mov", ".avi", ".css", ".js",
    ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".woff", ".woff2",
)


def slugify_url(url: str, with_timestamp: bool = True) -> str:
    """Build a filesystem-safe base filename from a URL."""
    parsed = urlparse(url)
    raw = f"{parsed.netloc}{parsed.path}".strip("/") or "page"
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", raw).strip("_")
    slug = slug[:80] or "page"
    if with_timestamp:
        slug = f"{slug}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    return slug


def unique_path(outdir: str, filename: str) -> str:
    """Avoid clobbering an existing file by appending a counter."""
    base, ext = os.path.splitext(filename)
    candidate = os.path.join(outdir, filename)
    counter = 1
    while os.path.exists(candidate):
        candidate = os.path.join(outdir, f"{base}_{counter}{ext}")
        counter += 1
    return candidate


def normalize_url(url: str) -> str:
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", url):
        return "https://" + url
    return url


def canonical(url: str) -> str:
    """Drop the fragment so #anchors don't create duplicate pages."""
    return urldefrag(url)[0].rstrip("/")


def same_site(url: str, root_netloc: str) -> bool:
    netloc = urlparse(url).netloc.lower()
    return netloc.replace("www.", "") == root_netloc.replace("www.", "")


def is_crawlable(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False
    return not parsed.path.lower().endswith(SKIP_EXTENSIONS)


def render_page(page, url: str, output: str, timeout_ms: int):
    """Render a URL to a PDF and return the list of anchor hrefs on the page."""
    page.goto(url, wait_until="load", timeout=timeout_ms)
    # Best-effort settle: many sites never go fully idle (analytics, chat widgets).
    try:
        page.wait_for_load_state("networkidle", timeout=8000)
    except Exception:  # noqa: BLE001 - idle is optional, keep going
        pass
    page.wait_for_timeout(1500)
    hrefs = page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
    page.emulate_media(media="print")
    page.pdf(
        path=output,
        format="A4",
        print_background=True,
        margin={"top": "15mm", "bottom": "15mm", "left": "12mm", "right": "12mm"},
    )
    return hrefs or []


def get_browser_page():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit(
            "Playwright is not installed. Run:\n"
            "    pip install playwright\n"
            "    playwright install chromium"
        )
    from playwright.sync_api import Error as PlaywrightError

    pw = sync_playwright().start()
    try:
        browser = pw.chromium.launch()
    except PlaywrightError as exc:
        pw.stop()
        sys.exit(
            f"Could not launch Chromium ({exc}).\n"
            "Install the browser with:\n    playwright install chromium"
        )
    page = browser.new_page()
    return pw, browser, page


def convert_single(url: str, output: str, timeout_ms: int) -> None:
    pw, browser, page = get_browser_page()
    try:
        print(f"Rendering {url} ...")
        render_page(page, url, output, timeout_ms)
        print(f"Saved: {output}")
    finally:
        browser.close()
        pw.stop()


def crawl_site(start_url: str, outdir: str, timeout_ms: int, max_pages: int, max_depth: int) -> None:
    root_netloc = urlparse(start_url).netloc
    unlimited = max_pages <= 0
    cap_label = "\u221e" if unlimited else str(max_pages)
    pw, browser, page = get_browser_page()
    visited = set()
    queue = deque([(canonical(start_url), 0)])
    saved = 0
    try:
        while queue and (unlimited or saved < max_pages):
            url, depth = queue.popleft()
            if url in visited:
                continue
            visited.add(url)
            try:
                output = unique_path(outdir, f"{slugify_url(url, with_timestamp=False)}.pdf")
                print(f"[{saved + 1}/{cap_label}] depth {depth}: {url}")
                hrefs = render_page(page, url, output, timeout_ms)
                saved += 1
                print(f"    saved: {os.path.basename(output)}")
            except Exception as exc:  # noqa: BLE001 - keep crawling past a bad page
                print(f"    skipped ({exc})")
                continue

            if max_depth and depth >= max_depth:
                continue
            for href in hrefs:
                nxt = canonical(normalize_url(href))
                if nxt in visited or not is_crawlable(nxt) or not same_site(nxt, root_netloc):
                    continue
                queue.append((nxt, depth + 1))
    finally:
        browser.close()
        pw.stop()
    print(f"\nDone. Saved {saved} page(s) to {outdir}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert URL(s) to PDF into the pdfs/ folder.")
    parser.add_argument("urls", nargs="+", help="One or more URLs to convert.")
    parser.add_argument("-o", "--output", help="Output filename (single URL, non-crawl only).")
    parser.add_argument("--outdir", default=DEFAULT_OUTDIR, help="Output directory (default: pdfs/).")
    parser.add_argument("--timeout", type=int, default=60000, help="Page load timeout in ms (default: 60000).")
    parser.add_argument("--crawl", action="store_true", help="Follow same-domain links and save the whole site.")
    parser.add_argument("--max-pages", type=int, default=0, help="Max pages to save when crawling (0 = unlimited, default: 0).")
    parser.add_argument("--max-depth", type=int, default=0, help="Max link depth when crawling (0 = unlimited, default: 0).")
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    if args.crawl:
        if args.output:
            parser.error("--output cannot be used with --crawl (filenames are derived per page).")
        for url in args.urls:
            crawl_site(normalize_url(url), args.outdir, args.timeout, args.max_pages, args.max_depth)
        return

    if args.output and len(args.urls) > 1:
        parser.error("--output can only be used with a single URL.")

    for url in args.urls:
        url = normalize_url(url)
        filename = args.output or f"{slugify_url(url)}.pdf"
        if not filename.lower().endswith(".pdf"):
            filename += ".pdf"
        output = unique_path(args.outdir, filename)
        convert_single(url, output, args.timeout)


if __name__ == "__main__":
    main()
