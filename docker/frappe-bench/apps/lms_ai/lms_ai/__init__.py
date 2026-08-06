__version__ = "0.0.1"
import frappe

# Kiểm tra nếu không phải trong môi trường CLI đơn thuần thì mới preload
try:
    # Gọi ngầm hàm để preload weights vào RAM cho worker hiện tại
    from lms_ai.api import get_reranker, get_embedding_model
    
    get_reranker()
    get_embedding_model()
    
    frappe.logger().info(">>> LMS AI: Preload Reranker & Embedding model thành công! <<<")
except Exception as e:
    # Chỉ ghi log warning/error chứ không chặn quá trình khởi động server
    frappe.logger().warning(f">>> LMS AI: Chưa thể preload Model (có thể do đang chạy CLI/Migrate): {str(e)} <<<")