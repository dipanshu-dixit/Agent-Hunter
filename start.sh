#!/bin/bash

echo "🛑 Stopping existing processes..."
pkill -f uvicorn 2>/dev/null || true
sudo fuser -k 8000/tcp 2>/dev/null || true

echo "🔄 Restoring database from snapshot..."
python restore_snapshot.py

echo "🚀 Starting API server..."
uvicorn api.main:app --port 8000 &

echo "⏳ Waiting for API to start..."
sleep 3

echo "🔍 Running initial scan..."
python -u run_scan.py

echo ""
echo "🚀 AgentHunter running!"
echo "🔌 API: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"

wait