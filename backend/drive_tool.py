import os
import json
from typing import Optional, List, Dict, Any
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

MIME_TYPE_MAP = {
    "pdf": "application/pdf",
    "doc": "application/vnd.google-apps.document",
    "docs": "application/vnd.google-apps.document",
    "google doc": "application/vnd.google-apps.document",
    "sheet": "application/vnd.google-apps.spreadsheet",
    "sheets": "application/vnd.google-apps.spreadsheet",
    "google sheet": "application/vnd.google-apps.spreadsheet",
    "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "slide": "application/vnd.google-apps.presentation",
    "slides": "application/vnd.google-apps.presentation",
    "presentation": "application/vnd.google-apps.presentation",
    "image": "image/jpeg",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "txt": "text/plain",
    "text": "text/plain",
    "csv": "text/csv",
    "folder": "application/vnd.google-apps.folder",
}

FRIENDLY_MIME = {
    "application/pdf": "PDF",
    "application/vnd.google-apps.document": "Google Doc",
    "application/vnd.google-apps.spreadsheet": "Google Sheet",
    "application/vnd.google-apps.presentation": "Google Slides",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "Excel",
    "image/jpeg": "Image (JPEG)",
    "image/png": "Image (PNG)",
    "text/plain": "Text File",
    "text/csv": "CSV",
    "application/vnd.google-apps.folder": "Folder",
}


def get_drive_service():
    """Build and return Google Drive API service."""
    creds_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not creds_json:
        raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON environment variable not set.")

    creds_dict = json.loads(creds_json)
    credentials = service_account.Credentials.from_service_account_info(
        creds_dict, scopes=SCOPES
    )
    service = build("drive", "v3", credentials=credentials)
    return service


def search_drive_files(
    query_string: str,
    folder_id: Optional[str] = None,
    max_results: int = 20,
) -> List[Dict[str, Any]]:
    """
    Search Google Drive using the files.list API with a q parameter.

    Args:
        query_string: A properly formatted Google Drive query string.
        folder_id: Optional folder ID to restrict search scope.
        max_results: Maximum number of results to return.

    Returns:
        List of file metadata dicts.
    """
    service = get_drive_service()

    # Add folder restriction if provided
    env_folder_id = os.environ.get("GOOGLE_DRIVE_FOLDER_ID", folder_id)
    if env_folder_id:
        folder_clause = f"'{env_folder_id}' in parents"
        if query_string:
            query_string = f"({query_string}) and {folder_clause}"
        else:
            query_string = folder_clause

    # Always exclude trashed files
    if "trashed" not in query_string:
        query_string = f"({query_string}) and trashed = false" if query_string else "trashed = false"

    try:
        results = (
            service.files()
            .list(
                q=query_string,
                pageSize=max_results,
                fields="files(id, name, mimeType, modifiedTime, size, webViewLink, iconLink, description, parents)",
                orderBy="modifiedTime desc",
            )
            .execute()
        )

        files = results.get("files", [])
        enriched = []
        for f in files:
            enriched.append(
                {
                    "id": f.get("id"),
                    "name": f.get("name"),
                    "mimeType": f.get("mimeType"),
                    "friendlyType": FRIENDLY_MIME.get(f.get("mimeType", ""), f.get("mimeType", "Unknown")),
                    "modifiedTime": f.get("modifiedTime"),
                    "size": f.get("size"),
                    "webViewLink": f.get("webViewLink"),
                    "iconLink": f.get("iconLink"),
                    "description": f.get("description", ""),
                }
            )
        return enriched

    except HttpError as e:
        raise RuntimeError(f"Google Drive API error: {e}")


def build_query_from_params(
    name: Optional[str] = None,
    name_exact: Optional[str] = None,
    file_type: Optional[str] = None,
    full_text: Optional[str] = None,
    modified_after: Optional[str] = None,
    modified_before: Optional[str] = None,
) -> str:
    """
    Helper to construct a Google Drive query string from individual parameters.
    The LLM calls this via tool calling by emitting structured params.
    """
    clauses = []

    if name_exact:
        clauses.append(f"name = '{name_exact}'")
    elif name:
        clauses.append(f"name contains '{name}'")

    if file_type:
        mime = MIME_TYPE_MAP.get(file_type.lower())
        if mime:
            clauses.append(f"mimeType = '{mime}'")

    if full_text:
        clauses.append(f"fullText contains '{full_text}'")

    if modified_after:
        clauses.append(f"modifiedTime > '{modified_after}T00:00:00'")

    if modified_before:
        clauses.append(f"modifiedTime < '{modified_before}T23:59:59'")

    return " and ".join(clauses) if clauses else ""
