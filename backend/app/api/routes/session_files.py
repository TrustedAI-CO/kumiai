"""Session files API endpoints."""

import hashlib
import logging
import mimetypes
import shutil
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.file_dtos import (
    CommittedFileInfo,
    FileCommitRequest,
    FileCommitResponse,
    FilePrepareResponse,
    FileUploadError,
    PreparedFileInfo,
    SessionFileDTO,
)
from app.core.dependencies import get_db
from app.infrastructure.database.models import SessionFile, Session, Project

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sessions", tags=["session-files"])

# File upload configuration
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB per file
MAX_TOTAL_SIZE = 500 * 1024 * 1024  # 500MB total
BLOCKED_EXTENSIONS = {".exe", ".sh", ".bat", ".dll", ".so", ".dylib", ".app"}

# Temp storage for prepared uploads
TEMP_UPLOAD_DIR = Path("temp_uploads")
TEMP_UPLOAD_DIR.mkdir(exist_ok=True)


def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


@router.post("/{session_id}/files/prepare", response_model=FilePrepareResponse)
async def prepare_file_upload(
    session_id: UUID,
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Stage 1: Upload files to temporary storage.

    Files are stored temporarily and given a unique ID.
    They will be moved to permanent storage when commit is called.

    Temp files auto-expire after 1 hour if not committed.
    """
    # Verify session exists
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Create temp directory for this session
    session_temp_dir = TEMP_UPLOAD_DIR / str(session_id)
    session_temp_dir.mkdir(parents=True, exist_ok=True)

    prepared = []
    errors = []

    # Validate total size first
    total_size = sum(file.size or 0 for file in files if file.size)
    if total_size > MAX_TOTAL_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Total upload size ({total_size / 1024 / 1024:.1f}MB) exceeds limit ({MAX_TOTAL_SIZE / 1024 / 1024:.0f}MB)",
        )

    for file in files:
        try:
            # Validate file size
            if file.size and file.size > MAX_FILE_SIZE:
                errors.append(
                    FileUploadError(
                        name=file.filename or "unknown",
                        error=f"File size ({file.size / 1024 / 1024:.1f}MB) exceeds {MAX_FILE_SIZE / 1024 / 1024:.0f}MB limit",
                    )
                )
                continue

            # Validate file extension
            file_ext = Path(file.filename or "").suffix.lower()
            if file_ext in BLOCKED_EXTENSIONS:
                errors.append(
                    FileUploadError(
                        name=file.filename or "unknown",
                        error=f"File type {file_ext} not allowed for security reasons",
                    )
                )
                continue

            # Sanitize filename (prevent path traversal)
            safe_filename = Path(file.filename or "unknown").name
            if not safe_filename or safe_filename.startswith("."):
                errors.append(
                    FileUploadError(
                        name=file.filename or "unknown", error="Invalid filename"
                    )
                )
                continue

            # Generate unique temp ID
            temp_id = f"temp_{uuid.uuid4().hex[:8]}_{safe_filename}"
            temp_path = session_temp_dir / temp_id

            # Stream file to temp storage
            file_size = 0
            with temp_path.open("wb") as buffer:
                while chunk := await file.read(8192):  # 8KB chunks
                    buffer.write(chunk)
                    file_size += len(chunk)

            # Set expiry (1 hour from now)
            expires_at = datetime.utcnow() + timedelta(hours=1)

            prepared.append(
                PreparedFileInfo(
                    id=temp_id,
                    name=safe_filename,
                    size=file_size,
                    type=mimetypes.guess_type(safe_filename)[0]
                    or "application/octet-stream",
                    expires_at=expires_at.isoformat() + "Z",
                )
            )

            logger.info(
                f"Prepared temp file: {temp_path} ({file_size} bytes, expires: {expires_at})"
            )

        except Exception as e:
            logger.error(f"Failed to prepare {file.filename}: {e}")
            errors.append(
                FileUploadError(name=file.filename or "unknown", error=str(e))
            )

    return FilePrepareResponse(prepared=prepared, errors=errors)


@router.post("/{session_id}/files/commit", response_model=FileCommitResponse)
async def commit_file_upload(
    session_id: UUID,
    request: FileCommitRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Stage 2: Move prepared files from temp to permanent storage.

    Call this when user sends the message with attachments.
    Files are moved to project-dir/.sessions/{session_id}/attachments.
    """
    # Verify session exists and get project
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get project to determine storage location
    if not session.project_id:
        raise HTTPException(status_code=400, detail="Session has no associated project")

    result = await db.execute(select(Project).where(Project.id == session.project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Create attachments directory in project/.sessions/{session_id}/attachments
    project_path = Path(project.path)
    attachments_dir = project_path / ".sessions" / str(session_id) / "attachments"
    attachments_dir.mkdir(parents=True, exist_ok=True)

    session_temp_dir = TEMP_UPLOAD_DIR / str(session_id)

    committed = []
    errors = []

    for file_id in request.file_ids:
        try:
            # Security: Ensure file_id doesn't contain path traversal
            if ".." in file_id or "/" in file_id or "\\" in file_id:
                errors.append(FileUploadError(name=file_id, error="Invalid file ID"))
                continue

            temp_file = session_temp_dir / file_id

            if not temp_file.exists():
                errors.append(
                    FileUploadError(
                        name=file_id, error="Temp file not found or expired"
                    )
                )
                continue

            # Extract original filename from temp_id (format: temp_hash_originalname.ext)
            parts = file_id.split(
                "_", 2
            )  # Split into ["temp", "hash", "originalname.ext"]
            if len(parts) < 3:
                errors.append(
                    FileUploadError(name=file_id, error="Invalid temp file ID format")
                )
                continue

            original_name = parts[2]

            # Handle filename conflicts (auto-rename)
            final_name = original_name
            final_path = attachments_dir / final_name
            counter = 1
            while final_path.exists():
                stem = Path(original_name).stem
                suffix = Path(original_name).suffix
                final_name = f"{stem}_{counter}{suffix}"
                final_path = attachments_dir / final_name
                counter += 1

            # Move file from temp to attachments (efficient, no copy)
            shutil.move(str(temp_file), str(final_path))

            file_size = final_path.stat().st_size
            file_hash = calculate_file_hash(final_path)

            # Create database record
            session_file = SessionFile(
                session_id=session_id,
                filename=final_name,
                original_filename=original_name,
                file_path=str(final_path),
                file_size=file_size,
                mime_type=mimetypes.guess_type(final_name)[0]
                or "application/octet-stream",
                file_hash=file_hash,
                status="uploaded",
            )
            db.add(session_file)
            await db.flush()

            # Return absolute path so agents can access the file
            # Frontend will parse this and display it properly
            absolute_path = str(final_path)

            committed.append(
                CommittedFileInfo(
                    id=str(session_file.id),
                    name=final_name,
                    path=absolute_path,
                    size=file_size,
                    type=session_file.mime_type,
                )
            )

            logger.info(f"Committed file: {temp_file} → {final_path}")

        except Exception as e:
            logger.error(f"Failed to commit {file_id}: {e}")
            errors.append(FileUploadError(name=file_id, error=str(e)))

    await db.commit()
    return FileCommitResponse(committed=committed, errors=errors)


@router.delete("/{session_id}/files/prepare")
async def cancel_file_preparation(
    session_id: UUID,
    file_ids: List[str] = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Cancel prepared files (delete from temp storage).

    Use when user removes attachments before sending the message.
    """
    # Verify session exists
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session_temp_dir = TEMP_UPLOAD_DIR / str(session_id)

    deleted = []
    errors = []

    for file_id in file_ids:
        try:
            # Security: Ensure file_id doesn't contain path traversal
            if ".." in file_id or "/" in file_id or "\\" in file_id:
                errors.append(FileUploadError(name=file_id, error="Invalid file ID"))
                continue

            temp_file = session_temp_dir / file_id

            if temp_file.exists():
                temp_file.unlink()
                deleted.append(file_id)
                logger.info(f"Deleted temp file: {temp_file}")
            else:
                errors.append(FileUploadError(name=file_id, error="File not found"))

        except Exception as e:
            logger.error(f"Failed to delete {file_id}: {e}")
            errors.append(FileUploadError(name=file_id, error=str(e)))

    return {"deleted": deleted, "errors": errors}


@router.get("/{session_id}/files", response_model=List[SessionFileDTO])
async def list_session_files(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """List all files attached to a session."""
    result = await db.execute(
        select(SessionFile)
        .where(SessionFile.session_id == session_id)
        .order_by(SessionFile.created_at.desc())
    )
    files = result.scalars().all()
    return [SessionFileDTO.model_validate(f) for f in files]


@router.get("/{session_id}/files/{file_id}", response_model=SessionFileDTO)
async def get_session_file(
    session_id: UUID,
    file_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get details of a specific file."""
    result = await db.execute(
        select(SessionFile).where(
            SessionFile.id == file_id, SessionFile.session_id == session_id
        )
    )
    file = result.scalar_one_or_none()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    return SessionFileDTO.model_validate(file)


@router.delete("/{session_id}/files/{file_id}", status_code=204)
async def delete_session_file(
    session_id: UUID,
    file_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a file attachment."""
    result = await db.execute(
        select(SessionFile).where(
            SessionFile.id == file_id, SessionFile.session_id == session_id
        )
    )
    file = result.scalar_one_or_none()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    # Delete physical file
    try:
        file_path = Path(file.file_path)
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Deleted physical file: {file_path}")
    except Exception as e:
        logger.error(f"Failed to delete physical file: {e}")

    # Delete database record
    await db.delete(file)
    await db.commit()
