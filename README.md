# Gurnoor Private Cloud

A modern self-hosted private cloud built with pure Python.

Gurnoor Private Cloud is a lightweight file sharing server that runs locally on your computer and can optionally expose itself securely to the internet using **ngrok**. It provides a modern web interface for uploading, downloading, searching, sorting, and managing files without requiring any external database or web framework.

The project is designed to be simple, portable, and easy to run while providing a polished user experience on both desktop and mobile devices.

---

# Features

* Modern responsive web interface
* Desktop and iPhone optimized layout
* Drag and drop file upload
* Automatic upload progress
* Download files
* Delete files
* Search files instantly
* Sort files
* Floating upload window
* Dashboard
* Activity page
* Settings page
* Automatic ngrok public URL detection
* Localhost access
* Local network access
* Public internet access through ngrok
* No database required
* Pure Python implementation
* Lightweight and fast
* Python 3.13 compatible
* Works without Flask or Django
* Simple folder-based storage

---

# Project Structure

```text
python_share/
│
├── README.md
├── server.py
├── servernet.py
├── pip.bat
│
├── LIVE/
│   └── Uploaded files
│
└── templates/
    └── index.html
```

---

# Files

## README.md

Project documentation.

---

## server.py

Local-only file server.

Use this when you only need access from your own computer or local network.

---

## servernet.py

Internet-enabled version.

Features include:

* Starts local server
* Starts ngrok automatically
* Detects public URL
* Updates dashboard automatically
* Internet file sharing

---

## pip.bat

Installs required Python packages.

---

## templates/

Contains the web interface.

Currently includes:

* index.html

---

## LIVE/

All uploaded files are stored here.

The server automatically serves files from this folder.

---

# Requirements

* Python 3.13+
* Windows
* Internet connection (optional if using ngrok)

---

# Installation

Clone the project or download the source.

Install dependencies:

```bash
pip.bat
```

or manually:

```bash
pip install pyngrok
```

---

# Running

Local server:

```bash
python server.py
```

Internet server:

```bash
python servernet.py
```

---

# Access

After starting the server you can use:

## Localhost

```
http://127.0.0.1:8080
```

---

## Local Network

```
http://YOUR_LOCAL_IP:8080
```

---

## Internet

When using **servernet.py**, a public ngrok URL will automatically appear inside the dashboard.

Example:

```
https://random-name.ngrok-free.app
```

---

# Uploading Files

You can upload files by:

* Dragging files into the upload window
* Selecting files manually
* Dropping files from desktop

Uploads are saved directly into:

```text
LIVE/
```

---

# Downloading Files

Every stored file includes a download button.

Downloaded files keep their original filename.

---

# Deleting Files

Files can be removed directly from the web interface.

A confirmation dialog prevents accidental deletion.

---

# Search

Instant search filters files in real time.

No page refresh is required.

---

# Sorting

Supported sorting methods:

* Name (A–Z)
* Name (Z–A)
* Largest first
* Smallest first

---

# Responsive Design

Optimized for:

* Desktop
* Laptop
* Tablet
* iPhone
* Android

---

# Security Notes

This project is intended for personal use.

Recommendations:

* Share the ngrok URL only with trusted people.
* Keep your computer updated.
* Do not expose sensitive files publicly unless necessary.
* Consider additional authentication if deploying beyond personal use.

---

# Technologies

* Python 3.13
* http.server
* ThreadingHTTPServer
* HTML5
* CSS3
* Vanilla JavaScript
* ngrok

---

# Design Philosophy

The project focuses on:

* Minimal dependencies
* High performance
* Clean code
* Easy maintenance
* Modern user interface
* Mobile-first responsiveness
* Self-hosting
* Privacy

---

# Future Ideas

Possible future improvements include:

* User authentication
* Multiple users
* File previews
* Image thumbnails
* Video streaming
* Folder support
* ZIP download
* File rename
* Storage statistics
* Theme customization
* Upload history
* Password-protected sharing
* QR code sharing
* WebDAV support

---

# License

This project is provided as-is for personal and educational use.

---

# Author

**Gurnoor Singh**

Built with Python to provide a modern, lightweight, self-hosted private cloud with local and internet file sharing capabilities.
