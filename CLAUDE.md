# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

doc-to-pdf is a REST API microservice for high-quality DOCX to PDF conversion using LibreOffice headless. Designed for n8n integration and Coolify deployment.

## Build & Run

```bash
# Docker (recommended)
docker compose up -d

# Local development (requires LibreOffice)
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Architecture

```
app/
├── main.py        # FastAPI app, /convert and /health endpoints
├── converter.py   # LibreOffice subprocess wrapper, metadata handling
├── downloader.py  # URL download and local file reading
├── auth.py        # API-Key middleware (X-API-Key header)
└── config.py      # Environment-based configuration
```

## Key Design Decisions

- **LibreOffice headless** for format-accurate conversion (no styling loss)
- **Three input modes**: file upload, URL, local path
- **API-Key auth** via middleware (optional in dev, required in production)
- **Fallback on errors**: returns PDF with warnings instead of failing
- **Metadata handling**: configurable keep/strip via exiftool
- **Coolify-ready**: separate docker-compose without port exposure

## API

- `POST /convert` - Convert DOCX to PDF (requires auth if API_KEY set)
- `GET /health` - Health check (no auth)

## Environment Variables

- `API_KEY` - Auth key (empty = disabled)
- `CONVERSION_TIMEOUT` - Default 120s
- `MAX_FILE_SIZE` - Default 50MB
