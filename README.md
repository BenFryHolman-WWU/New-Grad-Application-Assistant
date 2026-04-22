# Job Search Assistant MacOS

A local-first web app for managing your job search. Track applications, visit job boards, store documents, and keep notes — all in a SQLite database that lives on your machine. Nothing is sent to any server.

## Install

```bash
git clone <repo-url> job-search-assistant
cd job-search-assistant
bash install.sh
```

The installer will:

1. Verify Python 3.9+
2. Create a virtual environment and install dependencies
3. Add **Job Search.app** to your Desktop with a custom icon

Double-click the app to start — the server launches automatically and opens in your browser. If the server is already running, the app just opens the browser.

## Manual start

```bash
source venv/bin/activate
uvicorn main:app
```

Then open **http://localhost:8000**. Logs from the Desktop app are written to `/tmp/jsa-server.log`.

## Features

| Tab | What it does |
|---|---|
| **Job Boards** | 24 boards across General, Tech, and Remote categories. Green dot = visited today (resets at 6 AM). |
| **Applications** | Spreadsheet-style tracker. Add, edit, filter by status, import CSV/Excel, export CSV. |
| **Goals** | Set daily and weekly targets for applications and boards visited. Streaks track your consistency. |
| **Calendar** | Monthly heatmap showing boards visited and apps sent per day. |
| **My Links** | Quick-access bookmarks with color labels and copy-to-clipboard. |
| **Contacts** | Reference contacts with one-click email/phone copy. |
| **Documents** | Upload resumes, cover letters, and references. Drag-and-drop supported. |
| **Notes** | Two autosaving pads for cover letter snippets and general search notes. |

## Data

| Path | Contents |
|---|---|
| `jobs.db` | SQLite database — all applications, contacts, links, notes, and visits |
| `uploads/` | Uploaded document files |

Both are excluded from git. Back them up or move them freely — the app recreates them on first run if missing.

## Requirements

- Python 3.9+
- macOS (for the `.app` shortcut and icon generation — the app itself runs on any OS)

## API

Interactive docs at **http://localhost:8000/docs** while the server is running.
