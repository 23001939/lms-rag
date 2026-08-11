import frappe
from qdrant_client import QdrantClient
from qdrant_client.http import models
from openai import OpenAI
from sentence_transformers import CrossEncoder, SentenceTransformer
import os

os.environ["no_proxy"] = "localhost,127.0.0.1,0.0.0.0,9router,qdrant,host.docker.internal"
os.environ["NO_PROXY"] = "localhost,127.0.0.1,0.0.0.0,9router,qdrant,host.docker.internal"

_reranker = None
_embedding_model = None

def get_reranker():
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoder('cross-encoder/mmarco-mMiniLMv2-L12-H384-v1')
    return _reranker

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    return _embedding_model

def get_qdrant_client():
    return QdrantClient(host='qdrant', port=6333)

# ==========================================
# 1. API LẤY LỊCH SỬ CHAT CHO FRONTEND
# ==========================================
@frappe.whitelist()
def get_chat_history():
    user = frappe.session.user
    if user == "Guest":
        return []
        
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
        api_url = frappe.conf.get("llm_api_url")
        api_key = frappe.conf.get("llm_api_key")
        llm_api_model = frappe.conf.get("llm_api_model")
        llm_api_temperature = frappe.conf.get("llm_api_temperature") or 0.2
        llm_api_topp = frappe.conf.get("llm_api_mollm_api_toppdel") or 0.2

        if not api_url or not api_key:
            fralog = "Chưa cấu hình 'llm_api_url' hoặc 'llm_api_key' trong site_config.json"
            frappe.log_error(fralog, "LLM Configuration Error")
            return {"source": "error", "reply": "Hệ thống chưa cấu hình LLM. Vui lòng liên hệ quản trị viên."}

        if isinstance(categories, str):
            categories = frappe.parse_json(categories)
            
        if not categories:
            categories = []

        # ==========================================
        # CHỈ TÌM KIẾM TÀI LIỆU NẾU CÓ CHỌN CATEGORY
        # ==========================================
        if len(categories) > 0:
            reranker = get_reranker()
            embed_model = get_embedding_model()
            client = get_qdrant_client()
            
            # Tạo vector embedding cho câu hỏi
            query_vector = embed_model.encode(message).tolist()
            
            # Xây dựng điều kiện lọc (Filter) cho Qdrant
            qdrant_filter = models.Filter(
                should=[
                    models.FieldCondition(
                        key="category",
                        match=models.MatchValue(value=cat)
                    )
                    for cat in categories
                ]
            )
            
            # Truy vấn Qdrant bằng query_points (Thay thế cho client.search cũ)
            search_response = client.query_points(
                collection_name="lms_rag_docs",
                query=query_vector,
                query_filter=qdrant_filter,
                limit=10
            )
            search_results = search_response.points
            
            retrieved_chunks = [hit.payload["document"] for hit in search_results if hit.payload and "document" in hit.payload]
            retrieved_metadatas = [hit.payload for hit in search_results if hit.payload]

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
                        file_url = frappe.db.get_value("RAG Document", doc_name, "upload_tai_lieu")
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
            base_url=api_url, 
            api_key=api_key,
            timeout=60.0
        )

        base_instruction = (
            "Bạn là trợ lý AI thông minh.\n"
            "QUAN TRỌNG: Trước tiên hãy xem xét câu hỏi của người dùng. "
            "Nếu câu hỏi mang tính chất xã giao, chào hỏi hoặc không liên quan đến nội dung tài liệu HÃY BỎ QUA 'Ngữ cảnh tài liệu' để trả lời ngắn gọn dựa trên kiến thức của bạn, "
            "Nếu ngữ cảnh có thông tin, hãy bám sát vào đó. "
            "Nếu ngữ cảnh không có hoặc thiếu thông tin, bạn **được phép** sử dụng kiến thức tổng quát sẵn có của mình để giải thích và hỗ trợ người dùng, nhưng tuyệt đối không được bịa đặt các cú pháp hoặc thông tin sai lệch về hệ thống nội bộ."
            "Nếu không chắc chắn hoặc không có căn cứ, hãy trả lời 'tôi không rõ' hoặc đưa ra câu hỏi làm rõ phạm vi cần trả lời cho người dùng."
        )
        if context:
            system_prompt = (
                f"{base_instruction}\n"
                f"Ngữ cảnh tài liệu:\n{context}"
            )
        else:
            system_prompt = (
                f"{base_instruction}\n\n"
                "Hiện không có tài liệu nội bộ nào khớp với câu hỏi này. Hãy trả lời dựa trên kiến thức chung của bạn một cách ngắn gọn, chính xác hoặc đưa ra câu hỏi làm rõ phạm vi cần trả lời cho người dùng."
            )
        messages = [{"role": "system", "content": system_prompt}]
        for log in recent_history:
            messages.append({"role": log.role, "content": log.message})
        
        messages.append({"role": "user", "content": message})
        
        response = llm_client.chat.completions.create(
            model=llm_api_model,
            messages=messages,
            temperature=llm_api_temperature,        
            top_p=llm_api_topp
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
        docs = frappe.get_all(
            "RAG Category", 
            fields=["category_name"], 
            distinct=True, 
            ignore_permissions=True
        )
        categories = [d.category_name for d in docs if d.category_name]
        return categories
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "LMS AI Get Category Error")
        return []