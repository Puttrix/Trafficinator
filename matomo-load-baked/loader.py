#!/usr/bin/env python3
import os
import asyncio
import random
import time
import signal
import aiohttp
import logging
import urllib.parse
import ipaddress
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import pytz

# ---- Configuration via environment variables ----
MATOMO_URL = os.environ.get("MATOMO_URL", "https://matomo.example.com/matomo.php").rstrip("/")
SITE_ID = int(os.environ.get("MATOMO_SITE_ID", "1"))
MATOMO_TOKEN_AUTH = os.environ.get("MATOMO_TOKEN_AUTH", "")
URLS_FILE_ENV = os.environ.get("URLS_FILE")
DEFAULT_URL_CANDIDATES = [
    URLS_FILE_ENV,
    "/app/data/urls.txt",
    "/config/urls.txt",
]
FUNNEL_CONFIG_PATH = os.environ.get("FUNNEL_CONFIG_PATH", "/app/data/funnels.json")

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

# Custom events configuration
CLICK_EVENTS_PROBABILITY = float(os.environ.get("CLICK_EVENTS_PROBABILITY", "0.25"))  # 25% of visits will have click events
RANDOM_EVENTS_PROBABILITY = float(os.environ.get("RANDOM_EVENTS_PROBABILITY", "0.12"))  # 12% of visits will have random events

# Traffic source configuration
DIRECT_TRAFFIC_PROBABILITY = float(os.environ.get("DIRECT_TRAFFIC_PROBABILITY", "0.30"))  # 30% direct traffic

# Geolocation configuration
RANDOMIZE_VISITOR_COUNTRIES = os.environ.get("RANDOMIZE_VISITOR_COUNTRIES", "true").lower() == "true"

# Ecommerce configuration
ECOMMERCE_PROBABILITY = float(os.environ.get("ECOMMERCE_PROBABILITY", "0.05"))  # 5% of visits make a purchase
ECOMMERCE_ORDER_VALUE_MIN = float(os.environ.get("ECOMMERCE_ORDER_VALUE_MIN", "15.99"))
ECOMMERCE_ORDER_VALUE_MAX = float(os.environ.get("ECOMMERCE_ORDER_VALUE_MAX", "299.99"))
ECOMMERCE_ITEMS_MIN = int(os.environ.get("ECOMMERCE_ITEMS_MIN", "1"))
ECOMMERCE_ITEMS_MAX = int(os.environ.get("ECOMMERCE_ITEMS_MAX", "5"))
ECOMMERCE_TAX_RATE = float(os.environ.get("ECOMMERCE_TAX_RATE", "0.10"))  # 10% tax rate
ECOMMERCE_SHIPPING_RATES = list(map(float, os.environ.get("ECOMMERCE_SHIPPING_RATES", "0,5.99,9.99,15.99").split(",")))
ECOMMERCE_CURRENCY = os.environ.get("ECOMMERCE_CURRENCY", "SEK")  # Currency code for orders

# Timezone configuration
TIMEZONE = os.environ.get("TIMEZONE", "CET")  # Timezone for visit timestamps

# Backfill (historical replay) configuration
BACKFILL_ENABLED = os.environ.get("BACKFILL_ENABLED", "false").lower() == "true"
BACKFILL_START_DATE = os.environ.get("BACKFILL_START_DATE")
BACKFILL_END_DATE = os.environ.get("BACKFILL_END_DATE")
BACKFILL_DAYS_BACK = os.environ.get("BACKFILL_DAYS_BACK")
BACKFILL_DURATION_DAYS = os.environ.get("BACKFILL_DURATION_DAYS")
BACKFILL_MAX_VISITS_PER_DAY = int(os.environ.get("BACKFILL_MAX_VISITS_PER_DAY", "2000"))
BACKFILL_MAX_VISITS_TOTAL = int(os.environ.get("BACKFILL_MAX_VISITS_TOTAL", "200000"))
BACKFILL_RPS_LIMIT = os.environ.get("BACKFILL_RPS_LIMIT")
BACKFILL_RPS_LIMIT = float(BACKFILL_RPS_LIMIT) if BACKFILL_RPS_LIMIT else None
BACKFILL_SEED = os.environ.get("BACKFILL_SEED")
BACKFILL_SEED = int(BACKFILL_SEED) if BACKFILL_SEED is not None else None

# Startup control
def _parse_bool(value: Optional[str], default: bool = False) -> bool:
    if value is None:
        return default
    return value.lower() in ("1", "true", "yes", "on", "y")

AUTO_START = _parse_bool(os.environ.get("AUTO_START"), default=True)
START_SIGNAL_FILE = os.environ.get("START_SIGNAL_FILE", "/app/data/loadgen.start")
START_CHECK_INTERVAL = float(os.environ.get("START_CHECK_INTERVAL", "2.0"))

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

# Click events for UI interaction tracking
CLICK_EVENTS = [
    {'category': 'Navigation', 'action': 'Menu Click', 'name': 'Main Menu', 'value': None},
    {'category': 'Navigation', 'action': 'Button Click', 'name': 'Get Started', 'value': None},
    {'category': 'Navigation', 'action': 'Link Click', 'name': 'Learn More', 'value': None},
    {'category': 'UI', 'action': 'Tab Click', 'name': 'Product Features', 'value': None},
    {'category': 'UI', 'action': 'Accordion Click', 'name': 'FAQ Section', 'value': None},
    {'category': 'UI', 'action': 'Modal Open', 'name': 'Contact Form', 'value': None},
    {'category': 'UI', 'action': 'Image Click', 'name': 'Product Gallery', 'value': None},
    {'category': 'Social', 'action': 'Share Click', 'name': 'Twitter Share', 'value': None},
    {'category': 'Social', 'action': 'Share Click', 'name': 'Facebook Share', 'value': None},
    {'category': 'Social', 'action': 'Like Click', 'name': 'Article Like', 'value': None},
    {'category': 'Form', 'action': 'Submit', 'name': 'Newsletter Signup', 'value': None},
    {'category': 'Form', 'action': 'Focus', 'name': 'Search Input', 'value': None},
    {'category': 'Video', 'action': 'Play', 'name': 'Tutorial Video', 'value': None},
    {'category': 'Video', 'action': 'Pause', 'name': 'Product Demo', 'value': None},
    {'category': 'CTA', 'action': 'Click', 'name': 'Free Trial', 'value': None},
    {'category': 'CTA', 'action': 'Click', 'name': 'Request Quote', 'value': None},
]

