#!/usr/bin/env python3
import os
import asyncio
import random
import time
import signal
import aiohttp
import logging
import urllib.parse

# ---- Configuration via environment variables ----
MATOMO_URL = os.environ.get("MATOMO_URL", "https://matomo.example.com/matomo.php").rstrip("/")
SITE_ID = int(os.environ.get("MATOMO_SITE_ID", "1"))
URLS_FILE = os.environ.get("URLS_FILE", "/config/urls.txt")

TARGET_VISITS_PER_DAY = float(os.environ.get("TARGET_VISITS_PER_DAY", "20000"))
PAGEVIEWS_MIN = int(os.environ.get("PAGEVIEWS_MIN", "3"))
PAGEVIEWS_MAX = int(os.environ.get("PAGEVIEWS_MAX", "6"))
CONCURRENCY = int(os.environ.get("CONCURRENCY", "50"))
PAUSE_BETWEEN_PVS_MIN = float(os.environ.get("PAUSE_BETWEEN_PVS_MIN", "0.5"))
PAUSE_BETWEEN_PVS_MAX = float(os.environ.get("PAUSE_BETWEEN_PVS_MAX", "2.0"))

# New: auto-stop controls
AUTO_STOP_AFTER_HOURS = float(os.environ.get("AUTO_STOP_AFTER_HOURS", "0"))  # 0 = disabled
MAX_TOTAL_VISITS = int(os.environ.get("MAX_TOTAL_VISITS", "0"))             # 0 = disabled

# Site search configuration
SITESEARCH_PROBABILITY = float(os.environ.get("SITESEARCH_PROBABILITY", "0.15"))  # 15% of visits will have search

# Visit duration configuration (in minutes)
VISIT_DURATION_MIN = float(os.environ.get("VISIT_DURATION_MIN", "1.0"))  # Minimum visit duration
VISIT_DURATION_MAX = float(os.environ.get("VISIT_DURATION_MAX", "8.0"))  # Maximum visit duration

# Outlinks and downloads configuration
OUTLINKS_PROBABILITY = float(os.environ.get("OUTLINKS_PROBABILITY", "0.10"))  # 10% of visits will have outlinks
DOWNLOADS_PROBABILITY = float(os.environ.get("DOWNLOADS_PROBABILITY", "0.08"))  # 8% of visits will have downloads

USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:117.0) Gecko/20100101 Firefox/117.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
]

# Search terms for site search functionality
SEARCH_TERMS = [
    'product', 'service', 'contact', 'about', 'help', 'support', 'pricing', 'features',
    'login', 'register', 'download', 'documentation', 'tutorial', 'guide', 'faq',
    'news', 'blog', 'updates', 'announcement', 'release', 'version', 'security',
    'privacy', 'terms', 'policy', 'legal', 'careers', 'jobs', 'team', 'company',
    'analytics', 'tracking', 'dashboard', 'report', 'statistics', 'metrics', 'data'
]

# Outlinks for external link tracking
OUTLINKS = [
    'https://github.com', 'https://stackoverflow.com', 'https://developer.mozilla.org',
    'https://www.w3.org', 'https://nodejs.org', 'https://reactjs.org', 'https://vuejs.org',
    'https://angular.io', 'https://jquery.com', 'https://bootstrap.getbootstrap.com',
    'https://tailwindcss.com', 'https://fontawesome.com', 'https://unsplash.com',
    'https://fonts.google.com', 'https://codepen.io', 'https://jsfiddle.net',
    'https://wikipedia.org', 'https://youtube.com', 'https://twitter.com',
    'https://linkedin.com', 'https://facebook.com', 'https://instagram.com',
    'https://reddit.com', 'https://medium.com', 'https://dev.to'
]

# Downloads for download tracking
DOWNLOADS = [
    '/downloads/user-manual.pdf', '/downloads/getting-started-guide.pdf',
    '/downloads/api-documentation.pdf', '/downloads/whitepaper.pdf',
    '/downloads/case-study.pdf', '/downloads/technical-specs.pdf',
    '/files/product-brochure.pdf', '/files/pricing-sheet.pdf',
    '/assets/company-presentation.pptx', '/assets/logo-pack.zip',
    '/downloads/software-v2.1.0.zip', '/downloads/mobile-app.apk',
    '/files/dataset.csv', '/files/report-2024.xlsx',
    '/downloads/template.docx', '/downloads/configuration.json',
    '/files/backup.tar.gz', '/downloads/installer.exe',
    '/assets/images.zip', '/downloads/source-code.zip'
]

def read_urls(path):
    urls = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith('#'):
                continue
            urls.append(s.split()[0])
    if not urls:
        raise RuntimeError("No URLs found in URLS_FILE")
    return urls

def rand_hex(n=16):
    import random
    return ''.join(random.choice('0123456789abcdef') for _ in range(n))

# Logging configuration (can be adjusted with environment variable LOG_LEVEL)
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s %(levelname)s %(message)s')


