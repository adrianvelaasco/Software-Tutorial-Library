#!/bin/bash
# Automatically navigate to script directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "================================================================="
echo "  🚀 CREATIVE TECH TUTORIALS INDEX"
echo "================================================================="
echo "  Starting local web server (No-Cache) at http://localhost:8080 ..."
echo "  Press Ctrl+C to stop the server at any time."
echo "================================================================="

# Free port 8080 if already in use by a previous server instance
lsof -ti :8080 | xargs kill -9 2>/dev/null || true

# Open default browser automatically after 1 second with dynamic anti-cache timestamp
(sleep 1 && open "http://localhost:8080/?v=$(date +%s)") &

# Start Python HTTP Server with anti-caching headers
python3 -c "
import http.server, socketserver

class NoCacheHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

if __name__ == '__main__':
    PORT = 8080
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(('', PORT), NoCacheHTTPRequestHandler) as httpd:
        httpd.serve_forever()
"