# Random events for misc user interactions
RANDOM_EVENTS = [
    {'category': 'Engagement', 'action': 'Scroll', 'name': 'Page Bottom', 'value': 100},
    {'category': 'Engagement', 'action': 'Time on Page', 'name': 'Long Read', 'value': 300},
    {'category': 'Performance', 'action': 'Load Time', 'name': 'Page Load', 'value': 1200},
    {'category': 'Error', 'action': '404 Error', 'name': 'Broken Link', 'value': None},
    {'category': 'Error', 'action': 'Form Error', 'name': 'Validation Failed', 'value': None},
    {'category': 'Feature', 'action': 'Tool Usage', 'name': 'Calculator', 'value': 1},
    {'category': 'Feature', 'action': 'Filter Applied', 'name': 'Product Filter', 'value': None},
    {'category': 'Feature', 'action': 'Sort Applied', 'name': 'Price Sort', 'value': None},
    {'category': 'Content', 'action': 'Print', 'name': 'Article Print', 'value': None},
    {'category': 'Content', 'action': 'Bookmark', 'name': 'Page Bookmark', 'value': None},
    {'category': 'Mobile', 'action': 'Swipe', 'name': 'Image Gallery', 'value': None},
    {'category': 'Mobile', 'action': 'Tap', 'name': 'Phone Number', 'value': None},
    {'category': 'Analytics', 'action': 'Conversion', 'name': 'Goal Complete', 'value': 50},
    {'category': 'Analytics', 'action': 'Exit Intent', 'name': 'Modal Trigger', 'value': None},
    {'category': 'User', 'action': 'Login', 'name': 'User Login', 'value': None},
    {'category': 'User', 'action': 'Logout', 'name': 'User Logout', 'value': None},
]

# Traffic sources for realistic referrer simulation
REFERRER_SOURCES = {
    'search_engines': {
        'probability': 0.35,  # 35% from search engines
        'referrers': [
            'https://www.google.com/search?q=matomo+analytics',
            'https://www.google.com/search?q=web+analytics+tool',
            'https://www.google.com/search?q=open+source+analytics',
            'https://www.google.com/search?q=google+analytics+alternative',
            'https://www.bing.com/search?q=privacy+analytics',
            'https://duckduckgo.com/?q=matomo+tracking',
            'https://search.yahoo.com/search?p=web+statistics',
            'https://www.google.com/search?q=gdpr+compliant+analytics',
            'https://www.bing.com/search?q=self+hosted+analytics',
            'https://duckduckgo.com/?q=website+tracking+software'
        ]
    },
    'social_media': {
        'probability': 0.15,  # 15% from social media
        'referrers': [
            'https://twitter.com/',
            'https://www.linkedin.com/',
            'https://www.facebook.com/',
            'https://www.reddit.com/',
            'https://news.ycombinator.com/',
            'https://medium.com/',
            'https://dev.to/',
            'https://stackoverflow.com/',
            'https://github.com/',
            'https://www.producthunt.com/'
        ]
    },
    'referral_sites': {
        'probability': 0.20,  # 20% from referral sites
        'referrers': [
            'https://alternativeto.net/',
            'https://www.capterra.com/',
            'https://www.g2.com/',
            'https://sourceforge.net/',
            'https://www.softwaresuggest.com/',
            'https://blog.hubspot.com/',
            'https://moz.com/',
            'https://searchengineland.com/',
            'https://techcrunch.com/',
            'https://www.digitaltrends.com/',
            'https://blog.kissmetrics.com/',
            'https://www.semrush.com/',
            'https://backlinko.com/',
            'https://neilpatel.com/',
            'https://marketingland.com/'
        ]
    }
    # Note: Direct traffic (30%) is handled by not setting a referrer
}

SUPPORTED_FUNNEL_STEP_TYPES = {
    'pageview',
    'event',
    'site_search',
    'outlink',
    'download',
    'ecommerce',
}


def resolve_timezone():
    """Return a pytz timezone object, defaulting to UTC on error."""
    try:
        return pytz.timezone(TIMEZONE)
    except Exception:
        logging.warning("Unknown timezone '%s', falling back to UTC", TIMEZONE)
        return pytz.UTC


def _parse_date_str(value: str, field: str):
    """Parse YYYY-MM-DD into a date."""
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except Exception:
        raise ValueError(f"{field} must be YYYY-MM-DD")


def compute_backfill_window(tz) -> List[datetime.date]:
    """Compute the list of dates to backfill (inclusive)."""
    has_absolute = BACKFILL_START_DATE or BACKFILL_END_DATE
    has_relative = BACKFILL_DAYS_BACK or BACKFILL_DURATION_DAYS

    if has_absolute and has_relative:
        raise ValueError("Provide either absolute dates or days_back + duration, not both")

    today = datetime.now(tz).date()
    if has_absolute:
        if not (BACKFILL_START_DATE and BACKFILL_END_DATE):
            raise ValueError("BACKFILL_START_DATE and BACKFILL_END_DATE are both required")
        start = _parse_date_str(BACKFILL_START_DATE, "BACKFILL_START_DATE")
        end = _parse_date_str(BACKFILL_END_DATE, "BACKFILL_END_DATE")
    elif has_relative:
        if not (BACKFILL_DAYS_BACK and BACKFILL_DURATION_DAYS):
            raise ValueError("BACKFILL_DAYS_BACK and BACKFILL_DURATION_DAYS must both be set")
        start = today - timedelta(days=int(BACKFILL_DAYS_BACK))
        end = start + timedelta(days=int(BACKFILL_DURATION_DAYS) - 1)
    else:
        raise ValueError("Backfill window required: set start/end dates or days_back + duration")

    if start > end:
        raise ValueError("Backfill start date must be on or before end date")
    if end > today:
        raise ValueError("Backfill end date cannot be in the future")

    window_days = (end - start).days + 1
    if window_days > 180:
        raise ValueError("Backfill window cannot exceed 180 days")

    return [start + timedelta(days=i) for i in range(window_days)]


def day_bounds(day, tz):
    """Return start/end datetimes for a given date in the provided timezone."""
    start = tz.localize(datetime(day.year, day.month, day.day, 0, 0, 0))
    end = start + timedelta(days=1) - timedelta(seconds=1)
    return start, end


def format_cdt(dt):
    """Format a datetime for Matomo's cdt parameter.
    
    Matomo expects cdt to be in UTC timezone. This function converts
    timezone-aware datetimes to UTC before formatting.
    """
    if dt.tzinfo is not None:
        # Convert to UTC
        utc_dt = dt.astimezone(pytz.UTC)
    else:
        # Assume naive datetimes are already UTC
        utc_dt = dt
    return utc_dt.strftime('%Y-%m-%d %H:%M:%S')


