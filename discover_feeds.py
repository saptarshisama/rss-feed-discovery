#!/usr/bin/env python3
"""
discover_feeds.py

Simplified runner: no animated progress bar. As each site finishes, main thread
prints a numbered line:

1) Done: https://example.com -> best: https://example.com/feed

- Supports CSV or JSON input (positional or -i).
- Writes JSON output (default: feeds_verified.json).
- Ctrl+C stops submission of new work, waits briefly for running tasks, saves partial results.
- All terminal printing happens from the main thread.
"""

from __future__ import annotations
import argparse
import csv
import json
import time
import signal
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from typing import List, Dict, Optional
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup
import feedparser
import threading

# Color output (green)
try:
    from colorama import init as colorama_init, Fore, Style
    colorama_init()
    GREEN = Fore.GREEN
    RESET = Style.RESET_ALL
except Exception:
    GREEN = ""
    RESET = ""

# Module defaults
HEADERS = {"User-Agent": "discover-feeds-bot/1.0 (+https://example.com)"}
REQUEST_TIMEOUT = 10
SLEEP_BETWEEN_REQUESTS = 0.12
MAX_WORKERS = 8

COMMON_FEED_PATHS = [
    "/feed", "/feed/", "/rss", "/rss.xml", "/atom.xml",
    "/index.xml", "/index.rdf", "/feeds/posts/default",
    "/?format=rss", "/?format=xml", "/?feed=rss",
    "/blog/feed", "/blog/rss", "/rss.php",
]

# Simple stop flag for Ctrl+C
_stop = threading.Event()

def _sigint(sig, frame):
    _stop.set()
    try:
        sys.stdout.write(GREEN + "\nInterrupt received — will stop submitting new work and save partial results.\n" + RESET)
        sys.stdout.flush()
    except Exception:
        pass

signal.signal(signal.SIGINT, _sigint)

# thread-local session for connection pooling
thread_local = threading.local()

def get_session() -> requests.Session:
    if not getattr(thread_local, "session", None):
        s = requests.Session()
        s.headers.update(HEADERS)
        thread_local.session = s
    return thread_local.session

def norm_domain_to_url(domain: str) -> Optional[str]:
    if not domain:
        return None
    domain = domain.strip()
    if domain.startswith("//"):
        domain = "https:" + domain
    parsed = urlparse(domain, scheme="https")
    scheme = parsed.scheme or "https"
    netloc = parsed.netloc or parsed.path
    if not netloc:
        return None
    return f"{scheme}://{netloc.rstrip('/')}"

