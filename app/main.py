import json
from enum import Enum
from typing import Optional

from fastapi import FastAPI, UploadFile, HTTPException, Form, Body
from fastapi.responses import Response
from pydantic import BaseModel

from app.config import MAX_FILE_SIZE
from app.converter import convert_docx_to_pdf, check_onlyoffice, ConversionError
from app.downloader import download_from_url, read_local_file, DownloadError
from app.auth import APIKeyMiddleware

app = FastAPI(
    title="doc-to-pdf",
    description="DOCX to PDF conversion service",
    version="1.0.0"
)

# Add API Key authentication middleware
app.add_middleware(APIKeyMiddleware)


class MetadataOption(str, Enum):
    keep = "keep"
    strip = "strip"


class UrlConvertRequest(BaseModel):
    url: str
    metadata: MetadataOption = MetadataOption.keep


class PathConvertRequest(BaseModel):
    path: str
    metadata: MetadataOption = MetadataOption.keep


@app.get("/health")
async def health():
    converter_available = check_onlyoffice()
    return {
        "status": "ok" if converter_available else "degraded",
        "onlyoffice": "available" if converter_available else "unavailable"
    }


@app.post("/convert")
async def convert(
    file: Optional[UploadFile] = None,
    metadata: MetadataOption = Form(default=MetadataOption.keep),
    body: Optional[dict] = Body(default=None)
):
    """
    Convert DOCX to PDF.

    Supports three input modes:
    - File upload: multipart/form-data with 'file' field
    - URL: JSON body with 'url' field
    - Local path: JSON body with 'path' field
    """
    content: bytes
    filename: str
    strip_metadata = metadata == MetadataOption.strip

    # Determine input source
    if file and file.filename:
        # Mode: File upload
        content, filename = await _handle_file_upload(file)
    elif body:
        # Mode: URL or Path (JSON body)
        if "url" in body:
            content, filename = await _handle_url(body)
            if "metadata" in body:
                strip_metadata = body["metadata"] == "strip"
        elif "path" in body:
            content, filename = _handle_path(body)
            if "metadata" in body:
                strip_metadata = body["metadata"] == "strip"
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid request: provide 'file', 'url', or 'path'"
            )
    else:
        raise HTTPException(
            status_code=400,
            detail="No input provided. Use file upload, url, or path."
        )

    # Convert to PDF
    try:
        result = convert_docx_to_pdf(content, filename, strip_metadata)
    except ConversionError as e:
        raise HTTPException(status_code=500, detail=str(e))

    pdf_filename = filename.rsplit(".", 1)[0] + ".pdf"

    # Build response headers
    headers = {
        "Content-Disposition": f'attachment; filename="{pdf_filename}"'
    }

    # Add warnings header if any
    if result.warnings:
        headers["X-Conversion-Warnings"] = json.dumps(result.warnings)

    return Response(
        content=result.pdf_content,
        media_type="application/pdf",
        headers=headers
    )


async def _handle_file_upload(file: UploadFile) -> tuple[bytes, str]:
    """Handle file upload input."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    if not file.filename.lower().endswith(".docx"):
        raise HTTPException(
            status_code=400,
            detail="Only .docx files are supported"
        )

    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
        )

    return content, file.filename


async def _handle_url(body: dict) -> tuple[bytes, str]:
    """Handle URL input."""
    url = body.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    try:
        return await download_from_url(url)
    except DownloadError as e:
        raise HTTPException(status_code=400, detail=str(e))


def _handle_path(body: dict) -> tuple[bytes, str]:
    """Handle local path input."""
    path = body.get("path")
    if not path:
        raise HTTPException(status_code=400, detail="Path is required")

    try:
        return read_local_file(path)
    except DownloadError as e:
        raise HTTPException(status_code=400, detail=str(e))
