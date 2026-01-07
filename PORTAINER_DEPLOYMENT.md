# Trafficinator Control UI - Portainer Deployment Guide

## 🎯 Problem Summary

You're seeing "Failed to initialize application" because:
1. The published Docker image (`ghcr.io/puttrix/trafficinator:latest`) **only contains the load generator**
2. Your current Portainer stack doesn't include the Control UI service
3. The Control UI needs to be built from source (includes the fixed config.js)

## ✅ Solution: Deploy Complete Stack

You need to update your Portainer stack to **include the Control UI service** which will be built directly from GitHub with the latest bug fixes.

---

## 📋 Step-by-Step Instructions

### **Step 1: Open Portainer**

1. Navigate to your Portainer web interface
2. Log in if needed

### **Step 2: Go to Your Stack**

1. Click **Stacks** in the left sidebar
2. Find your Trafficinator stack
3. Click on the stack name

### **Step 3: Edit the Stack**

1. Click the **Editor** button at the top
2. You'll see your current compose file

### **Step 4: Replace Stack Content**

1. **Select all** the current content (Ctrl+A / Cmd+A)
2. **Delete** it
3. **Copy** the complete stack from: `/tmp/portainer-stack-with-ui.yml`
4. **Paste** into the Portainer editor

### **Step 5: Set Environment Variables**

Scroll down below the editor to the **Environment variables** section.

**Add these variables:**

```
MATOMO_URL=https://matomo.surputte.se/matomo.php
MATOMO_SITE_ID=1
MATOMO_TOKEN_AUTH=your-actual-matomo-token-here
CONTROL_UI_API_KEY=change-this-to-a-strong-secret-key
TIMEZONE=Europe/Stockholm
ECOMMERCE_CURRENCY=SEK
```

**Generate a strong API key:**
```bash
# On your server or local machine:
openssl rand -base64 32
```

### **Step 6: Deploy the Stack**

1. Scroll to the bottom
2. Enable these options:
   - ☑ **"Pull latest image version"** (optional)
   - ☑ **"Re-deploy stack"**
3. Click **"Update the stack"** button

### **Step 7: Wait for Build**

**This will take 2-3 minutes** because Portainer is:
1. Cloning the GitHub repository
2. Building the Control UI image from source
3. Starting both containers

**Monitor progress:**
- Go to **Containers** in the left sidebar
- You'll see both containers:
  - `trafficinator-control-ui` - Building/Starting
  - `matomo-loadgen` - Waiting for Control UI

### **Step 8: Verify Deployment**

Once both containers show **Status: Running**:

1. Click **trafficinator-control-ui** container
2. Click **Logs** button
3. Should see:
   ```
   INFO:     Started server process
   INFO:     Waiting for application startup.
   INFO:     Application startup complete.
   INFO:     Uvicorn running on http://0.0.0.0:8000
   ```

---

## 🌐 Access the Control UI

### **Option A: Direct Server IP**

Open in your browser:
```
http://YOUR_SERVER_IP:8000/ui
```

### **Option B: Via Cloudflare Tunnel**

If you have Cloudflare Tunnel configured:
```
https://trafficinator.yourdomain.com/ui
```

**You'll need to configure the tunnel to route to `trafficinator-control-ui:8000`**

---

## ✅ Verification Checklist

After deploying, verify:

### 1. **Containers are Running**

**Portainer → Containers**

- ✅ `trafficinator-control-ui` - Status: Running (Healthy)
- ✅ `matomo-loadgen` - Status: Running

### 2. **UI Loads Successfully**

Open: `http://your-server-ip:8000/ui`

- ✅ Page loads without "Failed to initialize" error
- ✅ All tabs visible (Status, Configuration, Backfill, etc.)
- ✅ No errors in browser console (F12 → Console)

### 3. **Browser Console is Clean**

Press **F12** → **Console** tab

Should see:
```
✅ Initializing Matomo Load Generator Control UI...
✅ Application initialized successfully
```

**No errors about:**
- ❌ `isBackfillInput`
- ❌ `ConfigForm`
- ❌ `Failed to initialize`

### 4. **API Key Authentication**

If you see "Unauthenticated" in the UI:

1. Click the **gear icon** (⚙️) in the top-right
2. Enter your `CONTROL_UI_API_KEY` value
3. Click **Save**
4. Page should reload and show authenticated state

---

