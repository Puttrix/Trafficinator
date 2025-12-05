#!/usr/bin/env python3
"""
Local Matomo Backfill Test Script

This script tests the backfill functionality against a local Matomo instance.
It sends a small number of historical visits and verifies they appear in Matomo.

Usage:
    python test_backfill_local.py

Configuration via environment variables:
    MATOMO_URL         - Matomo tracking URL (default: http://localhost:8181/matomo.php)
    MATOMO_SITE_ID     - Site ID to track to (default: 1)
    MATOMO_TOKEN_AUTH  - API token for authentication (REQUIRED for backfill)
"""

import os
import sys
import asyncio
import aiohttp
from datetime import datetime, timedelta
import pytz

# Add the loader module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'matomo-load-baked'))

# Configuration - set MATOMO_TOKEN_AUTH env var or edit default for local testing
MATOMO_URL = os.environ.get("MATOMO_URL", "http://localhost:8181/matomo.php")
MATOMO_SITE_ID = os.environ.get("MATOMO_SITE_ID", "1")
MATOMO_TOKEN_AUTH = os.environ.get("MATOMO_TOKEN_AUTH", "")  # Required for backfill

# Test configuration
TEST_DAYS_BACK = 3  # How many days back to backfill
TEST_VISITS_PER_DAY = 5  # Small number for testing
TIMEZONE = "CET"


def check_config():
    """Verify configuration is valid."""
    print("=" * 60)
    print("Matomo Backfill Test Configuration")
    print("=" * 60)
    print(f"MATOMO_URL:        {MATOMO_URL}")
    print(f"MATOMO_SITE_ID:    {MATOMO_SITE_ID}")
    print(f"MATOMO_TOKEN_AUTH: {'*' * 8 + MATOMO_TOKEN_AUTH[-4:] if MATOMO_TOKEN_AUTH else '(NOT SET)'}")
    print(f"TIMEZONE:          {TIMEZONE}")
    print(f"TEST_DAYS_BACK:    {TEST_DAYS_BACK}")
    print(f"TEST_VISITS_PER_DAY: {TEST_VISITS_PER_DAY}")
    print("=" * 60)
    
    if not MATOMO_TOKEN_AUTH:
        print("\n❌ ERROR: MATOMO_TOKEN_AUTH is required for backfill!")
        print("   Set it with: export MATOMO_TOKEN_AUTH='your_token_here'")
        print("   Find it in Matomo: Settings > Personal > Security > Auth tokens")
        return False
    
    return True


