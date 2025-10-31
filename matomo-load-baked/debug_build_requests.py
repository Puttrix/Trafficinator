#!/usr/bin/env python3
"""Debug helper: construct and print Matomo request URLs for outlinks and downloads.

This script reuses configuration from loader.py and simulates a few visits, but does
not perform network requests. It's useful to verify the parameters and URLs that
would be sent to Matomo.
"""
import random
import urllib.parse
import os

# Read configuration from environment with sensible defaults to avoid importing loader.py
MATOMO_URL = os.environ.get("MATOMO_URL", "https://matomo.example.com/matomo.php").rstrip("/")
SITE_ID = int(os.environ.get("MATOMO_SITE_ID", "1"))
PAGEVIEWS_MIN = int(os.environ.get("PAGEVIEWS_MIN", "3"))
PAGEVIEWS_MAX = int(os.environ.get("PAGEVIEWS_MAX", "6"))
SITESEARCH_PROBABILITY = float(os.environ.get("SITESEARCH_PROBABILITY", "0.15"))
OUTLINKS_PROBABILITY = float(os.environ.get("OUTLINKS_PROBABILITY", "0.10"))
DOWNLOADS_PROBABILITY = float(os.environ.get("DOWNLOADS_PROBABILITY", "0.08"))

# Minimal user agents list (matches loader.py defaults)
USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:117.0) Gecko/20100101 Firefox/117.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
]

# Outlinks and downloads defaults (trimmed for brevity)
OUTLINKS = [
    'https://github.com', 'https://stackoverflow.com', 'https://developer.mozilla.org',
    'https://www.w3.org', 'https://nodejs.org', 'https://reactjs.org',
]

DOWNLOADS = [
    '/downloads/user-manual.pdf', '/downloads/getting-started-guide.pdf',
    '/files/product-brochure.pdf', '/downloads/software-v2.1.0.zip',
    '/assets/logo-pack.zip'
]


def build_request(params: dict) -> str:
    try:
        qs = urllib.parse.urlencode(params)
    except Exception:
        qs = str(params)
    return f"{MATOMO_URL}?{qs}"


def simulate_visit(urls, force_outlink=False, force_download=False):
    num_pvs = random.randint(PAGEVIEWS_MIN, PAGEVIEWS_MAX)
    vid = ''.join(random.choice('0123456789abcdef') for _ in range(16))
    ua = random.choice(USER_AGENTS)
    ref = random.choice(urls)

    # Force inclusion when requested
    has_outlink = force_outlink or (random.random() < OUTLINKS_PROBABILITY)
    has_download = force_download or (random.random() < DOWNLOADS_PROBABILITY)

    outlink_pageview = random.randint(1, num_pvs) if has_outlink else -1
    download_pageview = random.randint(1, num_pvs) if has_download else -1

    results = []
    for i in range(num_pvs):
        url = random.choice(urls)
        params = {
            'idsite': SITE_ID,
            'rec': 1,
            'url': url,
            'action_name': f'LoadTest PV {i+1}/{num_pvs}',
            '_id': vid,
            'rand': random.randint(0, 2**31-1),
        }

        if i + 1 == outlink_pageview:
            outlink_url = random.choice(OUTLINKS)
            params['link'] = outlink_url
            params['url'] = outlink_url
            params['action_name'] = f'Outlink: {outlink_url}'

        if i + 1 == download_pageview:
            download_file = random.choice(DOWNLOADS)
            if download_file.startswith('http://') or download_file.startswith('https://'):
                download_url = download_file
            else:
                parsed = urllib.parse.urlparse(url)
                base_url = f"{parsed.scheme}://{parsed.netloc}"
                download_url = urllib.parse.urljoin(base_url, download_file)
            params['download'] = download_url
            params['url'] = download_url
            params['action_name'] = f'Download: {download_url.split('/')[-1]}'

        results.append((params, ua))

    return results


def main():
    # Load a small list of URLs from config/urls.txt
    urls_file = os.environ.get('URLS_FILE') or '/app/data/urls.txt'
    if not os.path.exists(urls_file):
        urls_file = '/config/urls.txt'
    if not os.path.exists(urls_file):
        # fallback to a minimal set
        urls = ['https://example.test/']
    else:
        urls = []
        with open(urls_file, 'r', encoding='utf-8') as f:
            for line in f:
                s = line.strip()
                if not s or s.startswith('#'):
                    continue
                urls.append(s.split()[0])

    print('Using MATOMO_URL =', MATOMO_URL)
    print('Simulating 3 visits: forcing one outlink and one download')

    # Visit 1: force outlink
    r1 = simulate_visit(urls, force_outlink=True, force_download=False)
    print('\n-- Visit 1 (outlink forced) --')
    for params, ua in r1:
        print(build_request(params))

    # Visit 2: force download
    r2 = simulate_visit(urls, force_outlink=False, force_download=True)
    print('\n-- Visit 2 (download forced) --')
    for params, ua in r2:
        print(build_request(params))

    # Visit 3: random
    r3 = simulate_visit(urls, force_outlink=False, force_download=False)
    print('\n-- Visit 3 (random) --')
    for params, ua in r3:
        print(build_request(params))


if __name__ == '__main__':
    main()
