import os

LIBREOFFICE_PATH = os.getenv("LIBREOFFICE_PATH", "soffice")
CONVERSION_TIMEOUT = int(os.getenv("CONVERSION_TIMEOUT", "120"))
TEMP_DIR = os.getenv("TEMP_DIR", "/tmp/doc-to-pdf")
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", str(50 * 1024 * 1024)))  # 50MB

# API Key for authentication (empty = auth disabled for development)
API_KEY = os.getenv("API_KEY", "")