def load_funnels_from_file(path: str) -> List[Dict[str, Any]]:
    """Load funnel definitions from JSON file."""
    if not path or not os.path.exists(path):
        logging.info("Funnel config not found at %s", path)
        return []

    try:
        with open(path, "r", encoding="utf-8") as handle:
            raw_data = json.load(handle)
    except Exception as exc:
        logging.error("Failed to load funnel config from %s: %s", path, exc)
        return []

    if not isinstance(raw_data, list):
        logging.error("Funnel config must be a list of funnel objects")
        return []

    funnels: List[Dict[str, Any]] = []
    for entry in raw_data:
        try:
            if not isinstance(entry, dict):
                raise ValueError("Funnel entry must be an object")

            enabled = bool(entry.get("enabled", True))
            if not enabled:
                continue

            steps = entry.get("steps", [])
            if not steps:
                logging.warning("Skipping funnel %s: no steps defined", entry.get("name"))
                continue

            if steps[0].get("type") != "pageview":
                logging.warning(
                    "Skipping funnel %s: first step must be a pageview",
                    entry.get("name"),
                )
                continue

            normalized_steps: List[Dict[str, Any]] = []
            for raw_step in steps:
                if not isinstance(raw_step, dict):
                    raise ValueError("Funnel step must be an object")
                step_type = raw_step.get("type")
                if step_type not in SUPPORTED_FUNNEL_STEP_TYPES:
                    raise ValueError(f"Unsupported step type: {step_type}")

                step = dict(raw_step)
                step["type"] = step_type

                min_delay = max(0.0, float(step.get("delay_seconds_min", 0.0)))
                max_delay = float(step.get("delay_seconds_max", min_delay))
                if max_delay < min_delay:
                    max_delay = min_delay

                step["delay_seconds_min"] = min_delay
                step["delay_seconds_max"] = max_delay
                normalized_steps.append(step)

            funnel = {
                "name": entry.get("name", "Unnamed Funnel"),
                "description": entry.get("description"),
                "probability": float(entry.get("probability", 0.0)),
                "priority": int(entry.get("priority", 0)),
                "enabled": True,
                "exit_after_completion": bool(entry.get("exit_after_completion", True)),
                "steps": normalized_steps,
            }
            funnel["probability"] = min(max(funnel["probability"], 0.0), 1.0)
            funnels.append(funnel)
        except Exception as exc:
            logging.warning("Skipping invalid funnel entry: %s", exc)

    funnels.sort(key=lambda f: f["priority"])
    if funnels:
        logging.info("Loaded %d active funnels from %s", len(funnels), path)
    else:
        logging.info("No active funnels found in %s", path)
    return funnels


def reload_funnels(path: Optional[str] = None) -> None:
    """Reload funnel definitions into global cache."""
    global FUNNELS
    config_path = path or FUNNEL_CONFIG_PATH
    FUNNELS = load_funnels_from_file(config_path)


FUNNELS: List[Dict[str, Any]] = load_funnels_from_file(FUNNEL_CONFIG_PATH)


def select_funnel() -> Optional[Dict[str, Any]]:
    """Randomly select a funnel to execute for the next visit."""
    if not FUNNELS:
        return None

    for funnel in FUNNELS:
        if random.random() <= funnel.get("probability", 0.0):
            return funnel
    return None

# Country distribution for visitor geolocation (based on typical web analytics patterns)
COUNTRY_IP_RANGES = {
    'United States': {
        'probability': 0.35,  # 35% US traffic
        'ip_ranges': [
            '173.252.0.0/16',    # Facebook range (for variety)
            '74.125.0.0/16',     # Google range
            '208.67.0.0/16',     # OpenDNS
            '192.30.252.0/22',   # GitHub
            '199.232.0.0/16',    # Akamai US
            '23.0.0.0/8',        # Akamai/CDN
            '104.16.0.0/12',     # Cloudflare US
            '142.250.0.0/15',    # Google US
        ]
    },
    'Germany': {
        'probability': 0.10,  # 10% German traffic
        'ip_ranges': [
            '78.46.0.0/15',      # Hetzner Germany
            '5.9.0.0/16',        # Hetzner
            '136.243.0.0/16',    # Hetzner dedicated
            '88.198.0.0/16',     # Hetzner
            '46.4.0.0/16',       # Deutsche Telekom
            '80.156.0.0/16',     # T-Mobile Germany
        ]
    },
    'United Kingdom': {
        'probability': 0.08,  # 8% UK traffic
        'ip_ranges': [
            '51.140.0.0/14',     # Microsoft Azure UK
            '185.40.0.0/16',     # UK ISP
            '86.0.0.0/12',       # Virgin Media UK
            '109.144.0.0/14',    # BT UK
            '2.96.0.0/11',       # Sky UK
        ]
    },
    'Canada': {
        'probability': 0.06,  # 6% Canadian traffic
        'ip_ranges': [
            '142.0.0.0/8',       # Canada general
            '206.47.0.0/16',     # Shaw Canada
            '24.0.0.0/13',       # Rogers Canada
            '99.224.0.0/11',     # Bell Canada
        ]
    },
    'France': {
        'probability': 0.06,  # 6% French traffic
        'ip_ranges': [
            '163.172.0.0/16',    # Online.net France
            '51.15.0.0/16',      # Scaleway France
            '212.129.0.0/16',    # Orange France
            '90.0.0.0/9',        # France Telecom
        ]
    },
    'Australia': {
        'probability': 0.05,  # 5% Australian traffic
        'ip_ranges': [
            '203.0.0.0/8',       # Australia/NZ general
            '144.132.0.0/16',    # Telstra Australia
            '101.160.0.0/11',    # Optus Australia
            '180.150.0.0/15',    # TPG Australia
        ]
    },
    'Netherlands': {
        'probability': 0.05,  # 5% Dutch traffic
        'ip_ranges': [
            '185.3.0.0/16',      # Netherlands hosting
            '146.185.0.0/16',    # TransIP Netherlands
            '31.220.0.0/16',     # Netherlands ISP
            '213.154.0.0/16',    # KPN Netherlands
        ]
    },
    'Japan': {
        'probability': 0.04,  # 4% Japanese traffic
        'ip_ranges': [
            '103.4.0.0/14',      # Japan hosting
            '210.0.0.0/7',       # Japan general
            '133.0.0.0/8',       # Japanese universities/research
        ]
    },
    'Sweden': {
        'probability': 0.03,  # 3% Swedish traffic  
        'ip_ranges': [
            '194.47.0.0/16',     # Telia Sweden
            '81.230.0.0/16',     # Bredband2 Sweden
            '78.72.0.0/15',      # Comhem Sweden
        ]
    },
    'Brazil': {
        'probability': 0.03,  # 3% Brazilian traffic
        'ip_ranges': [
            '200.0.0.0/7',       # Brazil general
            '177.0.0.0/8',       # Brazil ISPs
            '191.0.0.0/8',       # Brazil telecom
        ]
    },
    'Other Countries': {
        'probability': 0.15,  # 15% distributed among other countries
        'ip_ranges': [
            '85.0.0.0/8',        # Various European
            '195.0.0.0/8',       # European general
            '62.0.0.0/8',        # European ISPs
            '91.0.0.0/8',        # Eastern European
            '41.0.0.0/8',        # African
            '1.0.0.0/8',         # Asian Pacific
            '27.0.0.0/8',        # Asian
            '36.0.0.0/8',        # Various Asian
        ]
    }
}

