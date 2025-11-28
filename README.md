# doc-to-pdf

REST API Microservice zur qualitätserhaltenden DOCX→PDF Konvertierung.

## Quick Start

```bash
docker compose up -d
```

Der Service ist dann unter `http://localhost:8000` erreichbar.

## API

### POST /convert

Konvertiert eine DOCX-Datei zu PDF. Unterstützt drei Eingabemodi:

**1. Datei-Upload:**
```bash
curl -X POST "http://localhost:8000/convert" \
  -H "X-API-Key: your-secret-key" \
  -F "file=@dokument.docx" \
  -o dokument.pdf
```

**2. URL:**
```bash
curl -X POST "http://localhost:8000/convert" \
  -H "X-API-Key: your-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/dokument.docx"}' \
  -o dokument.pdf
```

**3. Lokaler Pfad:**
```bash
curl -X POST "http://localhost:8000/convert" \
  -H "X-API-Key: your-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"path": "/data/dokument.docx"}' \
  -o dokument.pdf
```

**Optionen:**
- `metadata=keep` (default) - Metadaten behalten
- `metadata=strip` - Metadaten entfernen

### GET /health

Health-Check Endpoint (ohne Authentifizierung).

```bash
curl http://localhost:8000/health
```

Response:
```json
{"status": "ok", "libreoffice": "available"}
```

## n8n Integration

HTTP Request Node:
- **Method**: POST
- **URL**: `http://doc-to-pdf:8000/convert`
- **Headers**: `X-API-Key: your-secret-key`
- **Body Content Type**: Form-Data
- **Form Parameter**: `file` (Binary)
- **Response Format**: File

## Konfiguration

Umgebungsvariablen:

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `API_KEY` | (leer) | API-Key für Auth. Leer = Auth deaktiviert |
| `CONVERSION_TIMEOUT` | 120 | Timeout in Sekunden |
| `MAX_FILE_SIZE` | 52428800 | Max. Dateigröße (50MB) |
| `TEMP_DIR` | /tmp/doc-to-pdf | Temp-Verzeichnis |

## Coolify Deployment

1. Neues Projekt in Coolify erstellen
2. Git Repository verbinden
3. Build Pack: **Dockerfile** auswählen
4. Environment Variables setzen:
   - `API_KEY`: Sicheren Key generieren
5. Domain zuweisen
6. Deploy!

**Hinweis:** Verwende `docker-compose.coolify.yml` oder das Dockerfile direkt. Ports werden von Coolify automatisch geroutet.

## Entwicklung

Lokale Installation:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Benötigt LibreOffice auf dem System.

## Lizenz

MIT
