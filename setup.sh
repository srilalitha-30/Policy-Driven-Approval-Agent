#!/bin/bash
# Setup script for Policy-Driven Approval Agent

echo "🚀 Setting up Policy-Driven Approval Agent..."

# Backend setup
echo "📦 Setting up backend..."
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo "✓ Backend setup complete"

# Frontend setup (optional)
if command -v npm &> /dev/null; then
    echo "📦 Setting up frontend..."
    cd ../frontend
    npm install -q
    echo "✓ Frontend setup complete"
else
    echo "⚠️  npm not found - skipping frontend setup"
fi

cd ..
echo "✅ Setup complete! Run './run.sh' to start the application"
