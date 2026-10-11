"""Background ingestion, including documents previously indexed in Qdrant."""
import hashlib

import frappe
from lms_ai.openkb_client import ensure_kb, file_data


def queue_document(name):
    url = frappe.db.get_value("RAG Document", name, "upload_tai_lieu") or ""
    revision = hashlib.sha256(url.encode()).hexdigest()[:16]
    frappe.db.set_value("RAG Document", name, {"status": "Processing", "index_error": ""}, update_modified=False)
    frappe.enqueue(
        "lms_ai.openkb_jobs.index_document", name=name, queue="long", timeout=3600,
        enqueue_after_commit=True, job_id=f"openkb-index:{name}:{revision}", deduplicate=True,
    )


def index_document(name):
    if not frappe.db.exists("RAG Document", name):
        return
    try:
        with frappe.cache.lock(frappe.cache.make_key("openkb:compile"), timeout=3600, blocking_timeout=3500):
            doc = frappe.get_doc("RAG Document", name)
            url = doc.upload_tai_lieu
            _, _, digest, _ = file_data(doc)
            doc.openkb_hash = digest
            frappe.db.set_value("RAG Document", name, {"openkb_hash": digest, "status": "Processing"}, update_modified=False)
            frappe.db.commit()
            namespace = hashlib.sha256(f"{frappe.local.site}:{name}:{digest}".encode()).hexdigest()
            kb = "lms-doc-" + namespace
            ensure_kb(kb, [doc])
            doc.reload()
            if doc.upload_tai_lieu != url or file_data(doc)[2] != digest:
                frappe.db.set_value("RAG Document", name, "status", "Pending", update_modified=False)
                frappe.db.commit()
                return
            frappe.db.set_value("RAG Document", name, {
                "status": "Completed", "openkb_kb": kb, "openkb_hash": digest,
                "indexed_at": frappe.utils.now_datetime(), "index_error": "",
            }, update_modified=False)
            frappe.db.commit()
    except Exception as exc:
        frappe.db.rollback()
        if frappe.db.exists("RAG Document", name):
            current_url = frappe.db.get_value("RAG Document", name, "upload_tai_lieu")
            changed = "url" in locals() and current_url != url
            values = {"status": "Pending", "index_error": ""} if changed else {"status": "Failed", "index_error": str(exc)[:1000]}
            frappe.db.set_value("RAG Document", name, values, update_modified=False)
            frappe.db.commit()
        frappe.log_error(title="OpenKB document processing", message=frappe.get_traceback())


def migrate_documents():
    for row in frappe.get_all("RAG Document", fields=["name", "upload_tai_lieu", "openkb_kb", "openkb_hash", "index_error", "status"]):
        not_attempted = not row.openkb_hash and not row.index_error
        if row.upload_tai_lieu and not row.openkb_kb and (not_attempted or row.status in ("Pending", "Processing")):
            queue_document(row.name)
    frappe.db.commit()


def recover_pending():
    # Failed documents require an explicit Retry; recover jobs interrupted by restart.
    for name in frappe.get_all("RAG Document", filters={"status": ["in", ["Pending", "Processing"]]}, pluck="name"):
        queue_document(name)
    frappe.db.commit()