# Ecommerce products database for realistic order simulation
ECOMMERCE_PRODUCTS = {
    'Electronics': [
        {'sku': 'PHONE-001', 'name': 'Smartphone Pro Max', 'price': 899.99},
        {'sku': 'PHONE-002', 'name': 'Budget Smartphone', 'price': 199.99},
        {'sku': 'LAPTOP-001', 'name': 'Gaming Laptop', 'price': 1299.99},
        {'sku': 'LAPTOP-002', 'name': 'Business Laptop', 'price': 749.99},
        {'sku': 'TABLET-001', 'name': 'Pro Tablet 11"', 'price': 599.99},
        {'sku': 'TABLET-002', 'name': 'Basic Tablet', 'price': 149.99},
        {'sku': 'HEADPHONE-001', 'name': 'Wireless Headphones', 'price': 249.99},
        {'sku': 'HEADPHONE-002', 'name': 'Gaming Headset', 'price': 89.99},
        {'sku': 'CAMERA-001', 'name': 'Digital Camera', 'price': 549.99},
        {'sku': 'WATCH-001', 'name': 'Smart Watch', 'price': 299.99}
    ],
    'Clothing': [
        {'sku': 'SHIRT-001', 'name': 'Cotton T-Shirt', 'price': 19.99},
        {'sku': 'SHIRT-002', 'name': 'Polo Shirt', 'price': 39.99},
        {'sku': 'PANTS-001', 'name': 'Jeans', 'price': 59.99},
        {'sku': 'PANTS-002', 'name': 'Chinos', 'price': 49.99},
        {'sku': 'SHOE-001', 'name': 'Running Shoes', 'price': 89.99},
        {'sku': 'SHOE-002', 'name': 'Casual Sneakers', 'price': 69.99},
        {'sku': 'JACKET-001', 'name': 'Winter Jacket', 'price': 129.99},
        {'sku': 'DRESS-001', 'name': 'Summer Dress', 'price': 79.99},
        {'sku': 'SWEATER-001', 'name': 'Wool Sweater', 'price': 89.99},
        {'sku': 'HAT-001', 'name': 'Baseball Cap', 'price': 24.99}
    ],
    'Books': [
        {'sku': 'BOOK-001', 'name': 'Programming Guide', 'price': 45.99},
        {'sku': 'BOOK-002', 'name': 'Mystery Novel', 'price': 12.99},
        {'sku': 'BOOK-003', 'name': 'Cook Book', 'price': 29.99},
        {'sku': 'BOOK-004', 'name': 'Science Textbook', 'price': 89.99},
        {'sku': 'BOOK-005', 'name': 'Biography', 'price': 19.99},
        {'sku': 'BOOK-006', 'name': 'Art History', 'price': 59.99},
        {'sku': 'BOOK-007', 'name': 'Travel Guide', 'price': 24.99},
        {'sku': 'BOOK-008', 'name': 'Business Strategy', 'price': 34.99},
        {'sku': 'EBOOK-001', 'name': 'Digital Marketing (eBook)', 'price': 9.99},
        {'sku': 'EBOOK-002', 'name': 'Fiction Collection (eBook)', 'price': 7.99}
    ],
    'Home & Garden': [
        {'sku': 'FURNITURE-001', 'name': 'Office Chair', 'price': 199.99},
        {'sku': 'FURNITURE-002', 'name': 'Desk Lamp', 'price': 49.99},
        {'sku': 'APPLIANCE-001', 'name': 'Coffee Maker', 'price': 89.99},
        {'sku': 'APPLIANCE-002', 'name': 'Blender', 'price': 69.99},
        {'sku': 'TOOL-001', 'name': 'Drill Set', 'price': 79.99},
        {'sku': 'TOOL-002', 'name': 'Screwdriver Kit', 'price': 29.99},
        {'sku': 'GARDEN-001', 'name': 'Plant Pot Set', 'price': 39.99},
        {'sku': 'GARDEN-002', 'name': 'Garden Hose', 'price': 34.99},
        {'sku': 'DECOR-001', 'name': 'Wall Art', 'price': 59.99},
        {'sku': 'STORAGE-001', 'name': 'Storage Box', 'price': 24.99}
    ],
    'Sports': [
        {'sku': 'SPORT-001', 'name': 'Yoga Mat', 'price': 29.99},
        {'sku': 'SPORT-002', 'name': 'Dumbbells Set', 'price': 89.99},
        {'sku': 'SPORT-003', 'name': 'Tennis Racket', 'price': 119.99},
        {'sku': 'SPORT-004', 'name': 'Basketball', 'price': 34.99},
        {'sku': 'SPORT-005', 'name': 'Running Shorts', 'price': 24.99},
        {'sku': 'SPORT-006', 'name': 'Athletic T-Shirt', 'price': 19.99},
        {'sku': 'SPORT-007', 'name': 'Water Bottle', 'price': 14.99},
        {'sku': 'SPORT-008', 'name': 'Gym Bag', 'price': 39.99},
        {'sku': 'SPORT-009', 'name': 'Resistance Bands', 'price': 19.99},
        {'sku': 'SPORT-010', 'name': 'Fitness Tracker', 'price': 149.99}
    ]
}

def resolve_urls_file() -> str:
    """
    Determine which URLs file to use for visit generation.

    Priority:
        1. Explicit URLS_FILE environment variable (if it exists on disk)
        2. Shared data volume (/app/data/urls.txt) managed by Control UI
        3. Embedded defaults in the image (/config/urls.txt)
    """
    for candidate in DEFAULT_URL_CANDIDATES:
        if candidate and os.path.exists(candidate):
            return candidate
    raise RuntimeError(
        "No URLs file found. Expected one of: "
        f"{', '.join(path for path in DEFAULT_URL_CANDIDATES if path)}"
    )


def read_urls(path):
    urls = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith('#'):
                continue
            urls.append(s.split()[0])
    if not urls:
        raise RuntimeError(f"No URLs found in URLs file: {path}")
    return urls

def choose_referrer():
    """Choose a referrer based on realistic traffic source probabilities.
    
    Returns:
        str or None: Referrer URL, or None for direct traffic
    """
    rand = random.random()
    
    # Direct traffic (no referrer)
    if rand < DIRECT_TRAFFIC_PROBABILITY:
        return None
    
    # Remaining probability distributed among referrer sources
    remaining_prob = 1.0 - DIRECT_TRAFFIC_PROBABILITY
    current_prob = DIRECT_TRAFFIC_PROBABILITY
    
    for source_type, config in REFERRER_SOURCES.items():
        source_prob = config['probability']
        if rand < current_prob + source_prob:
            return random.choice(config['referrers'])
        current_prob += source_prob
    
    # Fallback to direct traffic if probabilities don't add up to 1.0
    return None

