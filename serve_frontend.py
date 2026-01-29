"""Simple HTTP server to serve the frontend for development."""

import http.server
import socketserver
import os
import sys
import webbrowser
from functools import partial

PORT = 3000
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")


class CORSHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler with CORS headers for development."""

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()


def main():
    os.chdir(FRONTEND_DIR)

    handler = partial(CORSHTTPRequestHandler, directory=FRONTEND_DIR)

    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"\n{'='*50}")
        print(f"  Recipe Calculator Frontend Server")
        print(f"{'='*50}")
        print(f"\n  Serving frontend at: http://localhost:{PORT}")
        print(f"  Frontend directory:  {FRONTEND_DIR}")
        print(f"\n  Make sure backend is running on port 8000!")
        print(f"  Start backend with: python run.py")
        print(f"\n  Press Ctrl+C to stop the server")
        print(f"{'='*50}\n")

        # Open browser
        try:
            webbrowser.open(f"http://localhost:{PORT}")
        except Exception:
            pass

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\nServer stopped.")
            sys.exit(0)


if __name__ == "__main__":
    main()
