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
- Python 3.9+  
- Docker + Docker Compose (optional, recommended for containerized setup)  

### Clone the repo  
```bash
git clone https://github.com/Puttrix/Trafficinator.git
cd Trafficinator
```

### Install dependencies (non-Docker)  
```bash
pip install -r requirements.txt
```

---

## ⚡ Usage  

### Run locally  
```bash
python trafficinator.py --url https://your-matomo-instance.tld --visits 20000 --concurrency 50
```

### Run with Docker  
Build and run directly:  
```bash
docker build -t trafficinator .
docker run --rm trafficinator --url https://your-matomo-instance.tld --visits 20000 --concurrency 50
```

---

## 🐳 Docker Compose Setup  

Create a `docker-compose.yml` in your project folder:  

```yaml
version: "3.9"

services:
  trafficinator:
    build: .
    container_name: trafficinator
    command: >
      python trafficinator.py
      --url https://your-matomo-instance.tld
      --visits 20000
      --concurrency 50
    restart: "no"
```

### Run with Compose  
```bash
docker compose up --build
```

You can also override settings without editing the file:  
```bash
docker compose run --rm trafficinator --url https://analytics.example.com --visits 10000 --concurrency 20
```

---

## 📊 Example Workflow  

1. **Populate reports**  
   ```bash
   docker compose run --rm trafficinator --url https://analytics.example.com --visits 20000 --concurrency 30
   ```
2. **Check Matomo reports** → Identify slow reports (e.g., segments, device reports)  
3. **Optimize settings** → Tune archiving, caching, DB indexing, etc.  
4. **Re-run Trafficinator** → Compare load times before/after  

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
