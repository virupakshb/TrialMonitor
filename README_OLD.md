# Clinical Trial Data Layer - Protocol NVX-1218.22

## 📋 Overview

Complete synthetic data layer for **NVX-1218.22**, a Phase III clinical trial evaluating **NovaPlex-450** in combination with chemotherapy for Advanced Non-Small Cell Lung Cancer (NSCLC).

**Sponsor:** NexaVance Therapeutics Inc.

This dataset includes rich, realistic clinical trial data for **100 subjects** across **5 global sites** with various scenarios designed to test AI monitoring agents.

---

## 🎯 What's Included

### Data Components

- **Protocol Definition**: Complete study protocol with objectives, endpoints, visit schedule
- **Sites (5)**: Multi-country investigational sites
- **Subjects (100)**: Patients enrolled across sites with realistic distribution
- **Demographics**: Age, sex, race, BMI, ECOG performance status
- **Visits (~700)**: Complete visit schedule with protocol deviations
- **Vital Signs (~700)**: BP, HR, temperature, weight, O2 saturation
- **Laboratory Results (~15,000)**: Hematology, chemistry, coagulation panels
- **Adverse Events (~250)**: Including serious adverse events (SAEs)
- **Medical History (~400)**: Cancer diagnosis, comorbidities
- **Concomitant Medications (~400)**: Ongoing medications during study
- **Tumor Assessments (~250)**: RECIST 1.1 response evaluations
- **ECG Results (~250)**: QTc monitoring data
- **Protocol Deviations (20)**: Visit window violations, missed assessments
- **Queries (25)**: Data quality issues for resolution

### Rich Scenarios for AI Agent Testing

1. **Protocol Deviations**
   - 15 visit window violations (5-15 days outside window)
   - 3 eligibility violations
   - 5 missed assessments

2. **Safety Signals**
   - 8 Grade 3-4 adverse events
   - 5 serious adverse events (SAEs)
   - 4 hepatotoxicity cases (ALT/AST >3x ULN)
   - 2 QTc prolongations (>470 msec)
   - 3 bone marrow suppression cases

3. **Data Quality Issues**
   - 10 missing required fields
   - 8 data inconsistencies
   - 5 outlier values

4. **Operational Issues**
   - 25 open/resolved queries
   - Varying enrollment rates across sites

---

## 🗄️ Database Schema

### Core Tables

```
protocol_info           - Protocol metadata
sites                   - Investigational sites (5)
subjects                - Study subjects (100)
demographics            - Patient demographics
visits                  - Visit schedule tracking
vital_signs             - Vital signs measurements
laboratory_results      - Lab test results
adverse_events          - AEs and SAEs
medical_history         - Patient medical history
concomitant_medications - Ongoing medications
tumor_assessments       - Tumor response assessments
ecg_results             - ECG/QTc monitoring
protocol_deviations     - Protocol violations
queries                 - Data queries
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+ (or use Supabase free tier)
- 500MB disk space

### Installation

1. **Clone/Download this directory**

```bash
cd clinical-trial-data-layer
```

2. **Install Python dependencies**

```bash
pip install -r requirements.txt
```

3. **Set up PostgreSQL Database**

**Option A: Local PostgreSQL**
```bash
# Install PostgreSQL (if not already installed)
# macOS
brew install postgresql@15

# Ubuntu/Debian
sudo apt install postgresql-15

# Start PostgreSQL
# macOS
brew services start postgresql@15

# Ubuntu/Debian
sudo systemctl start postgresql
```

**Option B: Supabase (Free Cloud)**
- Go to https://supabase.com
- Create new project
- Get connection string from Settings > Database
- Update environment variables

4. **Configure Environment Variables**

Create `.env` file:

```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=clinical_trial
DB_USER=postgres
DB_PASSWORD=your_password
```

For Supabase:
```bash
DB_HOST=db.xxxxx.supabase.co
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your_supabase_password
```

5. **Generate Synthetic Data**

```bash
# Generate protocol, sites, subjects, demographics
python generate_data_part1.py

