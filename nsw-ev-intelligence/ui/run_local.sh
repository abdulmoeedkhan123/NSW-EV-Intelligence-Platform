#!/bin/bash

echo "🚀 NSW EV Intelligence Platform - Local Test"
echo "============================================="
echo ""

# Navigate to UI directory
cd "$(dirname "$0")"

# Check if streamlit is installed
if ! python3 -c "import streamlit" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip install -q streamlit==1.31.0 pandas plotly
    echo "✅ Dependencies installed"
fi

echo ""
echo "🌐 Starting Streamlit application..."
echo "   URL: http://localhost:8501"
echo "   Press Ctrl+C to stop"
echo ""
echo "⚠️  Note: Database queries may fail if not running on Databricks"
echo "   The UI will display sample/empty data in that case"
echo ""

# Start streamlit
streamlit run home.py --server.port 8501 --server.headless true
