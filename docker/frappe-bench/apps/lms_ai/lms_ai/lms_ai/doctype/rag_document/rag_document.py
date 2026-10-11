import frappe
from frappe.model.document import Document
from lms_ai.openkb_client import file_data
from lms_ai.openkb_jobs import queue_document


class RAGDocument(Document):
    def validate(self):
        if self.upload_tai_lieu:
            filename, _, digest, _ = file_data(self)
            if not self.title:
                self.title = filename
            previous = self.get_doc_before_save()
            changed = not previous or previous.upload_tai_lieu != self.upload_tai_lieu
            if changed or digest != self.openkb_hash:
                self.status = "Pending"
                self.openkb_kb = None
                self.openkb_hash = None
                self.indexed_at = None
                self.index_error = None

    def on_update(self):
        if self.upload_tai_lieu and self.status == "Pending":
            queue_document(self.name)

    @frappe.whitelist()
    def retry_openkb(self):
        self.check_permission("write")
        if self.status == "Processing":
            frappe.throw("Tài liệu đang được xử lý.")
        queue_document(self.name)
        return {"status": "Processing"}


def process_and_embed_file(doc_name):
    # Compatibility with jobs queued by the old controller before deployment.
    from lms_ai.openkb_jobs import index_document
    return index_document(doc_name)
