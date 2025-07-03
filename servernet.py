import os
import json
import subprocess
import time
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "LIVE")
PORT = 8080

class FileServerHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/upload':
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            html = f"""
            <html><body>
            <h2>Upload File to {UPLOAD_DIR}</h2>
            <form method='POST' enctype='multipart/form-data'>
                <input type='file' name='file'><br><br>
                <input type='submit' value='Upload'>
            </form>
            <br>
            <a href="/">Back to file list</a>
            </body></html>
            """
            self.wfile.write(html.encode('utf-8'))
        else:
            super().do_GET()

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        content_type = self.headers.get('Content-Type', '')

        if "multipart/form-data" not in content_type:
            self.send_error(400, "Invalid Content-Type")
            return

        boundary = content_type.split("boundary=")[-1].encode()
        remainbytes = content_length
        line = self.rfile.readline()
        remainbytes -= len(line)

        if boundary not in line:
            self.send_error(400, "Invalid upload format")
            return

        line = self.rfile.readline()
        remainbytes -= len(line)

        if b"filename=" not in line:
            self.send_error(400, "No filename found")
            return

        filename = line.decode().split("filename=")[-1].strip().strip('"')
        filepath = os.path.join(UPLOAD_DIR, filename)

        # Skip headers
        remainbytes -= len(self.rfile.readline())
        remainbytes -= len(self.rfile.readline())

        with open(filepath, 'wb') as f:
            preline = self.rfile.readline()
            remainbytes -= len(preline)
            while remainbytes > 0:
                line = self.rfile.readline()
                remainbytes -= len(line)
                if boundary in line:
                    f.write(preline.rstrip(b'\r\n'))
                    break
                else:
                    f.write(preline)
                    preline = line

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(f"✅ File '{filename}' uploaded successfully.<br><a href='/'>Back</a>".encode('utf-8'))

    def translate_path(self, path):
        rel = super().translate_path(path)
        return os.path.join(UPLOAD_DIR, os.path.relpath(rel, os.getcwd()))

def start_ngrok():
    print("🌐 Starting ngrok tunnel...")
    subprocess.Popen(["ngrok", "http", str(PORT)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(3)
    try:
        tunnel_info = subprocess.check_output(["curl", "-s", "http://127.0.0.1:4040/api/tunnels"]).decode("utf-8")
        public_url = json.loads(tunnel_info)["tunnels"][0]["public_url"]
        print(f"🔗 Public ngrok URL: {public_url}")
        print(f"⬆️  Upload via: {public_url}/upload")
    except Exception as e:
        print(f"⚠️ Could not fetch ngrok URL: {e}")

if __name__ == "__main__":
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.chdir(UPLOAD_DIR)
    server = HTTPServer(("", PORT), FileServerHandler)
    print(f"✅ Serving LIVE folder at http://localhost:{PORT}")
    print(f"⬆️  Upload via http://localhost:{PORT}/upload")

    # Start ngrok in a separate thread
    threading.Thread(target=start_ngrok, daemon=True).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n❌ Server stopped.")
