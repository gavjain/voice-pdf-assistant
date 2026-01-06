#!/bin/bash
# Production startup script for backend

echo "🚀 Starting Voice PDF Assistant Backend (Production)"

# Check if running in production
if [ "$ENVIRONMENT" = "production" ]; then
    echo "✅ Production mode detected"
else
    echo "⚠️  Warning: Not in production mode"
fi

# Run database migrations (if any)
echo "📊 Initializing database..."

# Start server with production settings
echo "🌐 Starting Uvicorn server..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port ${PORT:-8000} \
    --workers 2 \
    --log-level info \
    --no-access-log
