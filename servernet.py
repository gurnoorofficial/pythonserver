import html
import json
import mimetypes
import os
import shutil
import socket
import subprocess
import threading
import time
import urllib.request

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse


BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "LIVE"
TEMPLATE_FILE = BASE_DIR / "templates" / "index.html"

HOST = "0.0.0.0"
PORT = 8080

# Change this if you want a different limit.
MAX_UPLOAD_SIZE = 2 * 1024 * 1024 * 1024  # 2 GB

PUBLIC_URL = ""
PUBLIC_URL_LOCK = threading.Lock()


def get_local_ip() -> str:
    """
    Returns the computer's local network IP.
    Example: 192.168.1.25
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


def clean_filename(filename: str) -> str:
    """
    Prevent uploaded filenames from writing outside LIVE.
    """
    filename = filename.replace("\\", "/")
    filename = os.path.basename(filename)
    filename = filename.replace("\x00", "").strip()

    if not filename:
        raise ValueError("Invalid filename")

    return filename


def create_unique_path(directory: Path, filename: str) -> Path:
    """
    Prevent overwriting an existing file.

    file.txt
    file (1).txt
    file (2).txt
    """
    filepath = directory / filename

    if not filepath.exists():
        return filepath

    stem = filepath.stem
    suffix = filepath.suffix
    number = 1

    while True:
        filepath = directory / f"{stem} ({number}){suffix}"

        if not filepath.exists():
            return filepath

        number += 1


def get_public_url() -> str:
    with PUBLIC_URL_LOCK:
        return PUBLIC_URL


def set_public_url(url: str) -> None:
    global PUBLIC_URL

    with PUBLIC_URL_LOCK:
        PUBLIC_URL = url


def start_ngrok() -> None:
    print("🌐 Starting ngrok tunnel...")

    try:
        # Start ngrok.
        subprocess.Popen(
            ["ngrok", "http", str(PORT)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=(
                subprocess.CREATE_NO_WINDOW
                if os.name == "nt"
                else 0
            ),
        )
    except FileNotFoundError:
        print("❌ ngrok command was not found.")
        print("Install ngrok or add ngrok.exe to Windows PATH.")
        return
    except OSError as error:
        print(f"❌ Could not start ngrok: {error}")
        return

    # Wait for ngrok API to become available.
    for _ in range(15):
        time.sleep(1)

        try:
            with urllib.request.urlopen(
                "http://127.0.0.1:4040/api/tunnels",
                timeout=3,
            ) as response:
                tunnel_data = json.loads(
                    response.read().decode("utf-8")
                )

            tunnels = tunnel_data.get("tunnels", [])

            # Prefer HTTPS URL.
            https_tunnel = next(
                (
                    tunnel
                    for tunnel in tunnels
                    if tunnel.get("public_url", "").startswith("https://")
                ),
                None,
            )

            selected_tunnel = https_tunnel or (
                tunnels[0] if tunnels else None
            )

            if selected_tunnel:
                public_url = selected_tunnel["public_url"]
                set_public_url(public_url)

                print(f"🔗 Public ngrok URL: {public_url}")
                print(f"⬆️  Public upload page: {public_url}")
                return

        except Exception:
            continue

    print("⚠️ Could not retrieve the ngrok public URL.")
    print("Check the ngrok dashboard at http://127.0.0.1:4040")


class FileServerHandler(BaseHTTPRequestHandler):
    server_version = "PythonShareServer/1.0"

    def send_html(self, content: str, status: int = 200) -> None:
        encoded_content = content.encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded_content)))
        self.end_headers()

        self.wfile.write(encoded_content)

    def redirect(self, location: str) -> None:
        self.send_response(303)
        self.send_header("Location", location)
        self.end_headers()

    def load_template(self) -> str:
        if not TEMPLATE_FILE.exists():
            raise FileNotFoundError(
                f"HTML template not found:\n{TEMPLATE_FILE}"
            )

        return TEMPLATE_FILE.read_text(encoding="utf-8")

    @staticmethod
    def format_size(size: int) -> str:
        units = ["B", "KB", "MB", "GB", "TB"]
        current_size = float(size)

        for unit in units:
            if current_size < 1024 or unit == units[-1]:
                if unit == "B":
                    return f"{int(current_size)} {unit}"

                return f"{current_size:.2f} {unit}"

            current_size /= 1024

        return f"{size} B"

    def create_file_list(self) -> str:
        files = sorted(
            (
                path
                for path in UPLOAD_DIR.iterdir()
                if path.is_file()
            ),
            key=lambda path: path.name.lower(),
        )

        if not files:
            return """
            <div class="empty-state">
                <div class="empty-icon">📂</div>
                <h3>No files available</h3>
                <p>Upload your first file above.</p>
            </div>
            """

        file_rows = []

        for filepath in files:
            escaped_name = html.escape(filepath.name, quote=True)
            encoded_name = quote(filepath.name)
            file_size = self.format_size(filepath.stat().st_size)

            file_rows.append(
                f"""
                <div class="file-item">
                    <div class="file-details">
                        <div class="file-icon">📄</div>

                        <div class="file-text">
                            <a
                                class="file-name"
                                href="/files/{encoded_name}"
                                target="_blank"
                            >
                                {escaped_name}
                            </a>

                            <div class="file-size">
                                {file_size}
                            </div>
                        </div>
                    </div>

                    <div class="file-actions">
                        <a
                            class="button download-button"
                            href="/download/{encoded_name}"
                        >
                            Download
                        </a>

                        <form
                            method="POST"
                            action="/delete"
                            onsubmit="return confirm('Delete this file?');"
                        >
                            <input
                                type="hidden"
                                name="filename"
                                value="{escaped_name}"
                            >

                            <button
                                class="button delete-button"
                                type="submit"
                            >
                                Delete
                            </button>
                        </form>
                    </div>
                </div>
                """
            )

        return "\n".join(file_rows)

    def show_homepage(self, message: str = "") -> None:
        try:
            template = self.load_template()
        except FileNotFoundError as error:
            self.send_error(500, str(error))
            return

        local_ip = get_local_ip()
        public_url = get_public_url()

        if public_url:
            public_address = f"""
            <a href="{html.escape(public_url)}" target="_blank">
                {html.escape(public_url)}
            </a>
            """
        else:
            public_address = """
            <span class="loading-text">
                Starting ngrok tunnel...
            </span>
            """

        message_html = ""

        if message:
            message_html = (
                f'<div class="message">{html.escape(message)}</div>'
            )

        page = (
            template
            .replace("{{MESSAGE}}", message_html)
            .replace("{{FILE_LIST}}", self.create_file_list())
            .replace(
                "{{LOCALHOST_URL}}",
                f"http://localhost:{PORT}",
            )
            .replace(
                "{{LOCAL_IP_URL}}",
                f"http://{local_ip}:{PORT}",
            )
            .replace(
                "{{PUBLIC_URL}}",
                public_address,
            )
            .replace(
                "{{UPLOAD_DIRECTORY}}",
                html.escape(str(UPLOAD_DIR)),
            )
        )

        self.send_html(page)

    def serve_file(
        self,
        requested_filename: str,
        force_download: bool = False,
    ) -> None:
        try:
            filename = clean_filename(
                unquote(requested_filename)
            )
        except ValueError:
            self.send_error(400, "Invalid filename")
            return

        filepath = (UPLOAD_DIR / filename).resolve()
        upload_root = UPLOAD_DIR.resolve()

        if filepath.parent != upload_root:
            self.send_error(403, "Access denied")
            return

        if not filepath.exists() or not filepath.is_file():
            self.send_error(404, "File not found")
            return

        content_type, _ = mimetypes.guess_type(filepath.name)

        if content_type is None:
            content_type = "application/octet-stream"

        disposition = "attachment" if force_download else "inline"

        try:
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header(
                "Content-Length",
                str(filepath.stat().st_size),
            )
            self.send_header(
                "Content-Disposition",
                f"{disposition}; filename*=UTF-8''{quote(filepath.name)}",
            )
            self.end_headers()

            with filepath.open("rb") as file:
                shutil.copyfileobj(file, self.wfile)

        except OSError as error:
            self.send_error(
                500,
                f"Could not read file: {error}",
            )

    def handle_upload(self) -> None:
        content_length_text = self.headers.get("Content-Length")

        if not content_length_text:
            self.send_error(411, "Content-Length is required")
            return

        try:
            content_length = int(content_length_text)
        except ValueError:
            self.send_error(400, "Invalid Content-Length")
            return

        if content_length > MAX_UPLOAD_SIZE:
            self.send_error(
                413,
                "Uploaded file is larger than the allowed limit",
            )
            return

        content_type = self.headers.get("Content-Type", "")

        if "multipart/form-data" not in content_type:
            self.send_error(400, "Invalid Content-Type")
            return

        boundary_value = None

        for section in content_type.split(";"):
            section = section.strip()

            if section.startswith("boundary="):
                boundary_value = section.split("=", 1)[1].strip('"')
                break

        if not boundary_value:
            self.send_error(400, "Upload boundary was not found")
            return

        boundary = ("--" + boundary_value).encode("utf-8")
        remaining = content_length

        first_line = self.rfile.readline()
        remaining -= len(first_line)

        if boundary not in first_line:
            self.send_error(400, "Invalid multipart upload")
            return

        disposition_line = self.rfile.readline()
        remaining -= len(disposition_line)

        try:
            disposition_text = disposition_line.decode(
                "utf-8",
                errors="replace",
            )
        except UnicodeDecodeError:
            self.send_error(400, "Invalid upload headers")
            return

        if "filename=" not in disposition_text:
            self.send_error(400, "No filename was provided")
            return

        filename_section = disposition_text.split(
            "filename=",
            1,
        )[1]

        filename = filename_section.strip().strip('"')

        try:
            filename = clean_filename(filename)
        except ValueError:
            self.send_error(400, "Invalid filename")
            return

        # Read remaining headers until blank line.
        while remaining > 0:
            header_line = self.rfile.readline()
            remaining -= len(header_line)

            if header_line in (b"\r\n", b"\n", b""):
                break

        filepath = create_unique_path(UPLOAD_DIR, filename)

        try:
            with filepath.open("wb") as destination:
                previous_line = self.rfile.readline()
                remaining -= len(previous_line)

                while remaining > 0:
                    current_line = self.rfile.readline()
                    remaining -= len(current_line)

                    if current_line.startswith(boundary):
                        destination.write(
                            previous_line.rstrip(b"\r\n")
                        )
                        break

                    destination.write(previous_line)
                    previous_line = current_line

        except OSError as error:
            self.send_error(
                500,
                f"Upload failed: {error}",
            )
            return

        self.redirect(
            "/?message="
            + quote(
                f"File '{filepath.name}' uploaded successfully."
            )
        )

    def handle_delete(self) -> None:
        try:
            content_length = int(
                self.headers.get("Content-Length", "0")
            )
        except ValueError:
            self.send_error(400, "Invalid request")
            return

        body = self.rfile.read(content_length).decode(
            "utf-8",
            errors="replace",
        )

        form_data = parse_qs(body)
        filename_value = form_data.get("filename", [""])[0]

        try:
            filename = clean_filename(filename_value)
        except ValueError:
            self.send_error(400, "Invalid filename")
            return

        filepath = (UPLOAD_DIR / filename).resolve()
        upload_root = UPLOAD_DIR.resolve()

        if filepath.parent != upload_root:
            self.send_error(403, "Access denied")
            return

        if not filepath.exists() or not filepath.is_file():
            self.send_error(404, "File not found")
            return

        try:
            filepath.unlink()
        except OSError as error:
            self.send_error(
                500,
                f"Could not delete file: {error}",
            )
            return

        self.redirect(
            "/?message=" + quote(
                f"File '{filename}' deleted successfully."
            )
        )

    def do_GET(self) -> None:
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query = parse_qs(parsed_path.query)

        if path == "/":
            message = query.get("message", [""])[0]
            self.show_homepage(message)
            return

        if path == "/upload":
            # Old /upload URL now opens the same complete UI.
            self.redirect("/")
            return

        if path.startswith("/files/"):
            filename = path.removeprefix("/files/")
            self.serve_file(filename, force_download=False)
            return

        if path.startswith("/download/"):
            filename = path.removeprefix("/download/")
            self.serve_file(filename, force_download=True)
            return

        self.send_error(404, "Page not found")

    def do_POST(self) -> None:
        parsed_path = urlparse(self.path)

        if parsed_path.path == "/upload":
            self.handle_upload()
            return

        if parsed_path.path == "/delete":
            self.handle_delete()
            return

        self.send_error(404, "Page not found")


if __name__ == "__main__":
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    TEMPLATE_FILE.parent.mkdir(parents=True, exist_ok=True)

    server = ThreadingHTTPServer(
        (HOST, PORT),
        FileServerHandler,
    )

    local_ip = get_local_ip()

    print("=" * 65)
    print("✅ File server started")
    print(f"💻 Localhost: http://localhost:{PORT}")
    print(f"📱 Local network: http://{local_ip}:{PORT}")
    print(f"📂 Sharing folder: {UPLOAD_DIR}")
    print("🌐 ngrok public address will appear shortly")
    print("🛑 Press Ctrl+C to stop")
    print("=" * 65)

    ngrok_thread = threading.Thread(
        target=start_ngrok,
        daemon=True,
    )
    ngrok_thread.start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n❌ Server stopped.")
    finally:
        server.server_close()