#!/bin/bash

# NSW EV Intelligence Platform - Deployment Script

echo "🚀 NSW EV Intelligence Platform Deployment"
echo "=========================================="
echo ""

# Check if Databricks CLI is installed
if ! command -v databricks &> /dev/null
then
    echo "❌ Databricks CLI not found. Please install it first:"
    echo "   pip install databricks-cli"
    exit 1
fi

echo "✅ Databricks CLI found"
echo ""

# Get current directory
APP_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "📁 Application directory: $APP_DIR"
echo ""

# App name
APP_NAME="nsw-ev-intelligence-platform"

# Check if app exists
echo "🔍 Checking if app exists..."
if databricks apps list | grep -q "$APP_NAME"; then
    echo "⚠️  App '$APP_NAME' already exists"
    read -p "Do you want to update it? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]
    then
        echo "📦 Deploying updates..."
        databricks apps deploy "$APP_NAME" "$APP_DIR"
        echo "✅ App updated successfully!"
    else
        echo "❌ Deployment cancelled"
        exit 0
    fi
else
    echo "📦 Creating new app..."
    databricks apps create "$APP_NAME"
    echo "📦 Deploying app..."
    databricks apps deploy "$APP_NAME" "$APP_DIR"
    echo "✅ App created and deployed successfully!"
fi

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "To view your app:"
echo "  databricks apps list"
echo "  databricks apps start $APP_NAME"
echo ""
echo "To get the app URL:"
echo "  databricks apps get $APP_NAME"