def choose_country_and_ip():
    """Choose a country based on realistic distribution and generate an IP from that country.
    
    Returns:
        tuple: (country_name, ip_address) or (None, None) if disabled
    """
    if not RANDOMIZE_VISITOR_COUNTRIES:
        return None, None
    
    rand = random.random()
    current_prob = 0.0
    
    for country, config in COUNTRY_IP_RANGES.items():
        current_prob += config['probability']
        if rand < current_prob:
            # Choose random IP range from this country
            ip_range = random.choice(config['ip_ranges'])
            # Generate random IP within the chosen range
            network = ipaddress.ip_network(ip_range)
            # Get a random IP from the network (avoiding network and broadcast addresses)
            random_ip = network.network_address + random.randint(1, network.num_addresses - 2)
            return country, str(random_ip)
    
    # Fallback to US if probabilities don't add up
    us_range = random.choice(COUNTRY_IP_RANGES['United States']['ip_ranges'])
    network = ipaddress.ip_network(us_range)
    random_ip = network.network_address + random.randint(1, network.num_addresses - 2)
    return 'United States', str(random_ip)

def rand_hex(n=16):
    import random
    return ''.join(random.choice('0123456789abcdef') for _ in range(n))

def generate_ecommerce_order():
    """Generate a realistic ecommerce order with items, pricing, and metadata.
    
    Returns:
        tuple: (order_id, items_json, revenue, subtotal, tax, shipping) or None if no order
    """
    if random.random() >= ECOMMERCE_PROBABILITY:
        return None
    
    import json
    import uuid
    
    # Generate unique order ID
    order_id = str(uuid.uuid4())[:8].upper()
    
    # Determine number of items (weighted toward single items)
    num_items = random.randint(ECOMMERCE_ITEMS_MIN, ECOMMERCE_ITEMS_MAX)
    weights = [0.6, 0.25, 0.1, 0.04, 0.01]  # Favor 1-2 items
    if num_items <= len(weights):
        if random.random() > weights[num_items - 1]:
            num_items = 1
    
    # Select items from different categories
    selected_items = []
    categories = list(ECOMMERCE_PRODUCTS.keys())
    
    for _ in range(num_items):
        category = random.choice(categories)
        product = random.choice(ECOMMERCE_PRODUCTS[category])
        
        # Random quantity (mostly 1, sometimes 2-3)
        quantity = 1 if random.random() < 0.8 else random.randint(2, 3)
        
        # Slight price variation (±5%)
        base_price = product['price']
        price_variation = random.uniform(0.95, 1.05)
        final_price = round(base_price * price_variation, 2)
        
        # Ensure price within configured range
        final_price = max(ECOMMERCE_ORDER_VALUE_MIN / num_items, 
                         min(final_price, ECOMMERCE_ORDER_VALUE_MAX / num_items))
        
        # Matomo ecommerce item format: [sku, name, category, price, quantity]
        item = [
            product['sku'],
            product['name'],
            category,
            final_price,
            quantity
        ]
        selected_items.append(item)
    
    # Calculate order totals
    subtotal = sum(item[3] * item[4] for item in selected_items)
    shipping = random.choice(ECOMMERCE_SHIPPING_RATES)
    tax = round((subtotal + shipping) * ECOMMERCE_TAX_RATE, 2)
    revenue = round(subtotal + shipping + tax, 2)
    
    # Ensure total is within configured range
    if revenue < ECOMMERCE_ORDER_VALUE_MIN or revenue > ECOMMERCE_ORDER_VALUE_MAX:
        # Scale items proportionally to fit range
        target_subtotal = random.uniform(ECOMMERCE_ORDER_VALUE_MIN * 0.8, 
                                       ECOMMERCE_ORDER_VALUE_MAX * 0.8) - shipping
        scale_factor = target_subtotal / subtotal
        
        for item in selected_items:
            item[3] = round(item[3] * scale_factor, 2)
        
        subtotal = sum(item[3] * item[4] for item in selected_items)
        tax = round((subtotal + shipping) * ECOMMERCE_TAX_RATE, 2)
        revenue = round(subtotal + shipping + tax, 2)
    
    # Convert items to JSON format for Matomo
    items_json = json.dumps(selected_items)
    
    return order_id, items_json, revenue, subtotal, tax, shipping


def _generate_funnel_order(step: Dict[str, Any]):
    """Generate an ecommerce order for a funnel step."""
    global ECOMMERCE_PROBABILITY
    original_probability = ECOMMERCE_PROBABILITY
    try:
        ECOMMERCE_PROBABILITY = 1.0
        order = generate_ecommerce_order()
    finally:
        ECOMMERCE_PROBABILITY = original_probability

    if order is None:
        raise RuntimeError("Unable to generate ecommerce order for funnel step")

    order_id, items_json, revenue, subtotal, tax, shipping = order

    if step.get("ecommerce_revenue") is not None:
        revenue = float(step["ecommerce_revenue"])
    if step.get("ecommerce_subtotal") is not None:
        subtotal = float(step["ecommerce_subtotal"])
    if step.get("ecommerce_tax") is not None:
        tax = float(step["ecommerce_tax"])
    if step.get("ecommerce_shipping") is not None:
        shipping = float(step["ecommerce_shipping"])

    return order_id, items_json, revenue, subtotal, tax, shipping