def build_guesses(base_url: str) -> List[str]:
    parsed = urlparse(base_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    guesses = [origin + p for p in COMMON_FEED_PATHS] + [origin + "/feed.xml"]
    seen = set(); out = []
    for g in guesses:
        if g not in seen:
            out.append(g); seen.add(g)
    return out

def fetch_url(url: str) -> Dict:
    """Fetch URL using a thread-local session. Returns {'response': r} or {'error': str}."""
    if _stop.is_set():
        return {"error": "stopped"}
    session = get_session()
    try:
        r = session.get(url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        # polite tiny delay
        time.sleep(SLEEP_BETWEEN_REQUESTS)
        return {"response": r}
    except Exception as e:
        return {"error": str(e)}

def discover_from_homepage(site_url: str) -> List[str]:
    candidates: List[str] = []
    fetch = fetch_url(site_url)
    if "error" in fetch:
        return []
    r = fetch["response"]
    try:
        text = r.text
    except Exception:
        try:
            text = r.content.decode("utf-8", errors="ignore")
        except Exception:
            text = ""
    soup = BeautifulSoup(text, "html.parser")

    for link in soup.find_all("link", href=True):
        ltype = (link.get("type") or "").lower()
        rel = " ".join(link.get("rel") or [])
        href = link.get("href")
        if not href:
            continue
        if "rss" in ltype or "atom" in ltype or "xml" in ltype or "alternate" in rel:
            candidates.append(urljoin(site_url, href))

    for a in soup.find_all("a", href=True):
        href = a.get("href")
        if not href:
            continue
        lower = href.lower()
        if any(k in lower for k in ("rss", "feed", "atom", "xml")):
            candidates.append(urljoin(site_url, href))

    seen = set(); out = []
    for c in candidates:
        c_clean = c.split("#")[0].rstrip("/")
        if c_clean not in seen:
            seen.add(c_clean); out.append(c_clean)
    return out

def looks_like_feed_by_content(text: str) -> bool:
    if not text: return False
    t = text.lower()
    return ("<rss" in t) or ("<feed" in t) or ("<rdf:rdf" in t) or ("<rss:" in t)

def test_candidate(url: str) -> Dict:
    result = {"url": url, "final_url": None, "http_status": None, "content_type": None,
              "is_feed": False, "entries": 0, "error": None}
    if _stop.is_set():
        result["error"] = "stopped"; return result
    fetch = fetch_url(url)
    if "error" in fetch:
        result["error"] = fetch["error"]; return result
    r = fetch["response"]
    result["final_url"] = r.url
    result["http_status"] = r.status_code
    result["content_type"] = r.headers.get("Content-Type")
    body_bytes = r.content or b""
    ct = (result["content_type"] or "").lower()
    is_feed = False
    if any(x in ct for x in ("xml", "rss", "atom")):
        is_feed = True
    else:
        try:
            snippet = body_bytes[:2048].decode("utf-8", errors="ignore")
            if looks_like_feed_by_content(snippet):
                is_feed = True
        except Exception:
            pass
    result["is_feed"] = is_feed
    if is_feed:
        try:
            parsed = feedparser.parse(body_bytes)
            result["entries"] = len(getattr(parsed, "entries", []))
        except Exception as e:
            result["error"] = f"feedparser error: {e}"
    return result

def discover_for_site(domain_input: str) -> Dict:
    base_url = norm_domain_to_url(domain_input)
    out = {"name": domain_input, "site": base_url, "candidates": [], "best": None}
    if not base_url:
        out["candidates"].append({"url": None, "error": "invalid input"}); return out

    homepage_candidates = discover_from_homepage(base_url + "/")
    guessed = build_guesses(base_url)
    candidates = []
    for c in (homepage_candidates + guessed):
        if _stop.is_set(): break
        if not c: continue
        if c.startswith("//"): c = "https:" + c
        candidates.append(c.split("#")[0].rstrip("/"))

    seen = set(); unique_candidates = []
    for c in candidates:
        if c not in seen:
            unique_candidates.append(c); seen.add(c)

    results = []; best = None
    for c in unique_candidates:
        if _stop.is_set(): break
        info = test_candidate(c); results.append(info)
        if info.get("is_feed") and info.get("entries", 0) > 0 and not best:
            best = info.get("final_url") or info.get("url")

    if not best and not _stop.is_set():
        fallback = base_url + "/feed.xml"
        info = test_candidate(fallback); results.append(info)
        if info.get("is_feed") and info.get("entries", 0) > 0:
            best = info.get("final_url") or info.get("url")

    out["candidates"] = results; out["best"] = best
    return out

# ---------------------
# Input helpers
# ---------------------
def read_domains_from_csv(path: str) -> List[str]:
    vals: List[str] = []
    with open(path, newline="", encoding="utf-8") as fh:
        sniffer = csv.Sniffer()
        sample = fh.read(2048); fh.seek(0)
        has_header = False
        try:
            has_header = sniffer.has_header(sample)
        except Exception:
            has_header = False
        reader = csv.reader(fh)
        if has_header:
            headers = next(reader, [])
            idx = None
            for i, h in enumerate(headers):
                if h and h.strip().lower() in ("domain", "url", "site", "website"):
                    idx = i; break
            if idx is None: idx = 0
            for row in reader:
                if len(row) > idx:
                    v = row[idx].strip()
                    if v: vals.append(v)
        else:
            # first row is data already read by next(reader) above, so we iterate all rows
            fh.seek(0)
            reader = csv.reader(fh)
            for row in reader:
                if row and row[0].strip():
                    vals.append(row[0].strip())
    return vals

def read_domains_from_json(path: str) -> List[str]:
    vals: List[str] = []
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, list):
        for item in data:
            if isinstance(item, str): vals.append(item.strip())
            elif isinstance(item, dict):
                for k in ("url", "domain", "site"):
                    if k in item and isinstance(item[k], str):
                        vals.append(item[k].strip()); break
    elif isinstance(data, dict):
        list_keys = ("websites", "sites", "domains")
        found = False
        for key in list_keys:
            if key in data and isinstance(data[key], list):
                found = True
                for item in data[key]:
                    if isinstance(item, str): vals.append(item.strip())
                    elif isinstance(item, dict):
                        for k in ("url", "domain", "site"):
                            if k in item and isinstance(item[k], str):
                                vals.append(item[k].strip()); break
                break
        if not found:
            for v in data.values():
                if isinstance(v, str): vals.append(v.strip())
    return vals

# ---------------------
# Main runner - prints numbered lines as tasks complete
# ---------------------
def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Discover RSS/Atom feeds from CSV or JSON")
    p.add_argument("input_path", nargs="?", help="Positional input file (CSV or JSON)")
    p.add_argument("-i", "--input", dest="input_flag", help="Input CSV or JSON file")
    p.add_argument("-o", "--output", default="feeds_verified.json", help="Output JSON file")
    p.add_argument("-w", "--workers", type=int, default=MAX_WORKERS, help="Number of worker threads")
    p.add_argument("--timeout", type=int, default=REQUEST_TIMEOUT, help="Request timeout seconds")
    p.add_argument("--delay", type=float, default=SLEEP_BETWEEN_REQUESTS, help="Politeness delay between requests (s)")
    args = p.parse_args(argv)

    input_file = args.input_path or args.input_flag
    if not input_file:
        print(GREEN + "Error: no input file provided (positional or -i/--input)." + RESET)
        return 2

    # safe runtime overrides
    globals()["REQUEST_TIMEOUT"] = args.timeout
    globals()["SLEEP_BETWEEN_REQUESTS"] = args.delay

    # read domains
    try:
        if input_file.lower().endswith(".csv"):
            domains = read_domains_from_csv(input_file)
        elif input_file.lower().endswith(".json"):
            domains = read_domains_from_json(input_file)
        else:
            # try csv then json
            try:
                domains = read_domains_from_csv(input_file)
                if not domains:
                    domains = read_domains_from_json(input_file)
            except Exception:
                domains = read_domains_from_json(input_file)
    except Exception as e:
        print(GREEN + f"Failed to read input file {input_file}: {e}" + RESET)
        return 3

    if not domains:
        print(GREEN + f"No domains found in {input_file}" + RESET)
        return 1

    total = len(domains)
    results: List[Dict] = []
    counter = 0

    print(GREEN + f"Starting discovery for {total} sites with {args.workers} workers..." + RESET)

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures_map: Dict[Future, str] = {ex.submit(discover_for_site, d): d for d in domains}

        try:
            for fut in as_completed(futures_map):
                # if interrupted, cancel pending futures
                if _stop.is_set():
                    for f in futures_map:
                        if not f.done():
                            f.cancel()
                    break

                domain = futures_map[fut]
                try:
                    res = fut.result()
                except Exception as e:
                    res = {"name": domain, "site": domain, "candidates": [], "best": None, "error": str(e)}
                results.append(res)
                counter += 1
                site_display = res.get("site") or res.get("name") or domain
                best = res.get("best") or "None"
                # Print numbered line (main thread only)
                print(GREEN + f"{counter}) Done: {site_display} -> best: {best}" + RESET)

        except KeyboardInterrupt:
            _stop.set()
            # Cancel pending futures
            for f in futures_map:
                if not f.done():
                    f.cancel()
        finally:
            # ThreadPoolExecutor context manager will wait for running futures to finish.
            pass

    # Save results (partial or full)
    try:
        with open(args.output, "w", encoding="utf-8") as fh:
            json.dump({"results": results}, fh, indent=2, ensure_ascii=False)
        print(GREEN + f"\nWrote {len(results)} entries to {args.output}" + RESET)
    except Exception as e:
        print(GREEN + f"Failed to write output file {args.output}: {e}" + RESET)
        return 4

    if _stop.is_set():
        print(GREEN + "Stopped by user (partial results saved)." + RESET)
    else:
        print(GREEN + "Done." + RESET)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
