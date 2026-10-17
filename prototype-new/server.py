import http.server
import socketserver
import webbrowser
import os

PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

def run():
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print("=" * 65)
        print(" SIH 2026 IDR PROTOTYPE SHOWCASE — MAIN LAUNCHER SERVER")
        print("=" * 65)
        print(f" Server running locally at: http://localhost:{PORT}")
        print(" Press Ctrl+C to stop the server.")
        print("=" * 65)
        
        webbrowser.open(f"http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")

if __name__ == "__main__":
    run()
