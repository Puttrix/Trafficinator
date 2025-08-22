![Trafficinator Logo](logo.png)

# Trafficinator 🦖

Trafficinator is a **load testing tool** built to generate **realistic traffic patterns** for [Matomo](https://matomo.org/).  
It helps you **stress test Matomo’s frontend performance** when handling large datasets in reports, so you can identify bottlenecks and optimize configuration for high-traffic websites.  

---

## 🚀 Features  

- **Realistic traffic simulation**  
  - Generates **3–6 pageviews per visit** with natural timing between requests  
  - Rotates **user agents** and **URLs** to create diverse report data  
  - **Site search simulation** with configurable probability and realistic search terms  
  - **Outlinks and downloads tracking** with external URLs and file downloads  
  - **Extended visit durations** of 1-8 minutes for realistic engagement metrics  

- **High-volume traffic**  
  - Configurable to produce **20,000+ visits/day**  
  - Supports **50+ concurrent connections**  

- **Controlled load testing**  
  - Auto-stop options to generate **specific volumes of test data**  
  - Perfect for running **baseline vs optimized comparisons**  

- **Optimization workflow support**  
  1. **Generate baseline data** → Populate reports with realistic traffic  
  2. **Identify bottlenecks** → Observe where reports slow down  
  3. **Apply optimizations** → Adjust Matomo frontend/backend settings  
  4. **Validate improvements** → Re-run consistent load patterns  

---

## 🛠️ Installation  

### Requirements  
- Docker + Docker Compose  
- A running Matomo instance to test against  

### Clone the repo  
```bash
git clone https://github.com/Puttrix/Trafficinator.git
cd Trafficinator
```

The project is fully containerized - no local Python installation needed!

---

## ⚡ Usage  

### Docker Compose (Recommended)  
The project includes a pre-configured Docker Compose setup:

```bash
# Start load generation with default settings
docker-compose up --build

# View logs in real-time
docker-compose logs -f matomo_loadgen

# Stop the load generator
docker-compose down
```

### Configuration  
Edit `docker-compose.yml` to customize your load test:

```yaml
environment:
  MATOMO_URL: "https://your-matomo-instance.com/matomo.php"
  MATOMO_SITE_ID: "1"
  TARGET_VISITS_PER_DAY: "20000"
  PAGEVIEWS_MIN: "3"
  PAGEVIEWS_MAX: "6"
  CONCURRENCY: "50"
  PAUSE_BETWEEN_PVS_MIN: "0.5"
  PAUSE_BETWEEN_PVS_MAX: "2.0"
  AUTO_STOP_AFTER_HOURS: "24"     # Stop after N hours (0 = disabled)
  MAX_TOTAL_VISITS: "0"           # Stop after N visits (0 = disabled)
  SITESEARCH_PROBABILITY: "0.15"  # Probability (0-1) that a visit includes site search
  VISIT_DURATION_MIN: "1.0"       # Minimum visit duration in minutes
  VISIT_DURATION_MAX: "8.0"       # Maximum visit duration in minutes
  OUTLINKS_PROBABILITY: "0.10"    # Probability (0-1) that a visit includes outlinks
  DOWNLOADS_PROBABILITY: "0.08"   # Probability (0-1) that a visit includes downloads
```

### URL Structure  
The load generator uses a **3-level hierarchical URL structure** from `config/urls.txt`:
- **10 main categories**: products, blog, support, company, resources, news, services, solutions, documentation, community
- **5 subcategories each**: e.g., products → hardware, software, accessories, bundles, enterprise  
- **40 pages per subcategory**: 2,000 total URLs for comprehensive testing

This creates realistic navigation patterns that will generate rich data in Matomo's:
- Page hierarchy reports
- Behavior flow analysis  
- Content performance metrics
- URL structure insights

### Site Search Simulation
The load generator includes **realistic site search behavior**:
- **Configurable probability**: Set `SITESEARCH_PROBABILITY` (0.0-1.0) to control how many visits include searches
- **35 realistic search terms**: Including 'product', 'support', 'documentation', 'pricing', 'features', etc.
- **Search categories**: Random assignment to Products, Support, Documentation categories (30% probability)
- **Result counts**: Simulates 0-25 search results per query
- **Natural placement**: Search events occur randomly within visit pageviews

This generates comprehensive data for Matomo's site search analytics, helping you test and optimize search-related reports and performance.

### Outlinks and Downloads Simulation
The load generator includes **realistic outlinks and download behavior**:
- **Outlinks (10% probability)**: Clicks to external websites including:
  - Tech sites: GitHub, Stack Overflow, MDN, W3C
  - Frameworks: React, Vue, Angular, Node.js, jQuery, Bootstrap  
  - Design resources: Tailwind CSS, Font Awesome, Unsplash, Google Fonts
  - Social platforms: YouTube, Twitter, LinkedIn, Facebook, Instagram, Reddit, Medium
- **Downloads (8% probability)**: File downloads including:
  - Documents: PDFs (manuals, guides, whitepapers), presentations, spreadsheets
  - Software: ZIP files, installers, mobile apps, source code
  - Assets: Images, logos, configurations, backups
- **Smart placement**: Events occur randomly within visit pageviews for natural behavior
- **Extended visit duration**: Configurable 1-8 minute visits simulate realistic user engagement

This generates data for Matomo's **Behavior** → **Outlinks** and **Behavior** → **Downloads** reports, providing insights into user interaction with external content and file downloads.

### Debugging outlinks & downloads

If you don't see outlinks or downloads in Matomo, use the included debug helpers:

- `matomo-load-baked/debug_build_requests.py` — builds and prints the exact Matomo request URLs for a few simulated visits (no network). Good for quick inspection.
- Runtime debug: enable debug logging and limit visits so you can watch requests in the container logs.

Example quick test (runs a short load and exits):

```bash
# Run with verbose logs and stop after 50 visits
LOG_LEVEL=DEBUG MAX_TOTAL_VISITS=50 CONCURRENCY=5 docker compose up --build --abort-on-container-exit

# After run: check visitor log / Outlinks / Downloads in Matomo and container logs
docker compose logs matomo_loadgen
```

If outlinks/downloads still don't appear in Matomo, check the Matomo server access logs for `matomo.php` requests and verify the querystring contains `link=` or `download=` and a `urlref=` parameter.

### Behavior guarantees

The load generator now enforces a few guarantees that help Matomo classify events correctly:

- Outlinks, Downloads and Site Search will never be the *first* action in a visit. A regular pageview always precedes any of these events (when the visit contains multiple pageviews).
- For outlink and download hits the generator sets `urlref` to the page URL that contained the link/download. This improves Matomo's ability to attribute and display the click/download in the Outlinks/Downloads reports.
- Download entries that are configured as relative paths are converted to fully-qualified URLs using the page's base URL before being sent to Matomo.

These changes are implemented in `matomo-load-baked/loader.py`. Use the debug script and container logs (see above) to verify requests include `urlref`, `link`, or `download` as expected.

### Extended Visit Duration
The load generator simulates **realistic visit durations** to create more accurate engagement metrics:
- **Configurable duration range**: Set `VISIT_DURATION_MIN` and `VISIT_DURATION_MAX` in minutes (default: 1-8 minutes)
- **Smart timing calculation**: Total visit duration includes time spent between pageviews plus additional engagement time
- **Natural behavior simulation**: Users appear to stay on the site after their last pageview, simulating content consumption
- **Flexible configuration examples**:
  - Quick browsing: `1.0-3.0` minutes
  - Normal engagement: `2.0-8.0` minutes (default: `1.0-8.0`)
  - Deep engagement: `5.0-15.0` minutes

This creates realistic **session duration data** in Matomo's visitor reports, helping you analyze user engagement patterns and optimize for longer visits.

### Matomo Site Search Configuration
**Important:** You must enable Site Search tracking in Matomo to see the search data generated by Trafficinator.

#### Step 1: Enable Site Search Tracking
1. Go to **Administration** → **Websites** → **Manage** in your Matomo dashboard
2. Click the **Settings** button for your website
3. Scroll down to the **Site Search** section
4. Change the dropdown from "Do not track Site Search" to **"Site Search tracking enabled"**

#### Step 2: Configure Search Parameters
Choose one of these options:

**Option A (Recommended):** Use default parameters
- Check the box for **"Use default Site Search parameters"**
- Matomo includes `search` in the default parameters

**Option B:** Custom parameters  
- Leave the checkbox unchecked
- In the **"Query parameter"** field, enter: `search`
- In the **"Category parameter"** field, enter: `search_cat`

#### Step 3: Save and View Reports
1. Click **Save** to apply the changes
2. After running Trafficinator, view site search data in:
   - **Behavior** → **Site Search** → **Search Keywords**
   - **Behavior** → **Site Search** → **Search Categories**
   - **Behavior** → **Site Search** → **No Result Keywords**

**Note:** Search events won't appear as regular pageviews - they'll show up specifically in Site Search reports.

---

## 📊 Example Workflow  

1. **Configure your Matomo instance**  
   ```bash
   # Edit docker-compose.yml
   MATOMO_URL: "https://your-matomo-instance.com/matomo.php"
   MATOMO_SITE_ID: "1"
   ```

2. **Enable Site Search in Matomo** (if using site search feature)
   - Follow the [Matomo Site Search Configuration](#matomo-site-search-configuration) steps above
   - This is required to see search data in reports

3. **Generate baseline traffic data**  
   ```bash
   docker-compose up --build
   ```

4. **Monitor and analyze**  
   - Check Matomo reports for performance bottlenecks
   - Identify slow-loading reports (Pages, Visitors, Behavior Flow, Site Search, Outlinks, Downloads)
   - Note database query performance and frontend rendering times
   - Review comprehensive analytics: site search, outlinks, downloads, session duration, engagement metrics

5. **Optimize Matomo settings**  
   - Tune archiving processes
   - Optimize database indexing  
   - Adjust caching configuration
   - Configure report segmentation limits

6. **Validate improvements**  
   ```bash
   # Run consistent load test to compare performance
   docker-compose up
   ```  

---

## 🤝 Contributing  

Pull requests and issue reports are welcome!  
If you’d like to add new traffic patterns, extend report dimensions, or improve scaling, feel free to contribute.  

---

## 📜 License  

MIT License – free to use, modify, and share.  

---

## 👤 Author  

Developed by **[Putte Arvfors](https://github.com/Puttrix)**  
