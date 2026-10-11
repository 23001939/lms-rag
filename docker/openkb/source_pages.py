"""Read-only page metadata for verified LMS citations; upstream APIs stay intact."""
import json

from fastapi import APIRouter, Depends, HTTPException
from openkb.api_helpers import _resolve_kb, require_bearer_token
from openkb.api_models import DocumentSourceRequest
from openkb.documents import _resolve_source_file
from openkb.state import HashRegistry

router = APIRouter()


@router.post("/lms/v1/source-pages")
def source_pages(request: DocumentSourceRequest, _: None = Depends(require_bearer_token)):
    kb = _resolve_kb(request.kb)
    meta = HashRegistry(kb / ".openkb" / "hashes.json").get(request.hash)
    if not meta:
        raise HTTPException(404, "Unknown document")
    source = _resolve_source_file(kb, meta, meta.get("doc_name", ""))
    if not source:
        raise HTTPException(404, "Missing source")
    text = source.read_text(encoding="utf-8")
    if source.suffix == ".json":
        pages = json.loads(text)
        return {"pages": [{"page": p.get("page"), "content": p.get("content", "")} for p in pages if isinstance(p, dict)]}
    return {"pages": [{"page": None, "content": text}]}
