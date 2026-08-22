#!/bin/bash
# Run script for Policy-Driven Approval Agent

echo "🚀 Starting Policy-Driven Approval Agent..."

# Start backend in background
echo "Starting backend on http://localhost:8000..."
cd backend
source venv/bin/activate
python main.py &
BACKEND_PID=$!

sleep 2

# Check if backend is running
if kill -0 $BACKEND_PID 2>/dev/null; then
    echo "✓ Backend started (PID: $BACKEND_PID)"
else
    echo "✗ Failed to start backend"
    exit 1
fi

# Start frontend if npm is available
cd ../frontend
if command -v npm &> /dev/null; then
    echo "Starting frontend on http://localhost:3000..."
    npm start &
    FRONTEND_PID=$!
    echo "✓ Frontend started (PID: $FRONTEND_PID)"
else
    echo "⚠️  npm not found - frontend not started"
    echo "To start frontend manually: cd frontend && npm start"
fi

echo ""
echo "✅ Application started!"
echo ""
echo "Backend API:  http://localhost:8000"
echo "Frontend UI:  http://localhost:3000 (if npm available)"
echo ""
echo "Press Ctrl+C to stop the application"
echo ""

# Wait for Ctrl+C
wait $BACKEND_PID
