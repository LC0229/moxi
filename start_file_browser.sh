#!/bin/bash
# Start local server for file browser

cd "$(dirname "$0")"

echo "🚀 Starting file browser server..."
echo ""
echo "📁 Serving files from: $(pwd)"
echo "🌐 Open in browser: http://localhost:8000/file_browser_ui.html"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Check if port 8000 is already in use
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Port 8000 is already in use. Using existing server."
    echo "🌐 Open: http://localhost:8000/file_browser_ui.html"
else
    python3 -m http.server 8000
fi