async def execute_funnel(session, funnel: Dict[str, Any], urls: List[str], day_range: Optional[tuple] = None) -> bool:
    """
    Execute a funnel sequence. Returns True if the visit should end after completion.
    """
    steps = funnel.get("steps", [])
    if not steps:
        return True

    logging.info("Executing funnel '%s' (%d steps)", funnel.get("name"), len(steps))

    visit_id = rand_hex(16)
    user_agent = random.choice(USER_AGENTS)
    referrer = choose_referrer()
    country, visitor_ip = choose_country_and_ip()

    # Prepare delay schedule
    delays: List[float] = []
    for step in steps:
        min_delay = max(0.0, float(step.get("delay_seconds_min", 0.0)))
        max_delay = float(step.get("delay_seconds_max", min_delay))
        if max_delay < min_delay:
            max_delay = min_delay
        delays.append(random.uniform(min_delay, max_delay))

    tz = resolve_timezone()
    total_duration = sum(delays)

    if day_range:
        day_start, day_end = day_range
        seconds_available = max(1, int((day_end - day_start).total_seconds()))
        earliest_start = day_start
        latest_start = day_end - timedelta(seconds=total_duration)
        if latest_start < earliest_start:
            latest_start = earliest_start
        offset = random.uniform(0, max(0, (latest_start - earliest_start).total_seconds()))
        current_dt = earliest_start + timedelta(seconds=offset)
    else:
        now_dt = datetime.now(tz)
        current_dt = now_dt - timedelta(seconds=total_duration)
    last_page_url: Optional[str] = None

    for index, step in enumerate(steps):
        step_type = step.get("type", "pageview")
        delay_after = delays[index]

        page_url = step.get("url") or last_page_url or (random.choice(urls) if urls else MATOMO_URL)
        action_name = step.get("action_name")

        params: Dict[str, Any] = {
            'idsite': SITE_ID,
            'rec': 1,
            '_id': visit_id,
            'rand': random.randint(0, 2**31 - 1),
            'cdt': format_cdt(current_dt),
            'url': page_url,
        }

        if action_name:
            params['action_name'] = action_name

        if visitor_ip:
            params['cip'] = visitor_ip
        if MATOMO_TOKEN_AUTH:
            params['token_auth'] = MATOMO_TOKEN_AUTH

        if index == 0:
            params['new_visit'] = 1
            if referrer:
                params['urlref'] = referrer
        elif last_page_url:
            params['urlref'] = last_page_url

        if step_type == 'pageview':
            params.setdefault('action_name', f"Funnel: {funnel.get('name')} ({index+1}/{len(steps)})")
            params['pv_id'] = rand_hex(6)
            last_page_url = page_url

        elif step_type == 'event':
            params['e_c'] = step['event_category']
            params['e_a'] = step['event_action']
            params['e_n'] = step['event_name']
            if step.get('event_value') is not None:
                params['e_v'] = step['event_value']
            params.setdefault('action_name', f"Funnel Event: {step['event_action']}")
            last_page_url = page_url

        elif step_type == 'site_search':
            params['search'] = step['search_keyword']
            if step.get('search_category'):
                params['search_cat'] = step['search_category']
            search_results = step.get('search_results')
            if search_results is None:
                search_results = random.randint(0, 25)
            params['search_count'] = int(search_results)
            params.setdefault('action_name', f"Funnel Search: {step['search_keyword']}")
            last_page_url = page_url

        elif step_type == 'outlink':
            target_url = step.get('target_url') or page_url
            if not target_url.startswith(('http://', 'https://')):
                parsed = urllib.parse.urlparse(page_url)
                base_url = f"{parsed.scheme}://{parsed.netloc}"
                target_url = urllib.parse.urljoin(base_url, target_url)
            params['link'] = target_url
            params.setdefault('action_name', f"Funnel Outlink: {target_url}")

        elif step_type == 'download':
            target_url = step.get('target_url') or page_url
            if not target_url.startswith(('http://', 'https://')):
                parsed = urllib.parse.urlparse(page_url)
                base_url = f"{parsed.scheme}://{parsed.netloc}"
                target_url = urllib.parse.urljoin(base_url, target_url)
            params['download'] = target_url
            params.setdefault('action_name', f"Funnel Download: {target_url.split('/')[-1]}")

        elif step_type == 'ecommerce':
            order_id, items_json, revenue, subtotal, tax, shipping = _generate_funnel_order(step)
            params.update({
                'idgoal': '0',
                'ec_id': order_id,
                'ec_items': items_json,
                'revenue': f"{revenue:.2f}",
                'ec_st': f"{subtotal:.2f}",
                'ec_tx': f"{tax:.2f}",
            })
            params['ec_currency'] = ECOMMERCE_CURRENCY
            params.setdefault('action_name', f"Funnel Order: {order_id}")
            last_page_url = page_url

        headers = {'User-Agent': user_agent}

        try:
            await send_hit(session, params, headers)
        except Exception as exc:  # pragma: no cover - network errors already handled in send_hit
            logging.error("Error sending funnel step '%s': %s", step_type, exc)

        current_dt += timedelta(seconds=delay_after)

    return bool(funnel.get("exit_after_completion", True))

# Logging configuration (can be adjusted with environment variable LOG_LEVEL)
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s %(levelname)s %(message)s')


def choose_action_pages(num_pvs: int, want_search: bool, want_outlink: bool, want_download: bool, want_click_event: bool, want_random_event: bool):
    """Choose pageview indices for search/outlink/download/event actions.

    Guarantees:
    - If num_pvs <= 1 => all actions disabled (-1).
    - Otherwise, any chosen page is in the inclusive range [2, num_pvs].

    This helper is deterministic only in terms of its constraints; it uses
    randomness for selection so callers should treat results as non-deterministic.
    """
    if num_pvs <= 1:
        return -1, -1, -1, -1, -1

    def pick(want: bool):
        return random.randint(2, num_pvs) if want else -1

    return pick(want_search), pick(want_outlink), pick(want_download), pick(want_click_event), pick(want_random_event)


def check_daily_cap(now, day_start, visits_today_local, max_total):
    """Return (should_pause, new_day_start, new_visits_today)

    should_pause: True if production should pause (cap reached and window not expired)
    new_day_start: updated day window start timestamp (reset if window expired)
    new_visits_today: updated visits_today (reset if window expired)
    """
    if max_total <= 0:
        return False, day_start, visits_today_local
    # If window expired, reset
    if now - day_start >= 86400:
        return False, now, 0
    # Pause if we've hit or exceeded cap
    if visits_today_local >= max_total:
        return True, day_start, visits_today_local
    return False, day_start, visits_today_local

async def send_hit(session, params, headers):
    try:
        async with session.get(MATOMO_URL, params=params, headers=headers) as resp:
            await resp.read()
            return resp.status
    except Exception:
        return None

