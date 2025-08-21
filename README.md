![Trafficinator Logo](logo.png)

# Trafficinator 🦖

Trafficinator is a **load testing tool** built to generate **realistic traffic patterns** for [Matomo](https://matomo.org/).  
It helps you **stress test Matomo’s frontend performance** when handling large datasets in reports, so you can identify bottlenecks and optimize configuration for high-traffic websites.  

---

## 🚀 Features  

- **Realistic traffic simulation**  
  - Generates **3–6 pageviews per visit** with natural timing between requests  
  - Rotates **user agents** and **URLs** to create diverse report data  

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
docker-compose -f docker-compose.loadgen.yml up --build

# View logs in real-time
docker-compose -f docker-compose.loadgen.yml logs -f matomo_loadgen

# Stop the load generator
docker-compose -f docker-compose.loadgen.yml down
```

### Configuration  
Edit `docker-compose.loadgen.yml` to customize your load test:

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

---

## 📊 Example Workflow  

1. **Configure your Matomo instance**  
   ```bash
   # Edit docker-compose.loadgen.yml
   MATOMO_URL: "https://your-matomo-instance.com/matomo.php"
   MATOMO_SITE_ID: "1"
   ```

2. **Generate baseline traffic data**  
   ```bash
   docker-compose -f docker-compose.loadgen.yml up --build
   ```

3. **Monitor and analyze**  
   - Check Matomo reports for performance bottlenecks
   - Identify slow-loading reports (Pages, Visitors, Behavior Flow)
   - Note database query performance and frontend rendering times

4. **Optimize Matomo settings**  
   - Tune archiving processes
   - Optimize database indexing  
   - Adjust caching configuration
   - Configure report segmentation limits

5. **Validate improvements**  
   ```bash
   # Run consistent load test to compare performance
   docker-compose -f docker-compose.loadgen.yml up
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
