#!/usr/bin/env python3
import os, asyncio, random, time, signal, sys
import aiohttp

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

USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:117.0) Gecko/20100101 Firefox/117.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
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
        # Force new visit on the first pageview to avoid merging with older sessions
        if i == 0:
            params['new_visit'] = 1
            params['urlref'] = ref

        headers = {'User-Agent': ua}
        await send_hit(session, params, headers)
        if i < num_pvs - 1:
            await asyncio.sleep(random.uniform(PAUSE_BETWEEN_PVS_MIN, PAUSE_BETWEEN_PVS_MAX))

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
                while tokens >= 1 and not q.full():
                    # Check auto-stop by count before producing next job
                    if MAX_TOTAL_VISITS > 0 and visits_total >= MAX_TOTAL_VISITS:
                        await q.put(None)
                        await asyncio.sleep(0.1)
                        return
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