async def visit(session, urls, day_range: Optional[tuple] = None):
    funnel = select_funnel()
    if funnel:
        exit_after = await execute_funnel(session, funnel, urls, day_range)
        if exit_after:
            return

    # One "visit" with 3–6 pageviews (configurable)
    num_pvs = random.randint(PAGEVIEWS_MIN, PAGEVIEWS_MAX)
    vid = rand_hex(16)  # visitor id
    ua = random.choice(USER_AGENTS)
    ref = choose_referrer()  # Choose realistic referrer or None for direct traffic
    country, visitor_ip = choose_country_and_ip()  # Choose country and generate IP
    
    # Determine if this visit will include site search, outlinks, downloads, or custom events
    has_search = random.random() < SITESEARCH_PROBABILITY
    has_outlink = random.random() < OUTLINKS_PROBABILITY
    has_download = random.random() < DOWNLOADS_PROBABILITY
    has_click_event = random.random() < CLICK_EVENTS_PROBABILITY
    has_random_event = random.random() < RANDOM_EVENTS_PROBABILITY

    # Ensure search/outlink/download/events are NEVER the first pageview.
    # If there's only one pageview in the visit, disable these actions.
    search_pageview, outlink_pageview, download_pageview, click_event_pageview, random_event_pageview = choose_action_pages(
        num_pvs, has_search, has_outlink, has_download, has_click_event, has_random_event
    )
    
    # Check if this visit will include an ecommerce order
    ecommerce_order = generate_ecommerce_order()
    ecommerce_pageview = -1
    if ecommerce_order and num_pvs > 1:
        # Place ecommerce order on the last pageview (checkout completion)
        ecommerce_pageview = num_pvs

    # --- Build a simulated timeline for this visit ---
    # Total desired visit duration in seconds (includes time after last pageview)
    visit_duration_seconds = random.uniform(VISIT_DURATION_MIN * 60, VISIT_DURATION_MAX * 60)

    # Split visit duration across each pageview as dwell time segments.
    # There are num_pvs segments: one before each subsequent PV, and one final segment after the last PV.
    # Use random weights to create natural variation across pages.
    weights = [random.uniform(0.5, 1.5) for _ in range(num_pvs)]
    total_weight = sum(weights)
    dwell_times = [(visit_duration_seconds * w / total_weight) for w in weights]

    tz = resolve_timezone()
    day_start = None
    day_end = None
    if day_range:
        day_start, day_end = day_range

    if day_start and day_end:
        seconds_available = max(1, int((day_end - day_start).total_seconds()))
        latest_start = day_end - timedelta(seconds=visit_duration_seconds)
        if latest_start < day_start:
            latest_start = day_start
        offset = random.uniform(0, max(0, (latest_start - day_start).total_seconds()))
        start_dt = day_start + timedelta(seconds=offset)
    else:
        now_dt = datetime.now(tz)
        start_dt = now_dt - timedelta(seconds=visit_duration_seconds)

    # Precompute the pageview timestamps and pageview IDs
    pv_times = []
    acc = timedelta(0)
    for idx in range(num_pvs):
        pv_times.append(start_dt + acc)
        if idx < num_pvs - 1:
            acc += timedelta(seconds=dwell_times[idx])

    pv_ids = [rand_hex(6) for _ in range(num_pvs)]

    for i in range(num_pvs):
        url = random.choice(urls)
        # Keep the original page URL (the page that contains any outlink/download)
        page_url = url

        # Use the simulated timeline timestamp for this pageview (converted to UTC for Matomo)
        timestamp = format_cdt(pv_times[i])

        params = {
            'idsite': SITE_ID,
            'rec': 1,
            'url': page_url,
            'action_name': f'LoadTest PV {i+1}/{num_pvs}',
            '_id': vid,
            'rand': random.randint(0, 2**31-1),
            'cdt': timestamp,
        }

        # Include a stable pageview id so we can later send a ping to extend the last page's time
        params['pv_id'] = pv_ids[i]
        
        # Add visitor IP for geolocation if enabled
        if visitor_ip:
            params['cip'] = visitor_ip
        # Include token_auth whenever provided so Matomo accepts overridden cdt/cip
        if MATOMO_TOKEN_AUTH:
            params['token_auth'] = MATOMO_TOKEN_AUTH

        # If this is not the first pageview, include referrer as the previous page
        # so Matomo can attribute outlinks/downloads correctly.
        if i == 0:
            params['new_visit'] = 1
            # Only set referrer if it's not None (direct traffic has no referrer)
            if ref is not None:
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
            # Set the clicked link; keep params['url'] as the page URL where the link was clicked
            params['link'] = outlink_url
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

            # Set download parameter; keep params['url'] as the page URL where the download was initiated
            params['download'] = download_url
            params['action_name'] = f'Download: {download_url.split("/")[-1]}'
        
        # Add click event tracking if this is the click event pageview
        elif i + 1 == click_event_pageview:
            click_event = random.choice(CLICK_EVENTS)
            params['e_c'] = click_event['category']
            params['e_a'] = click_event['action']
            params['e_n'] = click_event['name']
            if click_event['value'] is not None:
                params['e_v'] = click_event['value']
            params['action_name'] = f'Event: {click_event["action"]} - {click_event["name"]}'
        
        # Add random event tracking if this is the random event pageview
        elif i + 1 == random_event_pageview:
            random_event = random.choice(RANDOM_EVENTS)
            params['e_c'] = random_event['category']
            params['e_a'] = random_event['action']
            params['e_n'] = random_event['name']
            if random_event['value'] is not None:
                params['e_v'] = random_event['value']
            params['action_name'] = f'Event: {random_event["action"]} - {random_event["name"]}'
        
        # Add ecommerce order tracking if this is the ecommerce pageview
        elif i + 1 == ecommerce_pageview and ecommerce_order:
            order_id, items_json, revenue, subtotal, tax, shipping = ecommerce_order
            params['idgoal'] = '0'  # Required for ecommerce orders
            params['ec_id'] = order_id
            params['ec_items'] = items_json
            params['revenue'] = str(revenue)
            params['ec_st'] = str(subtotal)
            params['ec_tx'] = str(tax)
            params['ec_currency'] = ECOMMERCE_CURRENCY
            params['action_name'] = f'Ecommerce Order: {order_id} ({ECOMMERCE_CURRENCY} {revenue})'
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

        # Log only the outlink/download/event/ecommerce hits at INFO level to avoid noise
        if 'download' in params:
            logging.info('Sending download hit: visitor=%s file=%s referer=%s', vid, params.get('download'), params.get('urlref'))
            logging.debug('Matomo request: %s', request_url)
        elif 'link' in params:
            logging.info('Sending outlink hit: visitor=%s link=%s referer=%s', vid, params.get('link'), params.get('urlref'))
            logging.debug('Matomo request: %s', request_url)
        elif 'e_c' in params:
            logging.info('Sending custom event: visitor=%s category=%s action=%s name=%s value=%s', vid, params.get('e_c'), params.get('e_a'), params.get('e_n'), params.get('e_v', 'None'))
            logging.debug('Matomo request: %s', request_url)
        elif 'ec_id' in params:
            logging.info('Sending ecommerce order: visitor=%s order=%s revenue=%s items=%s', vid, params.get('ec_id'), params.get('revenue'), len(eval(params.get('ec_items', '[]'))))
            logging.debug('Matomo request: %s', request_url)
        else:
            logging.debug('Sending pageview: visitor=%s action=%s', vid, params.get('action_name'))

        await send_hit(session, params, headers)
        
        # Set last_page_url for next iteration
        if i + 1 == outlink_pageview or i + 1 == download_pageview:
            # user clicked away; keep last_page_url as the page that contained the link
            last_page_url = page_url
        else:
            # for custom events and regular pageviews, use the current page URL
            last_page_url = page_url
            
        if i < num_pvs - 1:
            # Keep a short real delay to smooth outbound requests (cdt handles the simulated timing)
            await asyncio.sleep(random.uniform(PAUSE_BETWEEN_PVS_MIN, PAUSE_BETWEEN_PVS_MAX))
    
    # Extend the last page's time-on-page using a ping hit
    try:
        last_pv_time = pv_times[-1]
        last_pv_id = pv_ids[-1]
        last_page_timestamp = format_cdt(last_pv_time + timedelta(seconds=dwell_times[-1]))

        ping_params = {
            'idsite': SITE_ID,
            'rec': 1,
            'url': last_page_url,
            '_id': vid,
            'cdt': last_page_timestamp,
            'ping': 1,
            'pv_id': last_pv_id,
        }
        if visitor_ip:
            ping_params['cip'] = visitor_ip
        if MATOMO_TOKEN_AUTH:
            ping_params['token_auth'] = MATOMO_TOKEN_AUTH

        headers = {'User-Agent': ua}
        logging.debug('Sending ping to extend last page time: visitor=%s pv_id=%s', vid, last_pv_id)
        await send_hit(session, ping_params, headers)
    except Exception:
        # Best-effort; if ping fails, the last page time may appear shorter (0s)
        pass

