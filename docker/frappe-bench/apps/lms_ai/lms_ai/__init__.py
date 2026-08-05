__version__ = "0.0.1"
import frappe

# Khi bench restart hoặc worker khởi động, file __init__.py này chạy đầu tiên
try:
    # Gọi ngầm hàm lấy reranker để nó tự động download/load weights vào RAM
    from lms_ai.api import get_reranker
    get_reranker()
    from lms_ai.doctype.rag_document.rag_document import get_embedding_model
    get_embedding_model()
    frappe.logger().info(">>> LMS AI: Đã preload CrossEncoder thành công khi khởi động server! <<<")
except Exception as e:
    frappe.logger().error(f">>> LMS AI: Không thể preload CrossEncoder: {str(e)} <<<-")