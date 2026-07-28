# Python File Server

A lightweight Python file server with a modern web interface for uploading, downloading, viewing, and deleting files. Supports local network access and optional public access using ngrok.

## Features

- Modern responsive web interface
- Upload files
- Download files
- Delete files
- File size and timestamp display
- Local network sharing
- Optional public sharing with ngrok
- No database required
- Simple setup

## Project Structure

```
pythonserver/
│
├── LIVE/                 # Uploaded files
├── templates/
│   └── index.html
├── server.py             # Local server
├── servernet.py          # Local + ngrok server
├── pip.bat               # Install required Python packages
└── README.md
```

## Requirements

- Python 3.10 or newer
- Git
- ngrok (only for public sharing)

## Installation

### Clone the repository

```bash
git clone https://github.com/gurnoorofficial/pythonserver.git
cd pythonserver
```

### Install Python

Download Python from:

https://www.python.org/downloads/

### Install required packages

Run:

```bash
pip.bat
```

### Configure ngrok (Optional)

Download ngrok:

https://ngrok.com/download

After installing, add your authentication token:

```bash
ngrok config add-authtoken YOUR_NGROK_AUTH_TOKEN
```

> Your ngrok authentication token is **not included** in this project. It is stored locally on your computer and should never be uploaded to GitHub.

## Running

### Local Server

```bash
python server.py
```

### Local + Public Server

```bash
python servernet.py
```

## Security

- Do not upload passwords or secrets.
- Do not commit your ngrok authentication token.
- Keep uploaded files private if they contain sensitive information.

## License

This project is open for personal and educational use.

## Author

**Gurnoor Singh**

GitHub:
https://github.com/gurnoorofficial