async def test_matomo_connection():
    """Test basic connectivity to Matomo."""
    print("\n🔗 Testing Matomo connectivity...")
    
    # Simple tracking request without auth
    params = {
        'idsite': MATOMO_SITE_ID,
        'rec': 1,
        'url': 'http://test.example.com/connection-test',
        'action_name': 'Connection Test',
        '_id': 'a' * 16,
        'rand': 12345,
        'send_image': 0,
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(MATOMO_URL, params=params, timeout=10) as resp:
                if resp.status == 200 or resp.status == 204:
                    print(f"   ✅ Matomo responded with status {resp.status}")
                    return True
                else:
                    print(f"   ❌ Matomo responded with status {resp.status}")
                    return False
        except Exception as e:
            print(f"   ❌ Connection failed: {e}")
            return False


async def test_backfill_single_visit(session, date, visit_num):
    """Send a single backfill visit and return success status."""
    tz = pytz.timezone(TIMEZONE)
    
    # Create a visit time during business hours on the target date
    hour = 9 + (visit_num % 8)  # 9am-4pm
    minute = (visit_num * 17) % 60  # Spread minutes
    
    local_dt = tz.localize(datetime(date.year, date.month, date.day, hour, minute, 0))
    utc_dt = local_dt.astimezone(pytz.UTC)
    cdt_timestamp = utc_dt.strftime('%Y-%m-%d %H:%M:%S')
    
    visitor_id = f"backfilltest{visit_num:04d}"[:16].ljust(16, '0')
    
    params = {
        'idsite': MATOMO_SITE_ID,
        'rec': 1,
        'url': f'http://backfill-test.example.com/page-{visit_num}',
        'action_name': f'Backfill Test Page {visit_num} - {date}',
        '_id': visitor_id,
        'rand': hash(f"{date}-{visit_num}") % (2**31),
        'cdt': cdt_timestamp,
        'token_auth': MATOMO_TOKEN_AUTH,
        'new_visit': 1,
        'send_image': 0,
    }
    
    try:
        async with session.get(MATOMO_URL, params=params, timeout=10) as resp:
            status = resp.status
            if status in (200, 204):
                return True, cdt_timestamp
            else:
                body = await resp.text()
                return False, f"Status {status}: {body[:100]}"
    except Exception as e:
        return False, str(e)


async def run_backfill_test():
    """Run the backfill test."""
    print("\n🚀 Starting Backfill Test...")
    
    tz = pytz.timezone(TIMEZONE)
    today = datetime.now(tz).date()
    
    # Calculate test date range
    start_date = today - timedelta(days=TEST_DAYS_BACK)
    dates = [start_date + timedelta(days=i) for i in range(TEST_DAYS_BACK)]
    
    print(f"\n📅 Test Date Range: {dates[0]} to {dates[-1]}")
    print(f"   Total visits to send: {len(dates) * TEST_VISITS_PER_DAY}")
    
    results = {
        'success': 0,
        'failed': 0,
        'by_date': {}
    }
    
    async with aiohttp.ClientSession() as session:
        for date in dates:
            date_str = str(date)
            results['by_date'][date_str] = {'success': 0, 'failed': 0}
            print(f"\n   📆 Processing {date_str}...")
            
            for visit_num in range(TEST_VISITS_PER_DAY):
                success, detail = await test_backfill_single_visit(session, date, visit_num)
                
                if success:
                    results['success'] += 1
                    results['by_date'][date_str]['success'] += 1
                    print(f"      ✅ Visit {visit_num + 1}/{TEST_VISITS_PER_DAY} -> cdt={detail}")
                else:
                    results['failed'] += 1
                    results['by_date'][date_str]['failed'] += 1
                    print(f"      ❌ Visit {visit_num + 1}/{TEST_VISITS_PER_DAY} FAILED: {detail}")
                
                # Small delay to avoid overwhelming the server
                await asyncio.sleep(0.1)
    
    return results


def print_results(results):
    """Print test results summary."""
    print("\n" + "=" * 60)
    print("BACKFILL TEST RESULTS")
    print("=" * 60)
    
    total = results['success'] + results['failed']
    success_rate = (results['success'] / total * 100) if total > 0 else 0
    
    print(f"\n📊 Overall: {results['success']}/{total} visits sent ({success_rate:.1f}% success)")
    
    print("\n📅 By Date:")
    for date_str, counts in results['by_date'].items():
        status = "✅" if counts['failed'] == 0 else "⚠️"
        print(f"   {status} {date_str}: {counts['success']} success, {counts['failed']} failed")
    
    print("\n" + "=" * 60)
    
    if results['failed'] == 0:
        print("✅ ALL TESTS PASSED!")
        print("\n📝 Next Steps:")
        print("   1. Open Matomo at http://localhost:8181")
        print("   2. Go to the site dashboard")
        print("   3. Check the 'Visitors > Visits Log' for the test dates")
        print("   4. Verify visits appear with correct timestamps")
        print(f"   5. Look for 'Backfill Test Page' action names")
    else:
        print("❌ SOME TESTS FAILED")
        print("\n🔧 Troubleshooting:")
        print("   1. Verify MATOMO_TOKEN_AUTH is correct")
        print("   2. Check Matomo logs for errors")
        print("   3. Ensure the token has 'write' permission")
    
    print("=" * 60)


async def main():
    """Main entry point."""
    print("\n🧪 Matomo Backfill Test Script")
    print("   Testing historical data injection with UTC timestamps\n")
    
    # Check configuration
    if not check_config():
        sys.exit(1)
    
    # Test connectivity
    if not await test_matomo_connection():
        print("\n❌ Cannot connect to Matomo. Please check the URL and ensure Matomo is running.")
        sys.exit(1)
    
    # Run backfill test
    results = await run_backfill_test()
    
    # Print results
    print_results(results)
    
    # Exit with appropriate code
    sys.exit(0 if results['failed'] == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())
