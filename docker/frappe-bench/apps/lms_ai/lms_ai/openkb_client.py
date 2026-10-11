"""Server-only OpenKB adapter. Credentials never reach the browser."""
import hashlib
import os
from pathlib import Path

import frappe
import requests

SUPPORTED = {".pdf", ".md", ".markdown", ".docx", ".pptx", ".xlsx", ".xls", ".html", ".htm", ".txt", ".csv"}


class OpenKBError(RuntimeError):
    def __init__(self, status, endpoint):
        self.status = status
        super().__init__(f"OpenKB lỗi {status} tại {endpoint}. Kiểm tra logs OpenKB/9Router.")


def call(endpoint, payload=None, *, files=None):
    token = os.environ.get("OPENKB_API_TOKEN")
    base = os.environ.get("OPENKB_API_URL", "http://openkb:7566").rstrip("/")
    if not token:
        raise RuntimeError("Thiếu cấu hình OPENKB_API_TOKEN cho Frappe.")
    try:
        with requests.Session() as session:
            session.trust_env = False
            response = session.post(
                base + endpoint, headers={"Authorization": "Bearer " + token},
                json=None if files else payload, data=payload if files else None,
                files=files, timeout=(10, 3300),
            )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        status = exc.response.status_code if exc.response is not None else "kết nối/timeout"
        raise OpenKBError(status, endpoint) from None


def file_data(doc):
    """Resolve a saved File, never fetch an arbitrary URL from user input."""
    if not doc.upload_tai_lieu or not doc.upload_tai_lieu.startswith(("/files/", "/private/files/")):
        raise ValueError("Tài liệu phải là file đã upload vào LMS.")
    file_id = frappe.db.get_value("File", {"file_url": doc.upload_tai_lieu}, "name")
    if not file_id:
        raise ValueError("Không tìm thấy File của tài liệu.")
    file = frappe.get_doc("File", file_id)
    suffix = Path(file.file_name).suffix.lower()
    if suffix not in SUPPORTED:
        raise ValueError("OpenKB chưa hỗ trợ định dạng này. Hãy chuyển .doc/.ppt sang .docx/.pptx.")
    content = file.get_content()
    if isinstance(content, str):
        content = content.encode("utf-8")
    digest = hashlib.sha256(content).hexdigest()
    upload_name = f"{doc.name}_{digest[:12]}{suffix}"
    return file.file_name, content, digest, upload_name


def scope_key(docs):
    identity = [(doc.name, doc.openkb_hash) for doc in sorted(docs, key=lambda d: d.name)]
    return hashlib.sha256(frappe.as_json([frappe.local.site, identity]).encode()).hexdigest()


def ensure_kb(kb, docs, *, compile_missing=True):
    try:
        indexed = call("/api/v1/list", {"kb": kb})["documents"]
    except OpenKBError as exc:
        if exc.status != 400:
            raise
        try:
            call("/api/v1/init", {"kb": kb})
        except OpenKBError as init_error:
            if init_error.status != 400:
                raise
            # Another worker may have initialized the same deterministic KB.
        indexed = call("/api/v1/list", {"kb": kb})["documents"]
    wanted = {doc.openkb_hash for doc in docs}
    actual = {item["hash"] for item in indexed}
    if actual - wanted:
        raise ValueError("KB chứa file ngoài phạm vi lựa chọn; đã chặn truy vấn.")
    for doc in docs:
        _, content, digest, name = file_data(doc)
        if digest != doc.openkb_hash:
            raise ValueError("File đã thay đổi; hãy xử lý lại tài liệu trước khi hỏi.")
        if doc.openkb_hash in actual:
            continue
        if not compile_missing:
            return False
        result = call("/api/v1/add", {"kb": kb, "stream": "false"}, files=[("files", (name, content))])
        if result.get("failed_count") or not result.get("files"):
            raise RuntimeError("OpenKB chưa compile thành công. Kiểm tra logs OpenKB/9Router rồi thử lại.")
        actual.add(digest)
    indexed = call("/api/v1/list", {"kb": kb})["documents"]
    if {item["hash"] for item in indexed} != wanted:
        raise RuntimeError("OpenKB chưa có đủ chính xác các file được chọn.")
    return indexed