def choose_action_pages(num_pvs: int, want_search: bool, want_outlink: bool, want_download: bool):
    """Choose pageview indices for search/outlink/download actions.

    Guarantees:
    - If num_pvs <= 1 => all actions disabled (-1).
    - Otherwise, any chosen page is in the inclusive range [2, num_pvs].

    This helper is deterministic only in terms of its constraints; it uses
    randomness for selection so callers should treat results as non-deterministic.
    """
    if num_pvs <= 1:
        return -1, -1, -1

    def pick(want: bool):
        return random.randint(2, num_pvs) if want else -1

    return pick(want_search), pick(want_outlink), pick(want_download)

async def send_hit(session, params, headers):
    try:
        async with session.get(MATOMO_URL, params=params, headers=headers) as resp:
            await resp.read()
            return resp.status
    except Exception:
        return None

async def visit(session, urls):
    # One "visit" with 3–6 pageviews (configurable)
    num_pvs = random.randint(PAGEVIEWS_MIN, PAGEVIEWS_MAX)
    vid = rand_hex(16)  # visitor id
    ua = random.choice(USER_AGENTS)
    ref = random.choice(urls)
    
    # Determine if this visit will include site search, outlinks, or downloads
    has_search = random.random() < SITESEARCH_PROBABILITY
    has_outlink = random.random() < OUTLINKS_PROBABILITY
    has_download = random.random() < DOWNLOADS_PROBABILITY

    # Ensure search/outlink/download are NEVER the first pageview.
    # If there's only one pageview in the visit, disable these actions.
    if num_pvs <= 1:
        search_pageview = -1
        outlink_pageview = -1
        download_pageview = -1
    else:
        # Pick a pageview in the range 2..num_pvs (so not the first PV)
        search_pageview = random.randint(2, num_pvs) if has_search else -1
        outlink_pageview = random.randint(2, num_pvs) if has_outlink else -1
        download_pageview = random.randint(2, num_pvs) if has_download else -1

    for i in range(num_pvs):
        url = random.choice(urls)
        # Keep the original page URL (the page that contains any outlink/download)
        page_url = url

        params = {
            'idsite': SITE_ID,
            'rec': 1,
            'url': page_url,
            'action_name': f'LoadTest PV {i+1}/{num_pvs}',
            '_id': vid,
            'rand': random.randint(0, 2**31-1),
        }

        # If this is not the first pageview, include referrer as the previous page
        # so Matomo can attribute outlinks/downloads correctly.
        if i == 0:
            params['new_visit'] = 1
            params['urlref'] = ref
        else:
            params['urlref'] = last_page_url

        # Add site search parameters if this is the search pageview
        if i + 1 == search_pageview:
            search_keyword = random.choice(SEARCH_TERMS)
            search_category = random.choice(['', 'Products', 'Support', 'Documentation']) if random.random() < 0.3 else ''
            search_count = random.randint(0, 25)  # Number of search results
            
            params['search'] = search_keyword
            if search_category:
                params['search_cat'] = search_category
            params['search_count'] = search_count
            params['action_name'] = f'Search: {search_keyword}'
        
        # Add outlink tracking if this is the outlink pageview
        elif i + 1 == outlink_pageview:
            outlink_url = random.choice(OUTLINKS)
            # urlref must point to the page that contained the link
            params['urlref'] = page_url
            params['link'] = outlink_url
            params['url'] = outlink_url  # Matomo recommendation: url contains the clicked href
            params['action_name'] = f'Outlink: {outlink_url}'
        
        # Add download tracking if this is the download pageview
        elif i + 1 == download_pageview:
            download_file = random.choice(DOWNLOADS)
            # If DOWNLOADS items are paths, convert to a full URL using the current page as base
            if download_file.startswith('http://') or download_file.startswith('https://'):
                download_url = download_file
            else:
                parsed = urllib.parse.urlparse(page_url)
                base_url = f"{parsed.scheme}://{parsed.netloc}"
                download_url = urllib.parse.urljoin(base_url, download_file)

            # urlref must point to the page that contained the download link
            params['urlref'] = page_url
            params['download'] = download_url
            params['url'] = download_url  # Matomo recommendation: url contains the download path/URL
            params['action_name'] = f'Download: {download_url.split("/")[-1]}'
        
    # Update last_page_url so the next pageview can use it as urlref
    # For outlink/download we keep last_page_url as the original page containing the link
    # so subsequent pageviews still show a sensible referrer.
    # (last_page_url is used at the top of the loop for non-first PVs)

        headers = {'User-Agent': ua}

        # Build a debug-friendly request string for logging
        try:
            request_qs = urllib.parse.urlencode(params)
        except Exception:
            request_qs = str(params)
        request_url = f"{MATOMO_URL}?{request_qs}"

        # Log only the outlink/download hits at INFO level to avoid noise
        if 'download' in params:
            logging.info('Sending download hit: visitor=%s file=%s referer=%s', vid, params.get('download'), params.get('urlref'))
            logging.debug('Matomo request: %s', request_url)
        elif 'link' in params:
            logging.info('Sending outlink hit: visitor=%s link=%s referer=%s', vid, params.get('link'), params.get('urlref'))
            logging.debug('Matomo request: %s', request_url)
        else:
            logging.debug('Sending pageview: visitor=%s action=%s', vid, params.get('action_name'))

        await send_hit(session, params, headers)
        # set last_page_url for next iteration
        if i + 1 == outlink_pageview or i + 1 == download_pageview:
            # user clicked away; keep last_page_url as the page that contained the link
            last_page_url = page_url
        else:
            last_page_url = page_url
        if i < num_pvs - 1:
            await asyncio.sleep(random.uniform(PAUSE_BETWEEN_PVS_MIN, PAUSE_BETWEEN_PVS_MAX))
    
    # Add extended visit duration - simulate user staying on site after last pageview
    visit_duration_seconds = random.uniform(VISIT_DURATION_MIN * 60, VISIT_DURATION_MAX * 60)
    # Subtract time already spent on pageviews
    time_spent_on_pageviews = (num_pvs - 1) * ((PAUSE_BETWEEN_PVS_MIN + PAUSE_BETWEEN_PVS_MAX) / 2)
    remaining_time = max(0, visit_duration_seconds - time_spent_on_pageviews)
    
    if remaining_time > 0:
        await asyncio.sleep(remaining_time)

