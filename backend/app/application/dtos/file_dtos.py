"""File operation DTOs."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class FileInfoDTO(BaseModel):
    """File information DTO for API responses.

    Represents metadata about a file or directory in an agent/skill workspace.
    """

    path: str = Field(..., description="Path relative to entity directory")
    name: str = Field(..., description="File or directory name")
    size: int = Field(..., description="File size in bytes (0 for directories)")
    is_directory: bool = Field(..., description="Whether this is a directory")
    modified_at: datetime = Field(..., description="Last modification timestamp")


# Session file upload DTOs
class PreparedFileInfo(BaseModel):
    """Information about a prepared (temp uploaded) file."""

    id: str = Field(..., description="Temp file ID (e.g., 'temp_abc123_data.json')")
    name: str = Field(..., description="Original filename")
    size: int = Field(..., description="File size in bytes")
    type: str = Field(..., description="MIME type")
    expires_at: str = Field(..., description="ISO 8601 timestamp when file expires")


class FileUploadError(BaseModel):
    """Error information for failed file operation."""

    name: str = Field(..., description="Filename or file ID")
    error: str = Field(..., description="Error message")


class FilePrepareResponse(BaseModel):
    """Response from file prepare endpoint."""

    prepared: List[PreparedFileInfo] = Field(default_factory=list)
    errors: List[FileUploadError] = Field(default_factory=list)


class CommittedFileInfo(BaseModel):
    """Information about a committed (moved to session) file."""

    id: str = Field(..., description="Database file ID")
    name: str = Field(..., description="Final filename")
    path: str = Field(..., description="File path on server")
    size: int = Field(..., description="File size in bytes")
    type: str = Field(..., description="MIME type")


class FileCommitRequest(BaseModel):
    """Request to commit prepared files to session."""

    file_ids: List[str] = Field(..., description="List of temp file IDs to commit")


class FileCommitResponse(BaseModel):
    """Response from file commit endpoint."""

    committed: List[CommittedFileInfo] = Field(default_factory=list)
    errors: List[FileUploadError] = Field(default_factory=list)


class SessionFileDTO(BaseModel):
    """Session file attachment DTO."""

    id: UUID
    session_id: UUID
    message_id: Optional[UUID] = None
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    mime_type: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class FileContentRequest(BaseModel):
    """Request to update or create file content."""

    file_path: str = Field(..., description="Path relative to entity directory")
    content: str = Field(..., description="File content to write")

    class Config:
        json_schema_extra = {
            "example": {
                "file_path": "prompts/system.txt",
                "content": "You are a helpful assistant...",
            }
        }


class FileContentResponse(BaseModel):
    """Response containing file content and metadata."""

    file_path: str = Field(..., description="Path relative to entity directory")
    content: str = Field(..., description="File content")
    size: int = Field(..., description="File size in bytes")

    class Config:
        json_schema_extra = {
            "example": {
                "file_path": "agent.json",
                "content": '{"name": "Alice", "role": "assistant"}',
                "size": 45,
            }
        }