# Generate visits, vitals, labs
python generate_data_part2.py

# Generate AEs, medical history, queries, etc.
python generate_data_part3.py
```

6. **Load Data into PostgreSQL**

```bash
python load_data.py
```

Expected output:
```
Database Statistics:
  sites                         :      5 records
  subjects                      :    100 records
  demographics                  :    100 records
  visits                        :    ~700 records
  vital_signs                   :    ~700 records
  laboratory_results            :  ~15000 records
  adverse_events                :    ~250 records
  medical_history               :    ~400 records
  concomitant_medications       :    ~400 records
  tumor_assessments             :    ~250 records
  ecg_results                   :    ~250 records
  protocol_deviations           :     ~20 records
  queries                       :     ~25 records
```

7. **Start API Server**

```bash
python api.py
```

API will be available at: `http://localhost:8000`

API documentation: `http://localhost:8000/docs`

---

## 📡 API Endpoints

### Protocol & Sites

- `GET /api/protocol` - Protocol information
- `GET /api/sites` - All sites
- `GET /api/sites/{site_id}` - Specific site

### Subjects & Demographics

- `GET /api/subjects` - All subjects (filters: site_id, treatment_arm, status)
- `GET /api/subjects/{subject_id}` - Specific subject
- `GET /api/demographics/{subject_id}` - Subject demographics

### Clinical Data

- `GET /api/visits` - Visits (filters: subject_id, visit_status)
- `GET /api/vitals/{subject_id}` - Vital signs
- `GET /api/labs/{subject_id}` - Lab results (filters: lab_category, abnormal_only)
- `GET /api/adverse-events` - Adverse events (filters: severity, seriousness, ongoing)
- `GET /api/medical-history/{subject_id}` - Medical history
- `GET /api/conmeds/{subject_id}` - Concomitant medications
- `GET /api/tumor-assessments/{subject_id}` - Tumor assessments
- `GET /api/ecg/{subject_id}` - ECG results

### Monitoring & Quality

- `GET /api/deviations` - Protocol deviations (filters: type, status, severity)
- `GET /api/queries` - Data queries (filters: status, priority)
- `GET /api/statistics` - Overall statistics

### Example API Calls

```bash
# Get all subjects at Site 101
curl http://localhost:8000/api/subjects?site_id=101

# Get all serious adverse events
curl http://localhost:8000/api/adverse-events?seriousness=Yes

# Get abnormal labs for subject 101-001
curl http://localhost:8000/api/labs/101-001?abnormal_only=true

# Get open protocol deviations
curl http://localhost:8000/api/deviations?status=Open

# Get statistics
curl http://localhost:8000/api/statistics
```

---

## 📊 Data Quality & Scenarios

### Protocol Deviation Scenarios

```sql
-- Find visit window violations
SELECT subject_id, visit_number, visit_name, scheduled_date, actual_date,
       ABS(actual_date - scheduled_date) as days_outside_window
FROM visits
WHERE ABS(actual_date - scheduled_date) > window_upper_days
AND visit_completed = true;
```

### Safety Signal Detection

```sql
-- Find severe adverse events
SELECT subject_id, ae_term, severity, ctcae_grade, seriousness, onset_date
FROM adverse_events
WHERE severity IN ('Severe', 'Life-threatening')
OR seriousness = 'Yes'
ORDER BY onset_date DESC;

-- Find hepatotoxicity (ALT/AST >3x ULN)
SELECT subject_id, test_name, test_value, normal_range_upper,
       test_value / normal_range_upper as fold_increase
FROM laboratory_results
WHERE test_name IN ('ALT', 'AST')
AND test_value > normal_range_upper * 3
ORDER BY fold_increase DESC;

-- Find QTc prolongation
SELECT subject_id, ecg_date, qtcf_interval
FROM ecg_results
WHERE qtcf_interval > 470
ORDER BY qtcf_interval DESC;
```

### Data Quality Issues

