# PRD: doc-to-pdf

## 1. Introduction/Overview

**doc-to-pdf** ist ein REST API Microservice zur qualitätserhaltenden Konvertierung von Microsoft Word Dokumenten (DOCX) zu PDF. Der Service nutzt LibreOffice headless für formatgetreue Konvertierung und ist optimiert für die Integration mit n8n Workflow-Automation.

**Problem:** Automatisierte Workflows benötigen eine zuverlässige, qualitativ hochwertige DOCX→PDF Konvertierung ohne manuelle Eingriffe.

## 2. Goals

- G1: Qualitätserhaltende DOCX→PDF Konvertierung ohne Formatverlust
- G2: Einfache Integration mit n8n via REST API
- G3: Flexible Eingabequellen (Upload, URL, lokaler Pfad)
- G4: Robuste Fehlerbehandlung mit Fallback-Optionen
- G5: Sichere API mit API-Key Authentifizierung

## 3. User Stories

- **US1:** Als n8n-Workflow kann ich eine DOCX-Datei hochladen und erhalte ein PDF zurück
- **US2:** Als n8n-Workflow kann ich eine URL zu einer DOCX-Datei angeben und erhalte ein PDF zurück
- **US3:** Als Server-Prozess kann ich einen lokalen Dateipfad angeben für Batch-Verarbeitung
- **US4:** Als API-Nutzer erhalte ich bei Fehlern trotzdem ein PDF (wenn möglich) mit Warnhinweisen
- **US5:** Als Admin kann ich die API mit einem API-Key absichern

## 4. Functional Requirements

### 4.1 Eingabequellen
- **FR1:** Der Service muss Datei-Upload via multipart/form-data unterstützen
- **FR2:** Der Service muss URL-Parameter akzeptieren und die Datei herunterladen
- **FR3:** Der Service muss lokale Dateipfade akzeptieren (für Server-Side Processing)

### 4.2 Konvertierung
- **FR4:** Der Service muss LibreOffice headless für die Konvertierung nutzen
- **FR5:** Der Service muss .docx Dateien zu PDF konvertieren
- **FR6:** Der Service muss das Original-Layout bestmöglich erhalten

### 4.3 Fehlerbehandlung
- **FR7:** Bei Konvertierungsfehlern soll trotzdem ein PDF erstellt werden (Fallback)
- **FR8:** Warnungen müssen im Response-Header zurückgegeben werden
- **FR9:** Kritische Fehler (korrupte Datei, ungültiges Format) geben HTTP 4xx/5xx mit Details zurück

### 4.4 Metadaten
- **FR10:** Metadaten-Handling muss per Request-Parameter konfigurierbar sein
- **FR11:** Optionen: `metadata=keep` (default), `metadata=strip`

### 4.5 Sicherheit
- **FR12:** API-Key Authentifizierung via `X-API-Key` Header
- **FR13:** API-Key muss über Umgebungsvariable konfigurierbar sein
- **FR14:** Ohne gültigen API-Key: HTTP 401 Unauthorized

### 4.6 API Endpoints
- **FR15:** `POST /convert` - Hauptendpoint für Konvertierung
- **FR16:** `GET /health` - Health-Check (ohne Auth)

## 5. Non-Goals (Out of Scope)

- NG1: Asynchrone Verarbeitung mit Job-Queue (später erweiterbar)
- NG2: Andere Dateiformate (XLSX, PPTX) - nur DOCX
- NG3: Batch-Upload mehrerer Dateien in einem Request
- NG4: PDF-Nachbearbeitung (Wasserzeichen, Kompression)
- NG5: Benutzeroberfläche / Frontend

## 6. Technical Considerations

### Tech Stack
- **Python 3.12 + FastAPI**: Async REST API mit automatischer OpenAPI-Dokumentation
- **LibreOffice headless**: Beste Open-Source-Lösung für formatgetreue Konvertierung
- **Docker**: Container mit LibreOffice-Dependencies
- **httpx**: Für async URL-Downloads

### Deployment: Coolify auf VPS
- **Plattform**: Coolify Self-Hosted PaaS
- **Build**: Dockerfile Build Pack (Coolify baut direkt aus Git)
- **Ports**: NICHT im docker-compose.yml exponieren (Coolify handled das)
- **Env Vars**: Werden in Coolify UI konfiguriert
- **Health-Check**: Wichtig für Coolify-Monitoring

## 7. API Design

### POST /convert

**Request:**
```
Headers:
  X-API-Key: <api-key>
  Content-Type: multipart/form-data | application/json

Body (Option A - File Upload):
  file: <binary>
  metadata: keep|strip (optional, default: keep)

Body (Option B - URL):
  {
    "url": "https://example.com/document.docx",
    "metadata": "keep"
  }

Body (Option C - Local Path):
  {
    "path": "/data/documents/file.docx",
    "metadata": "keep"
  }
```

**Response (Success):**
```
Status: 200 OK
Headers:
  Content-Type: application/pdf
  Content-Disposition: attachment; filename="document.pdf"
  X-Conversion-Warnings: ["Font substitution: Arial → Liberation Sans"]
Body: <PDF binary>
```

### GET /health
```
Response: {"status": "ok", "libreoffice": "available"}
```

## 8. Success Metrics

- SM1: Konvertierung behält >95% des Original-Layouts bei
- SM2: API Response Time <10s für Dateien bis 10MB
- SM3: Service-Uptime >99%

## 9. Configuration

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `API_KEY` | (leer) | API-Key für Authentifizierung. Wenn leer: Auth deaktiviert |
| `CONVERSION_TIMEOUT` | 120 | Timeout in Sekunden |
| `MAX_FILE_SIZE` | 52428800 | Max. Dateigröße (50MB) |
| `TEMP_DIR` | /tmp/doc-to-pdf | Temp-Verzeichnis |
