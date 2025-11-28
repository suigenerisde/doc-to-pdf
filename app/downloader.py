import httpx
from pathlib import Path
from urllib.parse import urlparse

from app.config import MAX_FILE_SIZE, CONVERSION_TIMEOUT


class DownloadError(Exception):
    pass


async def download_from_url(url: str) -> tuple[bytes, str]:
    parsed = urlparse(url)
    if not parsed.scheme in ("http", "https"):
        raise DownloadError("Only HTTP/HTTPS URLs are supported")

    filename = Path(parsed.path).name
    if not filename:
        filename = "document.docx"

    if not filename.lower().endswith(".docx"):
        raise DownloadError("URL must point to a .docx file")

    try:
        async with httpx.AsyncClient(timeout=CONVERSION_TIMEOUT) as client:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()

            content_length = response.headers.get("content-length")
            if content_length and int(content_length) > MAX_FILE_SIZE:
                raise DownloadError(
                    f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
                )

            content = response.content
            if len(content) > MAX_FILE_SIZE:
                raise DownloadError(
                    f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
                )

            return content, filename

    except httpx.HTTPStatusError as e:
        raise DownloadError(f"HTTP error {e.response.status_code}: {e.response.reason_phrase}")
    except httpx.RequestError as e:
        raise DownloadError(f"Failed to download file: {str(e)}")


def read_local_file(path: str) -> tuple[bytes, str]:
    file_path = Path(path)

    if not file_path.exists():
        raise DownloadError(f"File not found: {path}")

    if not file_path.is_file():
        raise DownloadError(f"Not a file: {path}")

    if not file_path.suffix.lower() == ".docx":
        raise DownloadError("Only .docx files are supported")

    if file_path.stat().st_size > MAX_FILE_SIZE:
        raise DownloadError(
            f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
        )

    return file_path.read_bytes(), file_path.name