class GracefulExit(SystemExit):
    pass

def _handle_sig(*_):
    raise GracefulExit()


async def run_realtime(session, urls):
    """Realtime load generation loop (existing behavior)."""
    visits_per_sec = TARGET_VISITS_PER_DAY / 86400.0
    tokens = 0.0
    last = time.time()

    q = asyncio.Queue(maxsize=CONCURRENCY * 2)

    start_ts = time.time()
    visits_total = 0
    visits_today = 0
    day_window_start = start_ts

    async def producer():
        nonlocal tokens, last, visits_today
        while True:
            if AUTO_STOP_AFTER_HOURS > 0 and (time.time() - start_ts) >= AUTO_STOP_AFTER_HOURS * 3600:
                await q.put(None)
                await asyncio.sleep(0.1)
                break

            now = time.time()
            dt = now - last
            last = now
            tokens += visits_per_sec * dt
            if tokens > CONCURRENCY:
                tokens = CONCURRENCY

            if MAX_TOTAL_VISITS > 0:
                should_pause, new_day_start, new_visits_today = check_daily_cap(now, day_window_start, visits_today, MAX_TOTAL_VISITS)
                day_window_start = new_day_start
                visits_today = new_visits_today
                if should_pause:
                    logging.info('[loadgen] daily cap reached (%d). Pausing until window resets.', MAX_TOTAL_VISITS)
                    await asyncio.sleep(5)
                    continue

            while tokens >= 1 and not q.full():
                await q.put(1)
                tokens -= 1

            await asyncio.sleep(0.25)

    async def worker():
        nonlocal visits_total, visits_today
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
                visits_today += 1
                q.task_done()

    workers = [asyncio.create_task(worker()) for _ in range(CONCURRENCY)]
    prod = asyncio.create_task(producer())

    last_log = time.time()
    try:
        while True:
            await asyncio.sleep(10)
            if AUTO_STOP_AFTER_HOURS > 0 and (time.time() - start_ts) >= AUTO_STOP_AFTER_HOURS * 3600:
                break
            if MAX_TOTAL_VISITS > 0 and visits_total >= MAX_TOTAL_VISITS:
                break

            now = time.time()
            if now - last_log >= 60:
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

    elapsed = time.time() - start_ts
    rate = visits_total / elapsed if elapsed > 0 else 0.0
    print(f"[loadgen] Done. Sent {visits_total} visits in {elapsed:.1f}s (~{rate*86400:.0f}/day).")


async def run_backfill_day(session, urls, day_range: tuple, visits_target: int, rps_limit: Optional[float]):
    """Run backfill for a single day window."""
    tokens = 0.0
    last = time.time()
    rate_limit = rps_limit if rps_limit else TARGET_VISITS_PER_DAY / 86400.0

    q = asyncio.Queue(maxsize=CONCURRENCY * 2)
    visits_total = 0
    visits_scheduled = 0

    async def producer():
        nonlocal tokens, last, visits_scheduled
        while visits_scheduled < visits_target:
            now = time.time()
            dt = now - last
            last = now
            tokens += rate_limit * dt
            if tokens > CONCURRENCY:
                tokens = CONCURRENCY

            while tokens >= 1 and not q.full() and visits_scheduled < visits_target:
                await q.put(1)
                tokens -= 1
                visits_scheduled += 1

            await asyncio.sleep(0.2)

        for _ in range(CONCURRENCY):
            await q.put(None)

    async def worker():
        nonlocal visits_total
        while True:
            job = await q.get()
            if job is None:
                q.task_done()
                break
            try:
                await visit(session, urls, day_range)
            except Exception:
                pass
            finally:
                visits_total += 1
                q.task_done()

    workers = [asyncio.create_task(worker()) for _ in range(CONCURRENCY)]
    prod = asyncio.create_task(producer())
    try:
        await asyncio.gather(*workers)
    finally:
        prod.cancel()
        await asyncio.gather(prod, return_exceptions=True)

    return visits_total


async def run_backfill(session, urls):
    """Historical backfill loop with per-day caps and TZ-aware dates."""
    tz = resolve_timezone()
    try:
        days = compute_backfill_window(tz)
    except Exception as exc:
        logging.error("[backfill] Invalid configuration: %s", exc)
        return []

    remaining_total = BACKFILL_MAX_VISITS_TOTAL if BACKFILL_MAX_VISITS_TOTAL > 0 else None
    per_day_cap = BACKFILL_MAX_VISITS_PER_DAY if BACKFILL_MAX_VISITS_PER_DAY > 0 else int(TARGET_VISITS_PER_DAY)
    summary: List[Dict[str, Any]] = []

    for idx, day in enumerate(days):
        if remaining_total is not None and remaining_total <= 0:
            summary.append({"date": str(day), "sent": 0, "skipped": True, "reason": "total_cap_reached"})
            continue

        if BACKFILL_SEED is not None:
            random.seed(BACKFILL_SEED + idx)

        day_start, day_end = day_bounds(day, tz)
        day_target = per_day_cap
        if remaining_total is not None:
            day_target = min(day_target, remaining_total)

        if day_target <= 0:
            summary.append({"date": str(day), "sent": 0, "skipped": True, "reason": "cap_zero"})
            continue

        logging.info("[backfill] Replaying %d visits for %s (%s)", day_target, day, TIMEZONE)
        sent = await run_backfill_day(session, urls, (day_start, day_end), day_target, BACKFILL_RPS_LIMIT)
        if remaining_total is not None:
            remaining_total -= sent

        summary.append({"date": str(day), "sent": sent, "target": day_target, "timezone": TIMEZONE})

    logging.info("[backfill] Complete: %s", summary)
    return summary

async def wait_for_start_signal():
    """Block startup when AUTO_START is disabled until a start signal file appears."""
    if AUTO_START:
        return

    logging.info("[startup] AUTO_START disabled; waiting for start signal file at %s", START_SIGNAL_FILE)
    while True:
        if os.path.exists(START_SIGNAL_FILE):
            try:
                os.remove(START_SIGNAL_FILE)
            except OSError:
                pass
            logging.info("[startup] Start signal detected; beginning load generation.")
            return
        await asyncio.sleep(START_CHECK_INTERVAL)

async def main():
    await wait_for_start_signal()
    urls_file = resolve_urls_file()
    urls = read_urls(urls_file)

    connector = aiohttp.TCPConnector(limit=CONCURRENCY, ssl=False)
    timeout = aiohttp.ClientTimeout(total=None)
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        if BACKFILL_ENABLED:
            await run_backfill(session, urls)
        else:
            await run_realtime(session, urls)

if __name__ == "__main__":
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, _handle_sig)
    asyncio.run(main())
