# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

doc-to-pdf is a REST API microservice for high-quality DOCX to PDF conversion using OnlyOffice. Designed for n8n integration and Coolify deployment.

## Build & Run

```bash
# Docker (recommended)
docker compose up -d

# Note: First startup takes ~90 seconds (OnlyOffice initialization)
```

## Architecture

```
app/
├── main.py        # FastAPI app, /convert and /health endpoints
├── converter.py   # OnlyOffice x2t integration via shared volume
├── downloader.py  # URL download and local file reading
├── auth.py        # API-Key middleware (X-API-Key header)
└── config.py      # Environment-based configuration

fonts/             # Custom fonts (TTF/OTF) - auto-loaded on startup
```

### Docker Services

- **doc-to-pdf**: Python FastAPI service (lightweight)
- **onlyoffice**: OnlyOffice Document Server with x2t converter

Communication happens via shared Docker volume (`/shared`).

## Key Design Decisions

- **OnlyOffice x2t** for best MS Office compatibility (tables, colors, formatting)
- **Three input modes**: file upload, URL, local path
- **API-Key auth** via middleware (optional in dev, required in production)
- **Custom fonts**: Place TTF/OTF in `fonts/` folder, restart to apply
- **Metadata handling**: configurable keep/strip via exiftool

## API

- `POST /convert` - Convert DOCX to PDF (requires auth if API_KEY set)
- `GET /health` - Health check (no auth)

## Environment Variables

- `API_KEY` - Auth key (empty = disabled)
- `CONVERSION_TIMEOUT` - Default 120s
- `MAX_FILE_SIZE` - Default 50MB

## Adding Custom Fonts

1. Copy TTF/OTF files to `fonts/` directory
2. Restart: `docker compose restart onlyoffice`
3. Wait ~60s for font cache rebuild
