import os
import subprocess
import tempfile
import shutil
from pathlib import Path
from dataclasses import dataclass, field

from app.config import LIBREOFFICE_PATH, CONVERSION_TIMEOUT, TEMP_DIR


class ConversionError(Exception):
    pass


@dataclass
class ConversionResult:
    pdf_content: bytes
    warnings: list[str] = field(default_factory=list)


def ensure_temp_dir():
    os.makedirs(TEMP_DIR, exist_ok=True)


def convert_docx_to_pdf(
    docx_content: bytes,
    filename: str,
    strip_metadata: bool = False
) -> ConversionResult:
    ensure_temp_dir()
    work_dir = tempfile.mkdtemp(dir=TEMP_DIR)
    warnings: list[str] = []

    try:
        input_path = Path(work_dir) / filename
        input_path.write_bytes(docx_content)

        # Build conversion command
        cmd = [
            LIBREOFFICE_PATH,
            "--headless",
            "--convert-to", "pdf",
            "--outdir", work_dir,
            str(input_path)
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=CONVERSION_TIMEOUT,
            cwd=work_dir
        )

        stderr_output = result.stderr.decode() if result.stderr else ""
        stdout_output = result.stdout.decode() if result.stdout else ""

        # Check for warnings in output (font substitutions, etc.)
        if "Warning" in stderr_output or "Warning" in stdout_output:
            for line in (stderr_output + stdout_output).split("\n"):
                if "Warning" in line or "font" in line.lower():
                    warnings.append(line.strip())

        # Handle non-zero return code with fallback attempt
        if result.returncode != 0:
            # Check if PDF was created despite error (fallback)
            pdf_filename = Path(filename).stem + ".pdf"
            pdf_path = Path(work_dir) / pdf_filename

            if pdf_path.exists():
                warnings.append(f"Conversion completed with errors: {stderr_output[:200]}")
            else:
                raise ConversionError(
                    f"LibreOffice conversion failed: {stderr_output}"
                )

        pdf_filename = Path(filename).stem + ".pdf"
        pdf_path = Path(work_dir) / pdf_filename

        if not pdf_path.exists():
            raise ConversionError("PDF file was not created")

        pdf_content = pdf_path.read_bytes()

        # Strip metadata if requested
        if strip_metadata:
            pdf_content, meta_warnings = strip_pdf_metadata(pdf_content, work_dir)
            warnings.extend(meta_warnings)

        return ConversionResult(pdf_content=pdf_content, warnings=warnings)

    except subprocess.TimeoutExpired:
        raise ConversionError(
            f"Conversion timed out after {CONVERSION_TIMEOUT} seconds"
        )
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


def strip_pdf_metadata(pdf_content: bytes, work_dir: str) -> tuple[bytes, list[str]]:
    """
    Attempt to strip metadata from PDF using exiftool or pdftk if available.
    Falls back to original content if tools not available.
    """
    warnings: list[str] = []

    # Try using exiftool if available
    try:
        pdf_path = Path(work_dir) / "temp_meta.pdf"
        pdf_path.write_bytes(pdf_content)

        result = subprocess.run(
            ["exiftool", "-all=", "-overwrite_original", str(pdf_path)],
            capture_output=True,
            timeout=30
        )

        if result.returncode == 0:
            return pdf_path.read_bytes(), warnings
        else:
            warnings.append("Could not strip metadata: exiftool failed")
            return pdf_content, warnings

    except FileNotFoundError:
        warnings.append("Metadata stripping skipped: exiftool not installed")
        return pdf_content, warnings
    except subprocess.TimeoutExpired:
        warnings.append("Metadata stripping timed out")
        return pdf_content, warnings


def check_libreoffice() -> bool:
    try:
        result = subprocess.run(
            [LIBREOFFICE_PATH, "--version"],
            capture_output=True,
            timeout=10
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False