class GracefulExit(SystemExit):
    pass

def _handle_sig(*_):
    raise GracefulExit()

async def main():
    urls = read_urls(URLS_FILE)

    # Target rate in visits/sec
    visits_per_sec = TARGET_VISITS_PER_DAY / 86400.0
    # Simple token-bucket scheduler to smooth traffic
    tokens = 0.0
    last = time.time()

    connector = aiohttp.TCPConnector(limit=CONCURRENCY, ssl=False)
    timeout = aiohttp.ClientTimeout(total=None)
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        q = asyncio.Queue(maxsize=CONCURRENCY * 2)

        # Auto-stop timers/limits
        start_ts = time.time()
        visits_total = 0
        # Per-24h counter for MAX_TOTAL_VISITS
        visits_today = 0
        day_window_start = start_ts

        async def producer():
            nonlocal tokens, last
            while True:
                # Check auto-stop by time
                if AUTO_STOP_AFTER_HOURS > 0 and (time.time() - start_ts) >= AUTO_STOP_AFTER_HOURS * 3600:
                    await q.put(None)  # sentinel to tell workers to quit
                    await asyncio.sleep(0.1)
                    break

                # Refill tokens
                now = time.time()
                dt = now - last
                last = now
                tokens += visits_per_sec * dt
                if tokens > CONCURRENCY:
                    tokens = CONCURRENCY

                produced = 0
                # If a daily cap is configured, pause producing when reached until 24h window resets
                if MAX_TOTAL_VISITS > 0 and visits_today >= MAX_TOTAL_VISITS:
                    # if the day window has passed, reset the counter
                    if now - day_window_start >= 86400:
                        day_window_start = now
                        visits_today = 0
                    else:
                        # Wait a short while then continue (no new jobs produced until window resets)
                        await asyncio.sleep(1)
                        await asyncio.sleep(0.25)
                        continue

                while tokens >= 1 and not q.full():
                    await q.put(1)
                    tokens -= 1
                    produced += 1

                await asyncio.sleep(0.25)

        async def worker():
            nonlocal visits_total
            while True:
                job = await q.get()
                if job is None:
                    q.task_done()
                    break
                try:
                    await visit(session, urls)
                except Exception:
                    pass
                finally:
                    visits_total += 1
                    q.task_done()

        workers = [asyncio.create_task(worker()) for _ in range(CONCURRENCY)]
        prod = asyncio.create_task(producer())

        last_log = time.time()
        try:
            while True:
                await asyncio.sleep(10)
                # Exit conditions
                if AUTO_STOP_AFTER_HOURS > 0 and (time.time() - start_ts) >= AUTO_STOP_AFTER_HOURS * 3600:
                    break
                if MAX_TOTAL_VISITS > 0 and visits_total >= MAX_TOTAL_VISITS:
                    break

                now = time.time()
                if now - last_log >= 60:
                    # estimate: visits in the last minute -> multiply to daily rate
                    print(f"[loadgen] visits_total={visits_total}")
                    last_log = now
        except GracefulExit:
            print("[loadgen] Shutting down...")
        finally:
            prod.cancel()
            for w in workers:
                w.cancel()
            await asyncio.gather(*workers, return_exceptions=True)
            await asyncio.gather(prod, return_exceptions=True)

    # Print final summary
    elapsed = time.time() - start_ts
    rate = visits_total / elapsed if elapsed > 0 else 0.0
    print(f"[loadgen] Done. Sent {visits_total} visits in {elapsed:.1f}s (~{rate*86400:.0f}/day).")

if __name__ == "__main__":
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, _handle_sig)
    asyncio.run(main())
