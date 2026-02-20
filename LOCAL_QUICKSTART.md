# 🚀 Quick Start Guide - Local Development
## Clinical Trial Data Layer - NVX-1218.22

Get your clinical trial API running locally in under 5 minutes!

---

## 📋 What You'll Get

✅ **SQLite Database** with 17,511 real clinical trial records  
✅ **FastAPI Server** with 20+ REST endpoints  
✅ **Interactive API Docs** at `/docs`  
✅ **Full data access** for 100 subjects across 5 sites

---

## ⚡ Super Quick Start (3 Commands)

```bash
# 1. Navigate to the folder
cd clinical-trial-data-layer

# 2. Create the database (if not already done)
python create_sqlite_db.py

# 3. Start the API server
python api_sqlite.py
```

**That's it!** Your API is running at http://localhost:8000

---

## 📖 Detailed Setup

### Step 1: Install Dependencies

```bash
pip install fastapi uvicorn
```

Or install all at once:
```bash
pip install -r requirements.txt
```

### Step 2: Create the Database

The database might already be included. If not:

```bash
python create_sqlite_db.py
```

This creates `clinical_trial.db` (2.81 MB) with all data.

### Step 3: Start the Server

**Option A: Direct Python**
```bash
python api_sqlite.py
```

**Option B: Using the script**
```bash
./start_local_api.sh
```

**Option C: Using uvicorn directly**
```bash
uvicorn api_sqlite:app --reload --port 8000
```

### Step 4: Test the API

Open your browser:
- **API Root**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **Statistics**: http://localhost:8000/api/statistics

Or use curl:
```bash
curl http://localhost:8000/api/statistics
```

---

## 🧪 Testing the API

Run the test script:
```bash
python test_api.py
```

This tests all major endpoints and confirms everything works.

---

## 📡 Available Endpoints

### Core Data
- `GET /` - API information
- `GET /api/protocol` - Protocol details
- `GET /api/sites` - All sites
- `GET /api/subjects` - All subjects (with filters)
- `GET /api/statistics` - Database statistics

### Subject Data
- `GET /api/subjects/{subject_id}` - Specific subject
- `GET /api/demographics/{subject_id}` - Demographics
- `GET /api/vitals/{subject_id}` - Vital signs
- `GET /api/labs/{subject_id}` - Lab results
- `GET /api/medical-history/{subject_id}` - Medical history
- `GET /api/conmeds/{subject_id}` - Medications
- `GET /api/tumor-assessments/{subject_id}` - Tumor assessments
- `GET /api/ecg/{subject_id}` - ECG results

### Monitoring & Quality
- `GET /api/adverse-events` - Adverse events (with filters)
- `GET /api/deviations` - Protocol deviations
- `GET /api/queries` - Data queries
- `GET /api/visits` - Visit data

---

## 💡 Example API Calls

### Get all serious adverse events
```bash
curl "http://localhost:8000/api/adverse-events?seriousness=Yes"
```

### Get abnormal labs for a subject
```bash
curl "http://localhost:8000/api/labs/101-001?abnormal_only=true"
```

### Get subjects at a specific site
```bash
curl "http://localhost:8000/api/subjects?site_id=101"
```

### Get open protocol deviations
```bash
curl "http://localhost:8000/api/deviations?status=Open"
```

### Get statistics
```bash
curl "http://localhost:8000/api/statistics"
```

---

## 🔧 Configuration

### Change Port
```bash
# Default is 8000, change to 3000:
uvicorn api_sqlite:app --port 3000
```

### Enable Hot Reload (Development)
```bash
uvicorn api_sqlite:app --reload
```

### Allow External Access
```bash
# Access from other devices on your network:
uvicorn api_sqlite:app --host 0.0.0.0
```

---

## 📊 Database Info

**Location**: `clinical_trial.db`  
**Size**: 2.81 MB  
**Type**: SQLite 3  
**Records**: 17,511 across 13 tables

### Browse the Database

**Option 1: DB Browser for SQLite**
- Download: https://sqlitebrowser.org
- Open `clinical_trial.db`
- Browse tables, run queries

**Option 2: Command Line**
```bash
sqlite3 clinical_trial.db

# Inside SQLite:
.tables                    # List all tables
.schema subjects          # Show table structure
SELECT * FROM sites;      # Query data
.exit                     # Exit
```

**Option 3: Python**
```python
import sqlite3
conn = sqlite3.connect('clinical_trial.db')
cur = conn.cursor()
cur.execute("SELECT * FROM sites")
print(cur.fetchall())
```

---

## 🎨 Building a Frontend

Once your API is running, connect any frontend framework:

### React Example
```javascript
const API_URL = 'http://localhost:8000';

fetch(`${API_URL}/api/subjects`)
  .then(res => res.json())
  .then(data => console.log(data));
```

### Vue Example
```javascript
const response = await fetch('http://localhost:8000/api/statistics');
const stats = await response.json();
```

### Plain HTML/JavaScript
```html
<script>
fetch('http://localhost:8000/api/sites')
  .then(res => res.json())
  .then(sites => {
    sites.forEach(site => {
      console.log(site.site_name);
    });
  });
</script>
```

---

## 🐛 Troubleshooting

### "Port already in use"
```bash
# Use a different port:
uvicorn api_sqlite:app --port 8001
```

### "Database not found"
```bash
# Create it:
python create_sqlite_db.py
```

### "Module 'fastapi' not found"
```bash
# Install dependencies:
pip install fastapi uvicorn
```

### "Database is locked"
```bash
# Stop any other processes using the database
# SQLite only allows one writer at a time
```

### Server not responding
```bash
# Check if server is running:
curl http://localhost:8000

# Restart the server:
# Press CTRL+C to stop, then start again
```

---

## 📈 Next Steps

### Local Development
1. ✅ API running locally
2. 📊 Build a dashboard (React/Vue/Angular)
3. 🤖 Add AI monitoring agents
4. 📧 Set up email alerts
5. 📱 Create mobile app

### Cloud Deployment
When ready to deploy:
1. See `CLOUD_DEPLOYMENT.md` for detailed guides
2. Choose Railway, Render, or Fly.io
3. Deploy in 3 clicks
4. Share with your team

---

## 💻 Development Tips

### Auto-reload during development
```bash
uvicorn api_sqlite:app --reload
```
Changes to `api_sqlite.py` automatically restart the server.

### View logs
The server prints all requests to the console.

### Add CORS for specific origins
Edit `api_sqlite.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Your frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 🎯 Quick Commands Reference

```bash
# Create database
python create_sqlite_db.py

# Start server
python api_sqlite.py

# Start with auto-reload
uvicorn api_sqlite:app --reload

# Test API
python test_api.py

# Browse database
sqlite3 clinical_trial.db

# Check database size
ls -lh clinical_trial.db

# View all endpoints
curl http://localhost:8000/docs
```

---

## ✅ Checklist

- [ ] Install Python dependencies
- [ ] Create SQLite database
- [ ] Start API server
- [ ] Test endpoints
- [ ] Browse interactive docs
- [ ] Run test script
- [ ] Build your frontend (optional)
- [ ] Deploy to cloud (optional)

---

## 📞 Support

**Issues?**
- Check `README.md` for full documentation
- See `CLOUD_DEPLOYMENT.md` for deployment help
- Review `DATA_DICTIONARY.md` for data definitions

**Working?** 🎉
- Build your dashboard
- Add AI agents
- Share with your team
- Deploy to cloud when ready

---

**Protocol:** NVX-1218.22  
**Sponsor:** NexaVance Therapeutics Inc.  
**Version:** 1.0

**Happy coding!** 🚀
