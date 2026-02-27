import logging
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from api.config import get_settings

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)

# Constants
ALLOWED_EXTENSIONS = {".xml", ".json", ".zip", ".txt", ".csv"}
MAX_FILE_SIZE_MB = 100
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
UPLOAD_DIR = Path("uploads")

# Ensure upload directory exists
if not UPLOAD_DIR.exists():
    UPLOAD_DIR.mkdir(exist_ok=True)

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_file(file: UploadFile = File(...)):  # noqa: B008
    """
    Securely upload a file for analysis.
    Validates extension and size.
    Returns a unique file ID.
    """
    # 1. Validate Extension
    file_ext = Path(file.filename).suffix.lower() if file.filename else ""
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # 2. Validate Size (Naive check - read chunks to be safer, but SpooledTemporaryFile handles memory)
    # Applying a hard limit on the read size would be better for DoS protection.
    # For now, we'll rely on server configuration (e.g. Nginx/Uvicorn limits) and basic check.

    # Generate unique ID for this upload
    file_id = str(uuid.uuid4())
    safe_filename = f"{file_id}{file_ext}"
    destination_path = UPLOAD_DIR / safe_filename

    try:
        # Save file
        with destination_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Check size after save (or during)
        file_size = destination_path.stat().st_size
        if file_size > MAX_FILE_SIZE_BYTES:
            # Delete if too big
            destination_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Max size is {MAX_FILE_SIZE_MB}MB"
            )

        logger.info(f"File uploaded successfully: {safe_filename} ({file_size} bytes)")

        return {
            "file_id": file_id,
            "filename": file.filename,
            "saved_as": safe_filename,
            "size": file_size,
            "message": "Upload successful"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e!s}")
        # Cleanup if partial
        if destination_path.exists():
            destination_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save file"
        ) from e
class TextUploadRequest(BaseModel):
    content: str
    filename: str = "pasted_text.txt"

@router.post("/upload/text", status_code=status.HTTP_201_CREATED)
async def upload_text(request: TextUploadRequest):
    """
    Save raw text as a file for analysis.
    Useful for copy-pasting chat logs.
    """
    # Validate Extension
    file_ext = Path(request.filename).suffix.lower()
    if not file_ext:
        file_ext = ".txt"

    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Generate unique ID
    file_id = str(uuid.uuid4())
    safe_filename = f"{file_id}{file_ext}"
    destination_path = UPLOAD_DIR / safe_filename

    try:
        # Save file
        with destination_path.open("w", encoding="utf-8") as f:
            f.write(request.content)

        file_size = destination_path.stat().st_size

        # Check size (though unlikely to exceed 100MB with paste)
        if file_size > MAX_FILE_SIZE_BYTES:
            destination_path.unlink()
            raise HTTPException(status_code=413, detail="Text too large.")

        logger.info(f"Text saved: {safe_filename} ({file_size} bytes)")

        return {
            "file_id": file_id,
            "filename": request.filename,
            "saved_as": safe_filename,
            "size": file_size,
            "message": "Text saved successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Text save failed: {e!s}")
        if destination_path.exists():
            destination_path.unlink()
        raise HTTPException(status_code=500, detail="Could not save text") from e
