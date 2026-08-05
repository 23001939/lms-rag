import frappe
import chromadb
from chromadb.config import Settings
from openai import OpenAI
from sentence_transformers import CrossEncoder
import os

os.environ["no_proxy"] = "localhost,127.0.0.1,0.0.0.0,9router,chromadb,10.21.108.233,host.docker.internal"
os.environ["NO_PROXY"] = "localhost,127.0.0.1,0.0.0.0,9router,chromadb,10.21.108.233,host.docker.internal"


_reranker = None

def get_reranker():
    global _reranker
    if _reranker is None:
        # Lần đầu gọi sẽ load model
        # _reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        _reranker = CrossEncoder('cross-encoder/mmarco-mMiniLMv2-L12-H384-v1')
    return _reranker

def get_chroma_client():
    return chromadb.HttpClient(
        host='chromadb',
        port=8000, 
        settings=Settings(allow_reset=True, anonymized_telemetry=False)
    )

# ==========================================
# 1. API LẤY LỊCH SỬ CHAT CHO FRONTEND
# ==========================================
@frappe.whitelist()
def get_chat_history():
    user = frappe.session.user
    if user == "Guest":
        return []
        
    # Lấy 10 tin nhắn gần nhất của người dùng này, sắp xếp cũ đến mới
    logs = frappe.get_all(
        "LMS Chat History",
        filters={"user": user},
        fields=["role", "message"],
        order_by="creation desc",
        limit=10
    )
    return logs

