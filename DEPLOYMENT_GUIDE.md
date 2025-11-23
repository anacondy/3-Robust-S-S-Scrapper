# Deployment Guide - Platform-Specific Instructions

This guide provides detailed, step-by-step instructions for deploying the Subodh Student Hub scraper on various hosting platforms.

## Table of Contents
- [GitHub Pages (Recommended)](#github-pages-recommended)
- [Heroku](#heroku)
- [PythonAnywhere](#pythonanywhere)
- [Render](#render)
- [Vercel](#vercel)
- [Railway](#railway)
- [Google Cloud Run](#google-cloud-run)
- [Troubleshooting](#troubleshooting)

---

## GitHub Pages (Recommended)

**Best For**: Free hosting, automatic updates, static sites with scheduled scraping

### Prerequisites
- GitHub account
- Repository with the code

### Files Used
- `.github/workflows/scrape-and-deploy.yml` - Workflow automation
- `scraper.py` - Data collection script
- `templates/index.html` - Web interface
- `data.json` - Scraped data
- `requirements.txt` - Python dependencies

### Setup Instructions

1. **Enable GitHub Pages**
   ```
   Repository → Settings → Pages → Source: "GitHub Actions"
   ```

2. **Enable GitHub Actions**
   ```
   Repository → Settings → Actions → General → "Allow all actions"
   ```

3. **Trigger First Deployment**
   - Push code to main branch, OR
   - Go to Actions tab → "Scrape and Deploy to GitHub Pages" → "Run workflow"

4. **Access Your Site**
   ```
   https://[your-username].github.io/3-Robust-S-S-Scrapper/
   ```

### How It Works
1. GitHub Actions runs daily at 3:07 AM UTC
2. Workflow executes `scraper.py` to fetch fresh data
3. Data is saved to `data.json`
4. Files are copied to `docs/` folder
5. GitHub Pages serves the static site
6. Changes are committed back to repository

### Customization

**Change Schedule Time**
Edit `.github/workflows/scrape-and-deploy.yml`:
```yaml
schedule:
  - cron: '7 3 * * *'  # minute hour day month day-of-week
  # Examples:
  # '0 0 * * *'   - Midnight UTC daily
  # '0 */6 * * *' - Every 6 hours
  # '30 2 * * 1'  - 2:30 AM every Monday
```

**Change GitHub Pages Source Branch**
If you want to deploy from a different branch, update the workflow to push to that branch.

### Advantages
✅ Completely free with unlimited bandwidth
✅ Automatic HTTPS
✅ GitHub Actions provides 2,000 free minutes/month
✅ Fast global CDN
✅ No server management required

### Limitations
❌ Static site only (no server-side processing)
❌ Workflow runs only when triggered or scheduled
❌ 1GB repository size limit

---

## Heroku

**Best For**: Dynamic Flask applications, easy deployment

### Prerequisites
- Heroku account (free tier available)
- Heroku CLI installed
- Git

### Files Required
- `Procfile` ✅ Already included
- `runtime.txt` ✅ Already included
- `requirements.txt` ✅ Already included
- `app.py` - Flask application

### What Each File Does

**`Procfile`**
```
web: gunicorn app:app
```
- Tells Heroku to start a web process
- Uses Gunicorn (production WSGI server) instead of Flask's dev server
- `app:app` means import `app` from `app.py` file

**`runtime.txt`**
```
python-3.10.12
```
- Specifies exact Python version
- Heroku uses this to set up the environment
- Must be a version supported by Heroku

**`requirements.txt`**
- Lists all Python packages needed
- Heroku runs `pip install -r requirements.txt` during build

### Deployment Steps

1. **Install Heroku CLI**
   ```bash
   # macOS
   brew tap heroku/brew && brew install heroku
   
   # Windows
   # Download from: https://devcenter.heroku.com/articles/heroku-cli
   
   # Ubuntu/Debian
   curl https://cli-assets.heroku.com/install.sh | sh
   ```

2. **Login to Heroku**
   ```bash
   heroku login
   ```

3. **Create Heroku App**
   ```bash
   cd /path/to/3-Robust-S-S-Scrapper
   heroku create subodh-hub  # Choose your app name
   ```

4. **Deploy**
   ```bash
   git push heroku main
   ```
   If your branch is named differently:
   ```bash
   git push heroku your-branch-name:main
   ```

5. **Open App**
   ```bash
   heroku open
   ```

### Setting Up Scheduled Scraping

1. **Install Scheduler Add-on**
   ```bash
   heroku addons:create scheduler:standard
   ```

2. **Configure Schedule**
   ```bash
   heroku addons:open scheduler
   ```
   
3. **Add Job**
   - Command: `python scraper.py`
   - Frequency: Daily at 3:07 AM (closest available time)

### Managing Your Heroku App

**View Logs**
```bash
heroku logs --tail
```

**Restart App**
```bash
heroku restart
```

**Set Environment Variables**
```bash
heroku config:set VARIABLE_NAME=value
```

**Check App Status**
```bash
heroku ps
```

### Heroku Costs
- **Free Tier**: 550-1000 free dyno hours/month
- **Eco Dyno**: $5/month (replaces free tier for new apps)
- **Scheduler Add-on**: Free for up to 50 jobs/month

---

## PythonAnywhere

**Best For**: Python developers, easy Python hosting, scheduled tasks included

### Prerequisites
- PythonAnywhere account (free tier available)
- All project files

### Files Used
- All files in repository
- No special configuration files needed

### What Makes It Work

**`app.py`**
- Contains Flask application
- PythonAnywhere's WSGI config will import from this

**`requirements.txt`**
- You'll install these via command line
- PythonAnywhere doesn't auto-install

### Deployment Steps

1. **Create PythonAnywhere Account**
   - Go to [pythonanywhere.com](https://www.pythonanywhere.com)
   - Sign up for free account

2. **Upload Code**
   
   **Option A: Git Clone (Recommended)**
   - Go to "Consoles" → "Bash"
   ```bash
   git clone https://github.com/your-username/3-Robust-S-S-Scrapper.git
   cd 3-Robust-S-S-Scrapper
   ```
   
   **Option B: Upload Files**
   - Go to "Files" tab
   - Upload all files manually

3. **Create Virtual Environment**
   ```bash
   cd ~/3-Robust-S-S-Scrapper
   python3.10 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Configure Web App**
   - Go to "Web" tab
   - Click "Add a new web app"
   - Choose "Manual configuration"
   - Python version: 3.10
   
5. **Set Paths**
   - Source code: `/home/yourusername/3-Robust-S-S-Scrapper`
   - Working directory: `/home/yourusername/3-Robust-S-S-Scrapper`
   - Virtual env: `/home/yourusername/3-Robust-S-S-Scrapper/venv`

6. **Configure WSGI File**
   Click on WSGI configuration file link and replace contents with:
   ```python
   import sys
   import os
   
   # Add project directory
   path = '/home/yourusername/3-Robust-S-S-Scrapper'
   if path not in sys.path:
       sys.path.insert(0, path)
   
   # Activate virtual environment
   activate_this = '/home/yourusername/3-Robust-S-S-Scrapper/venv/bin/activate_this.py'
   with open(activate_this) as file:
       exec(file.read(), dict(__file__=activate_this))
   
   # Import Flask app
   from app import app as application
   ```

7. **Reload Web App**
   Click the big green "Reload" button

8. **Access Your Site**
   ```
   https://yourusername.pythonanywhere.com
   ```

### Setting Up Scheduled Scraping

1. **Go to Tasks Tab**
2. **Create Scheduled Task**
   - Time: 03:07 (24-hour format)
   - Command:
   ```bash
   /home/yourusername/3-Robust-S-S-Scrapper/venv/bin/python /home/yourusername/3-Robust-S-S-Scrapper/scraper.py
   ```

### PythonAnywhere Tips

**Update Code from Git**
```bash
cd ~/3-Robust-S-S-Scrapper
git pull
# Then click "Reload" button on Web tab
```

**View Logs**
- Web tab → Log files → Error log, Server log

**Free Tier Limitations**
- One web app
- Daily scheduled task execution time resets
- Limited CPU time
- No HTTPS on custom domains (HTTPS on pythonanywhere subdomain)

---

## Render

**Best For**: Modern deployment, automatic GitHub integration

### Prerequisites
- Render account
- GitHub repository

### Files Required
- `render.yaml` ✅ Already included
- `requirements.txt` ✅ Already included
- `app.py` - Flask application

### What `render.yaml` Does
```yaml
services:
  - type: web           # Creates a web service
    name: subodh-hub    # Service name
    env: python         # Python environment
    buildCommand: pip install -r requirements.txt  # How to build
    startCommand: gunicorn app:app                  # How to start
    envVars:
      - key: PYTHON_VERSION
        value: 3.10.12  # Python version to use
```

### Deployment Steps

1. **Connect GitHub to Render**
   - Go to [render.com](https://render.com)
   - Sign up/login with GitHub

2. **Create New Web Service**
   - Dashboard → "New" → "Web Service"
   - Connect repository
   - Render auto-detects `render.yaml`

3. **Configure (Auto-filled from render.yaml)**
   - Name: subodh-hub
   - Environment: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`

4. **Deploy**
   - Click "Create Web Service"
   - Render automatically builds and deploys

5. **Access Your Site**
   ```
   https://subodh-hub.onrender.com
   ```

### Scheduled Scraping on Render

**Option 1: Cron Jobs (Paid)**
- Render Cron Jobs cost $1/month
- Can run any command on schedule

**Option 2: GitHub Actions (Free - Recommended)**
- Use existing `.github/workflows/scrape-and-deploy.yml`
- Modify to commit data.json back to repo
- Render auto-deploys on git push

### Render Free Tier
- 750 hours/month free
- Apps spin down after 15 min inactivity
- Spin up takes ~30 seconds

---

## Vercel

**Best For**: Serverless deployment, frontend-heavy apps

### Prerequisites
- Vercel account
- GitHub repository

### Files Required
- `vercel.json` ✅ Already included
- `requirements.txt` ✅ Already included
- `app.py` - Flask application

### What `vercel.json` Does
```json
{
  "builds": [
    {
      "src": "app.py",           # Source file
      "use": "@vercel/python"    # Python builder
    }
  ],
  "routes": [
    {
      "src": "/(.*)",            # All routes
      "dest": "app.py"           # Go to app.py
    }
  ]
}
```

### Deployment Steps

1. **Install Vercel CLI**
   ```bash
   npm install -g vercel
   ```

2. **Deploy**
   ```bash
   cd /path/to/3-Robust-S-S-Scrapper
   vercel
   ```

3. **Follow Prompts**
   - Set up and deploy: Yes
   - Which scope: Your account
   - Link to existing project: No
   - Project name: subodh-hub
   - Directory: ./
   - Override settings: No

4. **Access Your Site**
   Vercel provides URL like:
   ```
   https://subodh-hub.vercel.app
   ```

### Alternative: GitHub Integration

1. Go to [vercel.com](https://vercel.com)
2. "Import Project" → Select GitHub repo
3. Vercel auto-detects and deploys

### Scheduled Scraping
Vercel doesn't have built-in cron jobs. Use GitHub Actions (already configured) to update data.

---

## Railway

**Best For**: Simple deployment, modern platform

### Prerequisites
- Railway account
- GitHub repository

### Files Required
- Just push your code! Railway auto-detects Flask apps
- Uses `requirements.txt` and `app.py`

### Deployment Steps

1. **Create Railway Account**
   - Go to [railway.app](https://railway.app)
   - Sign up with GitHub

2. **Create New Project**
   - Dashboard → "New Project"
   - "Deploy from GitHub repo"
   - Select `3-Robust-S-S-Scrapper`

3. **Auto-Detection**
   - Railway detects Python
   - Automatically installs dependencies
   - Starts Flask app

4. **Generate Domain**
   - Settings → Generate Domain
   - Access your site at generated URL

### Scheduled Scraping
Use GitHub Actions (already configured) - Railway auto-deploys on git push.

---

## Google Cloud Run

**Best For**: Enterprise deployment, auto-scaling

### Prerequisites
- Google Cloud account
- gcloud CLI installed
- Docker knowledge helpful

### Files Required
- `Dockerfile` ✅ Already included
- `requirements.txt` ✅ Already included
- `app.py` - Flask application

### What `Dockerfile` Does
```dockerfile
FROM python:3.10-slim          # Base image
WORKDIR /app                   # Set working directory
COPY requirements.txt .        # Copy dependencies
RUN pip install ...            # Install dependencies
COPY . .                       # Copy all files
CMD exec gunicorn ...          # Start command
```

### Deployment Steps

1. **Install gcloud CLI**
   ```bash
   # macOS
   curl https://sdk.cloud.google.com | bash
   
   # Initialize
   gcloud init
   ```

2. **Deploy to Cloud Run**
   ```bash
   cd /path/to/3-Robust-S-S-Scrapper
   gcloud run deploy subodh-hub \
     --source . \
     --region us-central1 \
     --allow-unauthenticated
   ```

3. **Access Your Site**
   gcloud provides URL like:
   ```
   https://subodh-hub-xxxxx-uc.a.run.app
   ```

### Scheduled Scraping

Use Cloud Scheduler:
```bash
gcloud scheduler jobs create http scraper-job \
  --schedule="7 3 * * *" \
  --uri="https://your-app-url.run.app/api/refresh" \
  --http-method=GET
```

---

## Troubleshooting

### Common Issues Across Platforms

**Issue: `ModuleNotFoundError: No module named 'flask'`**
- **Cause**: Dependencies not installed
- **Solution**: Ensure `requirements.txt` is present and properly formatted

**Issue: Port binding errors**
- **Cause**: App trying to bind to wrong port
- **Solution**: Most platforms provide PORT env variable
  ```python
  port = int(os.environ.get('PORT', 5000))
  app.run(host='0.0.0.0', port=port)
  ```

**Issue: Scraper fails with SSL errors**
- **Cause**: Target website has SSL certificate issues
- **Solution**: Already handled with `verify=False` in scraper

**Issue: 502 Bad Gateway**
- **Cause**: App crashed or not starting
- **Solution**: Check logs for errors

### Platform-Specific Issues

**GitHub Pages**
- **Issue**: Changes not appearing
- **Solution**: Check Actions tab for errors, clear browser cache

**Heroku**
- **Issue**: App sleeping
- **Solution**: Upgrade to paid dyno or use a service to ping it

**PythonAnywhere**
- **Issue**: WSGI configuration errors
- **Solution**: Double-check paths in WSGI file match your username

**Vercel**
- **Issue**: Serverless function timeout
- **Solution**: Optimize scraper or use background job

---

## Performance Optimization

### For All Platforms

1. **Enable Caching**
   - Data already cached in `data.json`
   - Scraper runs once daily, not on every request

2. **Minimize Dependencies**
   - Only install what's needed
   - Current dependencies are optimized

3. **Use Production WSGI Server**
   - Gunicorn already configured
   - Don't use Flask dev server in production

4. **Monitor Performance**
   - Check platform-specific metrics
   - Set up error alerts

---

## Security Best Practices

1. **Never Commit Secrets**
   - Use environment variables for sensitive data
   - Add to `.gitignore`

2. **Keep Dependencies Updated**
   ```bash
   pip list --outdated
   pip install --upgrade package-name
   ```

3. **Use HTTPS**
   - All platforms provide free HTTPS
   - Never disable SSL verification except for known issues

4. **Rate Limiting**
   - Current setup scrapes once daily
   - Respects target server

---

## Comparison Summary

| Platform | Free Tier | Setup Time | Best For |
|----------|-----------|------------|----------|
| **GitHub Pages** | ✅ Unlimited | 5 min | Static sites, automation |
| **Heroku** | ⚠️ Limited | 10 min | Quick Flask deployment |
| **PythonAnywhere** | ✅ Good | 15 min | Python-focused projects |
| **Render** | ✅ 750hrs | 5 min | Modern apps |
| **Vercel** | ✅ Generous | 5 min | Frontend-heavy |
| **Railway** | ✅ 500hrs | 3 min | Simplest deployment |
| **Google Cloud** | ⚠️ Credits | 20 min | Enterprise needs |

**Our Recommendation**: Use **GitHub Pages** (current setup) for the best balance of features, reliability, and cost (free!).

---

## Need Help?

- Check main README.md for general information
- Review platform-specific documentation
- Open an issue on GitHub
- Check platform status pages if service is down

---

**Last Updated**: November 2025
