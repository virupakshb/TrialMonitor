#!/bin/bash

# Clinical Trial Data Layer - Quick Start Script
# Protocol: NVX-1218.22 (NovaPlex-450 in Advanced NSCLC)
# Sponsor: NexaVance Therapeutics Inc.

echo "=================================================================="
echo "Clinical Trial Data Layer - Quick Start"
echo "Protocol: NVX-1218.22"
echo "Sponsor: NexaVance Therapeutics Inc."
echo "=================================================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed. Please install Python 3.11 or higher.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python 3 found${NC}"

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "  Python version: $PYTHON_VERSION"

# Install dependencies
echo ""
echo "📦 Installing Python dependencies..."
pip install -q -r requirements.txt --break-system-packages 2>/dev/null || pip install -q -r requirements.txt
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${RED}❌ Failed to install dependencies${NC}"
    exit 1
fi

# Check if data already exists
if [ -f "synthetic_data_part1.json" ]; then
    echo ""
    echo -e "${YELLOW}⚠ Synthetic data files already exist${NC}"
    read -p "Do you want to regenerate data? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Skipping data generation..."
        SKIP_GENERATION=true
    fi
fi

# Generate synthetic data
if [ "$SKIP_GENERATION" != true ]; then
    echo ""
    echo "🔄 Generating synthetic clinical trial data..."
    echo ""
    
    echo "  Part 1: Protocol, Sites, Subjects, Demographics..."
    python3 generate_data_part1.py
    if [ $? -eq 0 ]; then
        echo -e "  ${GREEN}✓ Part 1 complete${NC}"
    else
        echo -e "  ${RED}❌ Part 1 failed${NC}"
        exit 1
    fi
    
    echo ""
    echo "  Part 2: Visits, Vital Signs, Laboratory Results..."
    python3 generate_data_part2.py
    if [ $? -eq 0 ]; then
        echo -e "  ${GREEN}✓ Part 2 complete${NC}"
    else
        echo -e "  ${RED}❌ Part 2 failed${NC}"
        exit 1
    fi
    
    echo ""
    echo "  Part 3: AEs, Medical History, Queries, Deviations..."
    python3 generate_data_part3.py
    if [ $? -eq 0 ]; then
        echo -e "  ${GREEN}✓ Part 3 complete${NC}"
    else
        echo -e "  ${RED}❌ Part 3 failed${NC}"
        exit 1
    fi
fi

# Summary
echo ""
echo "=================================================================="
echo -e "${GREEN}✅ Data generation complete!${NC}"
echo "=================================================================="
echo ""
echo "📊 Generated Data Summary:"
echo "   • 5 Sites (USA, UK, Canada, Australia, Singapore)"
echo "   • 100 Subjects (randomized 1:1 to treatment arms)"
echo "   • ~800 Visits with realistic scheduling"
echo "   • ~15,000 Laboratory results"
echo "   • ~300 Adverse events (including SAEs)"
echo "   • Protocol deviations and data queries for AI testing"
echo ""
echo "=================================================================="
echo "📝 Next Steps:"
echo "=================================================================="
echo ""
echo "1. Set up PostgreSQL Database:"
echo "   - Option A: Local PostgreSQL"
echo "     $ brew install postgresql@15  (macOS)"
echo "     $ sudo apt install postgresql-15  (Linux)"
echo ""
echo "   - Option B: Supabase (Free Cloud)"
echo "     Visit: https://supabase.com"
echo "     Create project and get connection string"
echo ""
echo "2. Configure database connection:"
echo "   $ cp .env.example .env"
echo "   $ nano .env  (edit with your database credentials)"
echo ""
echo "3. Load data into PostgreSQL:"
echo "   $ python3 load_data.py"
echo ""
echo "4. Start the API server:"
echo "   $ python3 api.py"
echo "   API will be available at: http://localhost:8000"
echo "   Documentation: http://localhost:8000/docs"
echo ""
echo "=================================================================="
echo ""
echo "📚 For detailed instructions, see README.md"
echo ""
