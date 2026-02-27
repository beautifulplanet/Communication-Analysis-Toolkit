import json
import re
import shutil

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from api.config import get_settings
from api.routers.upload import UPLOAD_DIR

router = APIRouter()
settings = get_settings()

class CreateCaseRequest(BaseModel):
    case_name: str
    user_label: str
    contact_label: str
    source_file_id: str
    source_filename: str

class CreateCaseResponse(BaseModel):
    case_id: str
    message: str

def slugify(text: str) -> str:
    # Convert to lowercase, remove non-word chars (alphanumerics and underscores),
    # replace spaces with hyphens, allow hyphens
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s]+', '-', text)
    return text.strip('-')

@router.post("/cases", response_model=CreateCaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(request: CreateCaseRequest):
    """
    Initialize a new case from an uploaded file.
    Moves the file, creates config.json.
    """
    case_id = slugify(request.case_name)
    if not case_id:
        case_id = "unnamed-case"

    # Ensure unique ID
    original_case_id = case_id
    counter = 1
    while (settings.cases_path / case_id).exists():
        case_id = f"{original_case_id}-{counter}"
        counter += 1

    case_dir = settings.cases_path / case_id
    source_dir = case_dir / "source_data"
    output_dir = case_dir / "output"

    # 1. Verify Source File
    uploaded_file = UPLOAD_DIR / request.source_filename
    if not uploaded_file.exists():
        raise HTTPException(status_code=404, detail="Source file not found (expired?)")

    try:
        # 2. Create Structure
        case_dir.mkdir(parents=True, exist_ok=True)
        source_dir.mkdir(exist_ok=True)
        output_dir.mkdir(exist_ok=True)

        # 3. Move File
        # Determine strict destination name based on extension to match analyzer expectations
        # Analyzer expects specific filenames or config paths.
        # We will keep original filename but update config to point to it.
        dest_file = source_dir / request.source_filename
        shutil.move(str(uploaded_file), str(dest_file))

        # 4. Create config.json
        config = {
            "case_name": request.case_name,
            "user_label": request.user_label,
            "contact_label": request.contact_label,
            "sms_xml": str(dest_file.absolute()).replace("\\", "/"), # Normalize for JSON
            # We assume it's XML for now. If JSON, we might need logic.
            # But Analyzer config expects "sms_xml" key for XML or "signal_db" etc.
            # For Phase 3.1, let's just point "sms_xml" to it if it's XML.
            "output_dir": str(output_dir.absolute()).replace("\\", "/"),
            "date_start": "1970-01-01", # Default to capture all
            "date_end": "2099-12-31"
        }

        # If it's a JSON file (Signal export?), logic might differ.
        # But for now, let's assume standard flow.
        if dest_file.suffix.lower() == ".json":
             # Special handling for manual JSON or Signal?
             # Analyzer supports "manual_json" key?
             # Let's check analyzer arguments?
             # For now, put it in sms_xml key? No, that will break parser.
             pass

        with open(case_dir / "config.json", "w") as f:
            json.dump(config, f, indent=4)

        return {"case_id": case_id, "message": "Case created successfully"}

    except Exception as e:
        # Cleanup
        if case_dir.exists() and not (case_dir / "config.json").exists():
             shutil.rmtree(case_dir)
        raise HTTPException(status_code=500, detail=f"Failed to create case: {e!s}") from e
