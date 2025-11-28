import os
import subprocess
import tempfile
import shutil
import uuid
import time
from pathlib import Path
from dataclasses import dataclass, field

from app.config import CONVERSION_TIMEOUT, TEMP_DIR

SHARED_DIR = os.environ.get("SHARED_DIR", "/shared")
ONLYOFFICE_HOST = os.environ.get("ONLYOFFICE_HOST", "onlyoffice")


class ConversionError(Exception):
    pass


@dataclass
class ConversionResult:
    pdf_content: bytes
    warnings: list[str] = field(default_factory=list)


def ensure_temp_dir():
    os.makedirs(TEMP_DIR, exist_ok=True)
    os.makedirs(SHARED_DIR, exist_ok=True)


def convert_docx_to_pdf(
    docx_content: bytes,
    filename: str,
    strip_metadata: bool = False
) -> ConversionResult:
    ensure_temp_dir()
    warnings: list[str] = []

    # Generate unique ID for this conversion
    job_id = str(uuid.uuid4())
    input_filename = f"{job_id}_input.docx"
    output_filename = f"{job_id}_output.pdf"
    config_filename = f"{job_id}_config.xml"

    input_path = Path(SHARED_DIR) / input_filename
    output_path = Path(SHARED_DIR) / output_filename
    config_path = Path(SHARED_DIR) / config_filename

    try:
        # Write input file to shared volume
        input_path.write_bytes(docx_content)

        # Create x2t config XML
        # Format 513 = PDF
        config_xml = f"""<?xml version="1.0" encoding="utf-8"?>
<TaskQueueDataConvert>
  <m_sFileFrom>/shared/{input_filename}</m_sFileFrom>
  <m_sFileTo>/shared/{output_filename}</m_sFileTo>
  <m_nFormatTo>513</m_nFormatTo>
</TaskQueueDataConvert>
"""
        config_path.write_text(config_xml)

        # Create marker file to trigger conversion
        marker_path = Path(SHARED_DIR) / f"{job_id}.convert"
        marker_path.write_text(config_filename)

        # Wait for conversion to complete
        done_path = Path(SHARED_DIR) / f"{job_id}.done"
        error_path = Path(SHARED_DIR) / f"{job_id}.error"

        start_time = time.time()
        while time.time() - start_time < CONVERSION_TIMEOUT:
            # Check for done signal or output file
            if done_path.exists() or output_path.exists():
                # Give it a moment to finish writing
                time.sleep(0.5)
                if output_path.exists():
                    break

            # Check for error file
            if error_path.exists():
                error_msg = error_path.read_text()
                raise ConversionError(f"OnlyOffice conversion failed: {error_msg}")

            time.sleep(0.5)
        else:
            raise ConversionError(f"Conversion timed out after {CONVERSION_TIMEOUT} seconds")

        if not output_path.exists():
            raise ConversionError("PDF file was not created")

        pdf_content = output_path.read_bytes()

        # Strip metadata if requested
        if strip_metadata:
            work_dir = tempfile.mkdtemp(dir=TEMP_DIR)
            try:
                pdf_content, meta_warnings = strip_pdf_metadata(pdf_content, work_dir)
                warnings.extend(meta_warnings)
            finally:
                shutil.rmtree(work_dir, ignore_errors=True)

        return ConversionResult(pdf_content=pdf_content, warnings=warnings)

    finally:
        # Cleanup
        for path in [input_path, output_path, config_path, done_path, error_path, marker_path]:
            try:
                path.unlink(missing_ok=True)
            except:
                pass


def strip_pdf_metadata(pdf_content: bytes, work_dir: str) -> tuple[bytes, list[str]]:
    """Strip metadata from PDF using exiftool."""
    warnings: list[str] = []

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


def check_onlyoffice() -> bool:
    """Check if OnlyOffice is available via shared volume."""
    try:
        # Check if shared directory exists and is writable
        test_file = Path(SHARED_DIR) / ".health_check"
        test_file.write_text("test")
        test_file.unlink()
        return True
    except:
        return False
