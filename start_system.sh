#!/bin/bash

# Clinical Trial Rules Engine - Complete Startup Script
# This starts both backend API and frontend UI

echo "============================================================================"
echo "🏥 CLINICAL TRIAL RULES ENGINE - COMPLETE SYSTEM STARTUP"
echo "============================================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python
echo -e "${BLUE}[1/6] Checking Python...${NC}"
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi
echo -e "${GREEN}✓ Python found: $(python3 --version)${NC}"
echo ""

# Check Node.js
echo -e "${BLUE}[2/6] Checking Node.js...${NC}"
if ! command -v node &> /dev/null; then
    echo "⚠️  Node.js not found. Frontend will not start."
    echo "   Install from: https://nodejs.org/"
    SKIP_FRONTEND=true
else
    echo -e "${GREEN}✓ Node.js found: $(node --version)${NC}"
    SKIP_FRONTEND=false
fi
echo ""

# Check database
echo -e "${BLUE}[3/6] Checking database...${NC}"
if [ ! -f "clinical_trial.db" ]; then
    echo "❌ Database not found: clinical_trial.db"
    echo "   Please ensure clinical_trial.db is in the current directory"
    exit 1
fi
echo -e "${GREEN}✓ Database found: clinical_trial.db${NC}"
echo ""

# Install Python dependencies
echo -e "${BLUE}[4/6] Installing Python dependencies...${NC}"
pip install -q fastapi uvicorn anthropic pyyaml 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Python dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠️  Some dependencies may already be installed${NC}"
fi
echo ""

# Install Node dependencies
if [ "$SKIP_FRONTEND" = false ]; then
    echo -e "${BLUE}[5/6] Installing Node.js dependencies...${NC}"
    cd frontend
    if [ ! -d "node_modules" ]; then
        echo "   Installing npm packages (this may take a minute)..."
        npm install --silent
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Node.js dependencies installed${NC}"
        else
            echo "❌ Failed to install Node.js dependencies"
            SKIP_FRONTEND=true
        fi
    else
        echo -e "${GREEN}✓ Node.js dependencies already installed${NC}"
    fi
    cd ..
    echo ""
else
    echo -e "${BLUE}[5/6] Skipping Node.js dependencies (Node.js not found)${NC}"
    echo ""
fi

# Start services
echo -e "${BLUE}[6/6] Starting services...${NC}"
echo ""

# Start backend in background
echo -e "${GREEN}🚀 Starting Backend API (Port 8001)...${NC}"
python3 api/rules_api.py > backend.log 2>&1 &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"
echo "   Logs: backend.log"

# Wait for backend to start
sleep 3

# Check if backend started successfully
if ps -p $BACKEND_PID > /dev/null; then
    echo -e "${GREEN}✓ Backend API started successfully${NC}"
    echo "   API URL: http://localhost:8001"
    echo "   API Docs: http://localhost:8001/docs"
else
    echo "❌ Backend failed to start. Check backend.log for details"
    exit 1
fi
echo ""

# Start frontend
if [ "$SKIP_FRONTEND" = false ]; then
    echo -e "${GREEN}🚀 Starting Frontend UI (Port 3000)...${NC}"
    cd frontend
    npm run dev > ../frontend.log 2>&1 &
    FRONTEND_PID=$!
    cd ..
    echo "   Frontend PID: $FRONTEND_PID"
    echo "   Logs: frontend.log"
    
    # Wait for frontend to start
    sleep 5
    
    if ps -p $FRONTEND_PID > /dev/null; then
        echo -e "${GREEN}✓ Frontend UI started successfully${NC}"
        echo "   UI URL: http://localhost:3000"
    else
        echo "❌ Frontend failed to start. Check frontend.log for details"
    fi
else
    echo -e "${YELLOW}⚠️  Skipping Frontend (Node.js not available)${NC}"
    echo "   You can still use the API at http://localhost:8001"
fi

echo ""
echo "============================================================================"
echo -e "${GREEN}✅ SYSTEM STARTUP COMPLETE${NC}"
echo "============================================================================"
echo ""
echo "📊 Access Points:"
echo "   • Backend API:  http://localhost:8001"
echo "   • API Docs:     http://localhost:8001/docs"
if [ "$SKIP_FRONTEND" = false ]; then
    echo "   • Frontend UI:  http://localhost:3000"
fi
echo ""
echo "📝 Process IDs:"
echo "   • Backend:  $BACKEND_PID"
if [ "$SKIP_FRONTEND" = false ]; then
    echo "   • Frontend: $FRONTEND_PID"
fi
echo ""
echo "📋 Quick Test:"
echo "   curl http://localhost:8001/api/rules"
echo ""
echo "🛑 To stop all services:"
echo "   kill $BACKEND_PID"
if [ "$SKIP_FRONTEND" = false ]; then
    echo "   kill $FRONTEND_PID"
fi
echo ""
echo "📚 Documentation:"
echo "   • COMPLETE_DEPLOYMENT_GUIDE.md - Full setup guide"
echo "   • RULES_ENGINE_README.md - Technical documentation"
echo ""
echo "🎉 Ready to monitor clinical trials!"
echo "============================================================================"

# Save PIDs to file for easy cleanup
echo $BACKEND_PID > .pids
if [ "$SKIP_FRONTEND" = false ]; then
    echo $FRONTEND_PID >> .pids
fi
