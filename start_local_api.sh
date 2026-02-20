#!/bin/bash

# Local API Server - Quick Start
# Clinical Trial Monitoring System

echo "=================================================================="
echo "🏥 Clinical Trial Monitoring API - Local Server"
echo "Protocol: NVX-1218.22 (NovaPlex-450 in Advanced NSCLC)"
echo "Sponsor: NexaVance Therapeutics Inc."
echo "=================================================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if database exists
if [ ! -f "clinical_trial.db" ]; then
    echo -e "${YELLOW}⚠ Database not found. Creating it now...${NC}"
    python create_sqlite_db.py
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Failed to create database${NC}"
        exit 1
    fi
fi

# Check if Python packages are installed
echo "📦 Checking dependencies..."
python -c "import fastapi, uvicorn" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Installing required packages...${NC}"
    pip install -q fastapi uvicorn --break-system-packages 2>/dev/null || pip install -q fastapi uvicorn
fi

echo -e "${GREEN}✓ Dependencies ready${NC}"
echo ""

# Display info
DB_SIZE=$(ls -lh clinical_trial.db | awk '{print $5}')
echo "📊 Database: clinical_trial.db ($DB_SIZE)"
echo "🔧 API Server: FastAPI + Uvicorn"
echo "🌐 Local URL: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""

# Display some quick stats
echo "📈 Quick Database Stats:"
python -c "
import sqlite3
conn = sqlite3.connect('clinical_trial.db')
cur = conn.cursor()
tables = ['subjects', 'adverse_events', 'laboratory_results', 'protocol_deviations', 'queries']
for table in tables:
    cur.execute(f'SELECT COUNT(*) FROM {table}')
    count = cur.fetchone()[0]
    print(f'   {table:25s}: {count:,} records')
conn.close()
"

echo ""
echo "=================================================================="
echo -e "${GREEN}🚀 Starting API Server...${NC}"
echo "=================================================================="
echo ""
echo -e "${BLUE}Press CTRL+C to stop the server${NC}"
echo ""

# Start the server
python api_sqlite.py