# ==========================================
# 2. API XỬ LÝ CHAT (CÓ LƯU DB & NHỚ NGỮ CẢNH)
# ==========================================
@frappe.whitelist()
def ask_ai(message: str, categories: list | str = None):
    try:
        user = frappe.session.user
        if user == "Guest":
            return {"source": "error", "reply": "Bạn cần đăng nhập để sử dụng tính năng này."}

        context = ""
        references = []
        api_key = frappe.conf.get("llm_api_key")
        if not api_key:
            fralog = "Chưa cấu hình 'llm_api_key' trong site_config.json"
            frappe.log_error(fralog, "LLM Configuration Error")
            return {"source": "error", "reply": "Hệ thống chưa cấu hình API Key cho LLM. Vui lòng liên hệ quản trị viên."}
        # Frappe có thể chuyển mảng JSON thành chuỗi, ta cần parse lại cho chắc chắn
        if isinstance(categories, str):
            categories = frappe.parse_json(categories)
            
        if not categories:
            categories = []

        # ==========================================
        # CHỈ TÌM KIẾM TÀI LIỆU NẾU CÓ CHỌN CATEGORY
        # ==========================================
        if len(categories) > 0:
            reranker = get_reranker()
            client = get_chroma_client()
            collection = client.get_collection(name="lms_rag_docs")
            
            # Dùng toán tử $in nếu có nhiều category, hoặc so sánh trực tiếp nếu chỉ có 1
            where_filter = {"category": {"$in": categories}} if len(categories) > 1 else {"category": categories[0]}
            
            # Truy xuất tài liệu
            results = collection.query(
                query_texts=[message],
                n_results=10, 
                where=where_filter 
            )
            
            retrieved_chunks = results['documents'][0] if results['documents'] else []
            retrieved_metadatas = results['metadatas'][0] if results['metadatas'] else []

            if retrieved_chunks:
                chunk_meta_pairs = list(zip(retrieved_chunks, retrieved_metadatas))
                cross_inp = [[message, chunk] for chunk, meta in chunk_meta_pairs]
                cross_scores = reranker.predict(cross_inp)
                
                scored_items = list(zip(cross_scores, chunk_meta_pairs))
                scored_items.sort(key=lambda x: x[0], reverse=True)
                top_3_items = [item for score, item in scored_items[:3]]
                
                seen_docs = set()
                
                for chunk, meta in top_3_items:
                    context += f"\n---\n{chunk}"
                    doc_name = meta.get("doc_name")
                    doc_title = meta.get("title") or doc_name
                    
                    if doc_name and doc_name not in seen_docs:
                        # LẤY ĐƯỜNG DẪN TRỰC TIẾP CỦA FILE TỪ DATABASE
                        file_url = frappe.db.get_value("RAG Document", doc_name, "upload_tai_lieu")
                        
                        # Nếu có file thì trỏ thẳng vào file, nếu không thì dùng đường dẫn mặc định
                        final_url = file_url if file_url else f"/app/rag-document/{doc_name}"
                        
                        references.append({"title": doc_title, "url": final_url})
                        seen_docs.add(doc_name)

        # ==========================================
        # LẤY NGỮ CẢNH LỊCH SỬ CHAT CHO AI
        # ==========================================
        recent_history = frappe.get_all(
            "LMS Chat History",
            filters={"user": user},
            fields=["role", "message"],
            order_by="creation desc",
            limit=3,
            ignore_permissions=True
        )
        recent_history.reverse()

        # ==========================================
        # GỌI LLM
        # ==========================================
        llm_client = OpenAI(
            base_url="http://9router:20128/v1", 
            api_key=api_key,
            timeout=60.0
        )

        base_instruction = (
            "Bạn là trợ lý AI thông minh.\n"
            "QUAN TRỌNG: Trước tiên hãy xem xét câu hỏi của người dùng. "
            "Nếu câu hỏi mang tính chất xã giao, chào hỏi hoặc không liên quan đến nội dung tài liệu, "
            "HÃY BỎ QUA 'Ngữ cảnh tài liệu' và trả lời một cách tự nhiên dựa trên kiến thức của bạn.\n"
            "Nếu ngữ cảnh có thông tin, hãy bám sát vào đó. "
            "Nếu ngữ cảnh không có hoặc thiếu thông tin, bạn **được phép** sử dụng kiến thức tổng quát sẵn có của mình để giải thích và hỗ trợ người dùng, nhưng tuyệt đối không được bịa đặt các cú pháp hoặc thông tin sai lệch về hệ thống nội bộ. "
            "Nếu hoàn toàn không chắc chắn hoặc không có căn cứ, hãy trả lời 'tôi không rõ'."
        )
        if context:
            system_prompt = (
                f"{base_instruction}\n"
                f"Dựa vào ngữ cảnh tài liệu sau đây, hãy trả lời câu hỏi của người dùng:\n{context}"
            )
        else:
            system_prompt = (
                f"{base_instruction}\n\n"
                "Hiện không có tài liệu nội bộ nào khớp với câu hỏi này. Hãy trả lời dựa trên kiến thức chung của bạn một cách ngắn gọn, chính xác."
            )
        messages = [{"role": "system", "content": system_prompt}]
        for log in recent_history:
            messages.append({"role": log.role, "content": log.message})
        
        messages.append({"role": "user", "content": message})
        # frappe.logger().info(f"--- [DEBUG RAG] messages hoàn chỉnh gửi cho LLM:\n{messages}")
        # frappe.log_error(f"--- [DEBUG RAG] messages hoàn chỉnh gửi cho LLM:\n{messages}","DEBUG RAG")
        response = llm_client.chat.completions.create(
            model="my-combo",
            messages=messages,
            temperature=0.2
        )

        reply_text = response.choices[0].message.content

        # ==========================================
        # LƯU LỊCH SỬ VÀO DATABASE
        # ==========================================
        frappe.get_doc({
            "doctype": "LMS Chat History",
            "user": user,
            "role": "user",
            "message": message
        }).insert(ignore_permissions=True)
        
        frappe.get_doc({
            "doctype": "LMS Chat History",
            "user": user,
            "role": "assistant",
            "message": reply_text
        }).insert(ignore_permissions=True)
        
        frappe.db.commit()

        return {
            "source": "api", 
            "reply": reply_text,
            "references": references
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "LMS AI Chat Error")
        return {"source": "error", "reply": f"Có lỗi xảy ra: {str(e)}"}
    
@frappe.whitelist()
def get_categories():
    try:
        # Lấy tất cả category từ RAG Category, ignore_permissions=True để ai cũng xem được list này
        docs = frappe.get_all(
            "RAG Category", 
            fields=["category_name"], 
            distinct=True, 
            ignore_permissions=True
        )
        
        # Lọc ra danh sách mảng các chuỗi category không bị rỗng
        categories = [d.category_name for d in docs if d.category_name]
        return categories
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "LMS AI Get Category Error")
        return []