## 🔧 Troubleshooting

### Issue: "Build Failed" Error

**Possible causes:**
- GitHub is down or unreachable from your server
- Docker doesn't have internet access
- Insufficient disk space

**Solution:**
```bash
# Check Docker can reach GitHub
docker run --rm curlimages/curl:latest https://github.com/Puttrix/Trafficinator.git

# Check disk space
df -h
```

### Issue: Container Keeps Restarting

**Check logs:**

**Portainer → Containers → trafficinator-control-ui → Logs**

Common issues:
1. **Port 8000 already in use:**
   - Change port mapping in stack: `"8080:8000"`
   - Access via: `http://server-ip:8080/ui`

2. **Docker socket permission denied:**
   - Ensure `/var/run/docker.sock` is mounted
   - Check Docker socket permissions on host

3. **Python errors:**
   - Usually means dependencies failed to install during build
   - Try rebuilding: Delete stack → Recreate

### Issue: Still Shows "Failed to initialize"

**Steps:**

1. **Clear browser cache:**
   - Hard refresh: `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)
   - Or open incognito/private window

2. **Verify file in container:**
   ```bash
   # SSH to server
   docker exec trafficinator-control-ui cat /app/control-ui/static/js/config.js | grep -c "const isBackfillInput"
   ```
   Should return: `1` (only one occurrence)

3. **Check if using old cache:**
   - Add `?v=999` to URL: `http://server-ip:8000/ui?v=999`
   - This bypasses cache

### Issue: Can't Access from Browser

**Check firewall:**
```bash
# On server
sudo ufw status
sudo ufw allow 8000/tcp

# Or if using firewalld
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload
```

**Check container is listening:**
```bash
docker exec trafficinator-control-ui netstat -tuln | grep 8000
```

### Issue: "Cannot connect to Docker daemon"

**The Control UI needs Docker socket access to control containers.**

Verify in stack YAML:
```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock
```

If still fails:
```bash
# Check Docker socket exists
ls -la /var/run/docker.sock

# Check permissions
sudo chmod 666 /var/run/docker.sock  # Temporary fix
```

---

## 🔐 Security Notes

### For Production Deployment:

1. **Change API Key:**
   ```bash
   openssl rand -base64 32
   ```
   Update in Portainer environment variables

2. **Restrict CORS:**
   ```
   CORS_ORIGINS=https://trafficinator.yourdomain.com
   ```

3. **Use HTTPS:**
   - Configure Cloudflare Tunnel
   - Or use reverse proxy (Nginx Proxy Manager, Traefik)

4. **Don't expose port 8000 directly:**
   - Remove `ports:` section from control-ui service
   - Access only via Cloudflare Tunnel or reverse proxy

---

## 📊 What This Deployment Includes

**Services:**
- ✅ `control-ui` - Web UI with all bug fixes (built from GitHub)
- ✅ `matomo-loadgen` - Load generator (from GHCR image)

**Volumes:**
- `control-ui-data` - Presets, URLs, funnels, backfill history
- `loadgen-data` - Shared data, start signals

**Networks:**
- `trafficinator` - Bridge network for inter-container communication

**Features:**
- ✅ Fixed JavaScript bugs
- ✅ Latest backfill functionality
- ✅ URL/Event/Funnel management
- ✅ Real-time status dashboard
- ✅ Container control (start/stop/restart)

---

## 🆘 Need More Help?

If you're still having issues:

1. **Export container logs:**
   ```bash
   docker logs trafficinator-control-ui > /tmp/control-ui.log 2>&1
   docker logs matomo-loadgen > /tmp/loadgen.log 2>&1
   ```

2. **Screenshot browser console errors** (F12 → Console)

3. **Share your Portainer stack YAML** (remove secrets first!)

4. **Create a GitHub issue:**
   https://github.com/Puttrix/Trafficinator/issues

---

## ✅ Success Indicators

You'll know it's working when:

1. ✅ Both containers show "Running (Healthy)" in Portainer
2. ✅ UI loads at `http://server-ip:8000/ui`
3. ✅ No errors in browser console
4. ✅ Status dashboard shows load generator status
5. ✅ Can start/stop load generator from UI
6. ✅ All tabs (Configuration, Backfill, URLs, Events, Funnels) work

---

**Ready to deploy?** Follow Steps 1-8 above to get your Control UI running with the fix!
