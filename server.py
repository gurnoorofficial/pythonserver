import html
import mimetypes
import os
import shutil
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, unquote, urlparse
import cgi


BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "LIVE"
TEMPLATE_FILE = BASE_DIR / "templates" / "index.html"

HOST = "0.0.0.0"
PORT = 8080

# Maximum upload size: 1 GB
MAX_UPLOAD_SIZE = 1024 * 1024 * 1024


def get_local_ip() -> str:
    """
    Find the computer's local network IP address.
    Example: 192.168.1.25
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        # No actual connection is made.
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


def safe_filename(filename: str) -> str:
    """
    Remove folders and unsafe path characters from uploaded filenames.
    """
    filename = filename.replace("\\", "/")
    filename = os.path.basename(filename)
    filename = filename.replace("\x00", "").strip()

    if not filename:
        raise ValueError("Invalid filename")

    return filename


def unique_filepath(directory: Path, filename: str) -> Path:
    """
    Avoid overwriting an existing file.

    example.txt
    example (1).txt
    example (2).txt
    """
    filepath = directory / filename

    if not filepath.exists():
        return filepath

    stem = filepath.stem
    suffix = filepath.suffix
    counter = 1

    while True:
        new_filepath = directory / f"{stem} ({counter}){suffix}"

        if not new_filepath.exists():
            return new_filepath

        counter += 1


class FileServerHandler(BaseHTTPRequestHandler):
    server_version = "LocalFileServer/1.0"

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
                f"HTML template was not found: {TEMPLATE_FILE}"
            )

        return TEMPLATE_FILE.read_text(encoding="utf-8")

    def create_file_list_html(self) -> str:
        files = sorted(
            UPLOAD_DIR.iterdir(),
            key=lambda item: item.name.lower()
        )

        if not files:
            return """
            <div class="empty-state">
                <div class="empty-icon">📂</div>
                <h3>No files uploaded</h3>
                <p>Choose a file above to upload it.</p>
            </div>
            """

        rows = []

        for file_path in files:
            if not file_path.is_file():
                continue

            if file_path.name == ".gitkeep":
                continue

            file_name = file_path.name
            escaped_name = html.escape(file_name)
            encoded_name = quote(file_name)

            file_size = self.format_file_size(file_path.stat().st_size)

            rows.append(
                f"""
                <div class="file-item">
                    <div class="file-information">
                        <div class="file-icon">📄</div>

                        <div>
                            <a
                                class="file-name"
                                href="/files/{encoded_name}"
                                target="_blank"
                            >
                                {escaped_name}
                            </a>

                            <div class="file-size">{file_size}</div>
                        </div>
                    </div>

                    <div class="file-actions">
                        <a
                            class="button secondary-button"
                            href="/files/{encoded_name}"
                            download
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

        return "\n".join(rows)

    @staticmethod
    def format_file_size(size: int) -> str:
        units = ["B", "KB", "MB", "GB", "TB"]
        converted_size = float(size)

        for unit in units:
            if converted_size < 1024 or unit == units[-1]:
                if unit == "B":
                    return f"{int(converted_size)} {unit}"

                return f"{converted_size:.2f} {unit}"

            converted_size /= 1024

        return f"{size} B"

    def show_homepage(self, message: str = "") -> None:
        try:
            template = self.load_template()
        except FileNotFoundError as error:
            self.send_error(500, str(error))
            return

        local_ip = get_local_ip()

        message_html = ""

        if message:
            message_html = (
                f'<div class="message">{html.escape(message)}</div>'
            )

        page = (
            template
            .replace("{{FILE_LIST}}", self.create_file_list_html())
            .replace("{{MESSAGE}}", message_html)
            .replace("{{LOCAL_URL}}", f"http://{local_ip}:{PORT}")
            .replace("{{LOCALHOST_URL}}", f"http://localhost:{PORT}")
        )

        self.send_html(page)

    def serve_file(self, requested_name: str) -> None:
        try:
            filename = safe_filename(unquote(requested_name))
        except ValueError:
            self.send_error(400, "Invalid filename")
            return

        filepath = (UPLOAD_DIR / filename).resolve()

        # Ensure the requested file remains inside LIVE.
        if UPLOAD_DIR.resolve() not in filepath.parents:
            self.send_error(403, "Access denied")
            return

        if not filepath.exists() or not filepath.is_file():
            self.send_error(404, "File not found")
            return

        content_type, _ = mimetypes.guess_type(filepath.name)

        if content_type is None:
            content_type = "application/octet-stream"

        try:
            file_size = filepath.stat().st_size

            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(file_size))
            self.send_header(
                "Content-Disposition",
                f'inline; filename="{filepath.name}"'
            )
            self.end_headers()

            with filepath.open("rb") as file:
                shutil.copyfileobj(file, self.wfile)

        except OSError as error:
            self.send_error(500, f"Unable to read file: {error}")

    def do_GET(self) -> None:
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        if path == "/":
            self.show_homepage()
            return

        if path.startswith("/files/"):
            requested_name = path.removeprefix("/files/")
            self.serve_file(requested_name)
            return

        self.send_error(404, "Page not found")

    def handle_upload(self) -> None:
        content_length_value = self.headers.get("Content-Length")

        if not content_length_value:
            self.send_error(411, "Content-Length is required")
            return

        try:
            content_length = int(content_length_value)
        except ValueError:
            self.send_error(400, "Invalid Content-Length")
            return

        if content_length > MAX_UPLOAD_SIZE:
            self.send_error(413, "Uploaded file is too large")
            return

        content_type = self.headers.get("Content-Type", "")

        if "multipart/form-data" not in content_type:
            self.send_error(400, "Expected multipart form upload")
            return

        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": content_type,
                "CONTENT_LENGTH": str(content_length),
            },
        )

        if "file" not in form:
            self.send_error(400, "No file was selected")
            return

        uploaded_file = form["file"]

        if isinstance(uploaded_file, list):
            uploaded_file = uploaded_file[0]

        if not uploaded_file.filename:
            self.send_error(400, "No file was selected")
            return

        try:
            filename = safe_filename(uploaded_file.filename)
        except ValueError:
            self.send_error(400, "Invalid filename")
            return

        filepath = unique_filepath(UPLOAD_DIR, filename)

        try:
            with filepath.open("wb") as destination:
                shutil.copyfileobj(uploaded_file.file, destination)
        except OSError as error:
            self.send_error(500, f"Upload failed: {error}")
            return

        self.redirect(
            "/?message=" + quote(
                f"File '{filepath.name}' uploaded successfully."
            )
        )

    def handle_delete(self) -> None:
        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length).decode("utf-8")

        from urllib.parse import parse_qs

        form_data = parse_qs(body)
        filename_value = form_data.get("filename", [""])[0]

        try:
            filename = safe_filename(filename_value)
        except ValueError:
            self.send_error(400, "Invalid filename")
            return

        if filename == ".gitkeep":
            self.send_error(403, ".gitkeep is protected and cannot be deleted")
            return

        filepath = (UPLOAD_DIR / filename).resolve()

        if UPLOAD_DIR.resolve() not in filepath.parents:
            self.send_error(403, "Access denied")
            return

        if not filepath.exists() or not filepath.is_file():
            self.send_error(404, "File not found")
            return

        try:
            filepath.unlink()
        except OSError as error:
            self.send_error(500, f"Could not delete file: {error}")
            return

        self.redirect("/")

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

    local_ip = get_local_ip()

    server = ThreadingHTTPServer(
        (HOST, PORT),
        FileServerHandler
    )

    print("=" * 55)
    print("File server started")
    print(f"Localhost: http://localhost:{PORT}")
    print(f"Local network: http://{local_ip}:{PORT}")
    print(f"Serving folder: {UPLOAD_DIR}")
    print("Press Ctrl+C to stop")
    print("=" * 55)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()