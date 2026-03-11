#!/bin/bash

echo "🛑 Stopping existing processes..."
pkill -f uvicorn 2>/dev/null || true
pkill -f streamlit 2>/dev/null || true
sudo fuser -k 8000/tcp 2>/dev/null || true
sudo fuser -k 8501/tcp 2>/dev/null || true

echo "🚀 Starting API server..."
uvicorn api.main:app --port 8000 &

echo "⏳ Waiting for API to start..."
sleep 3

echo "🔍 Running initial scan..."
python -u run_scan.py

echo "📊 Starting dashboard..."
streamlit run dashboard/app.py &

sleep 2

echo ""
echo "🚀 AgentHunter running!"
echo "📊 Dashboard: http://localhost:8501"
echo "🔌 API: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Keep script running
wait