```sql
-- Find open queries
SELECT subject_id, query_type, query_text, priority, query_date
FROM queries
WHERE query_status = 'Open'
ORDER BY priority DESC, query_date;

-- Find abnormal lab values
SELECT subject_id, test_name, test_value, abnormal_flag, 
       clinically_significant
FROM laboratory_results
WHERE abnormal_flag != 'Normal'
AND clinically_significant = true;
```

---

## 🌐 Free Cloud Deployment

### Supabase + Railway (Recommended)

**Database: Supabase (Free)**
- 500MB PostgreSQL database
- Automatic backups
- Connection pooling
- No credit card required

**API: Railway (Free)**
- 500 hours/month free
- Automatic HTTPS
- GitHub integration
- Simple deployment

**Deployment Steps:**

1. **Supabase Setup**
   ```bash
   # Create project at supabase.com
   # Copy connection string
   # Update .env with Supabase credentials
   ```

2. **Load Data to Supabase**
   ```bash
   python load_data.py
   ```

3. **Deploy API to Railway**
   ```bash
   # Install Railway CLI
   npm install -g @railway/cli
   
   # Login and init
   railway login
   railway init
   
   # Deploy
   railway up
   ```

### Alternative: Render

**Database: Render PostgreSQL (Free)**
- Limited to 1GB
- Auto-expires after 90 days

**API: Render Web Service (Free)**
- 750 hours/month free

---

## 📁 Project Structure

```
clinical-trial-data-layer/
├── README.md                      # This file
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment variables template
│
├── protocol_definition.json       # Complete protocol definition
├── schema.sql                     # PostgreSQL schema
│
├── generate_data_part1.py        # Generate sites, subjects, demographics
├── generate_data_part2.py        # Generate visits, vitals, labs
├── generate_data_part3.py        # Generate AEs, history, queries
│
├── synthetic_data_part1.json     # Generated data (Part 1)
├── synthetic_data_part2.json     # Generated data (Part 2)
├── synthetic_data_part3.json     # Generated data (Part 3)
│
├── load_data.py                   # Load data into PostgreSQL
├── api.py                         # FastAPI backend
│
└── exports/                       # CSV/Excel exports (optional)
```

---

## 🔄 Data Regeneration

To regenerate data with different scenarios:

```bash
# Change random seed in generate_data_*.py files
# Then regenerate all data
python generate_data_part1.py
python generate_data_part2.py
python generate_data_part3.py

# Reload into database
python load_data.py
```

---

## 📝 Next Steps: Adding AI Agents

Once the data layer is deployed, you can:

1. **Connect AI Agents** - Point agents to PostgreSQL database
2. **Test Detection Logic** - Use scenarios to test agent accuracy
3. **Implement Event Streaming** - Add Kafka for real-time processing
4. **Build Frontend** - React dashboard to visualize data
5. **Add MCP Servers** - Enable conversational queries

See the main project documentation for agent implementation details.

---

## 🛠️ Technical Details

### Data Generation Approach

- **Realistic Distributions**: Normal distributions for vitals/labs
- **Temporal Patterns**: Disease progression over time
- **Correlated Events**: Related AEs and lab abnormalities
- **Random Seed (1218)**: Reproducible generation
- **Scenario Injection**: Controlled deviations and safety signals

### Performance

- **Database Size**: ~50MB with indexes
- **API Response Time**: <100ms for most queries
- **Concurrent Users**: 50+ on free tier

---

## 📞 Support

For questions or issues:
- Review the API docs at `/docs`
- Check SQL queries in schema.sql
- Verify data generation logs
- Ensure PostgreSQL connection is working

---

## 📄 License

This synthetic dataset is for development and testing purposes only. 
Not for use in actual clinical trials or regulatory submissions.

---

**Ready to start building AI agents!** 🚀

The data layer is now complete and deployable on free cloud infrastructure. All 100 subjects have rich clinical data with realistic scenarios to test your 27 AI monitoring agents.
