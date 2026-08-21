import os
import json
import re
import frappe
from qdrant_client import QdrantClient
from qdrant_client.http import models
from openai import OpenAI
from sentence_transformers import CrossEncoder, SentenceTransformer

os.environ["no_proxy"] = "localhost,127.0.0.1,0.0.0.0,9router,qdrant,host.docker.internal"
os.environ["NO_PROXY"] = "localhost,127.0.0.1,0.0.0.0,9router,qdrant,host.docker.internal"

# ==========================================
# SINGLETON MODEL LOADERS
# ==========================================
_reranker = None
_embedding_model = None
_qdrant_client = None

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
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = QdrantClient(host='qdrant', port=6333)
    return _qdrant_client

# ==========================================
# HEURISTIC & ROUTING UTILITIES
# ==========================================
CASUAL_KEYWORDS = {
    "chào", "chào bạn", "hello", "hi", "hey", "alo",
    "cảm ơn", "cám ơn", "thanks", "thank you",
    "tạm biệt", "bye", "goodbye",
    "thời tiết", "trời đẹp", "mấy giờ", "hôm nay thế nào",
    "bạn là ai", "bạn tên gì", "ai tạo ra bạn"
}

def is_casual_query(message: str) -> bool:
    """Lọc nhanh (0ms) các câu chào hỏi, cảm ơn, thời tiết phổ thông để bỏ qua toàn bộ RAG pipeline."""
    clean_msg = message.lower().strip()
    clean_msg = re.sub(r'[^\w\s]', '', clean_msg)
    words = clean_msg.split()
    
    if len(words) <= 2 and any(kw in clean_msg for kw in ["hi", "chào", "hello", "alo", "thanks", "cảm ơn"]):
        return True
        
    return any(kw in clean_msg for kw in CASUAL_KEYWORDS)

def route_and_rewrite_query(llm_client: OpenAI, model: str, message: str, history: list) -> dict:
    """Ghép 2 bước thành 1 LLM call duy nhất: 
    1. Phân loại câu hỏi có cần tra cứu tài liệu nội bộ không (Semantic Routing).
    2. Viết lại câu hỏi độc lập ngữ cảnh nếu cần tra cứu (Query Transformation).
    """
    history_text = "\n".join([f"{h.get('role')}: {h.get('message')}" for h in history[-3:]])
    
    prompt = f"""Bạn là bộ định tuyến truy vấn (Query Router). Hãy phân tích ngữ cảnh hội thoại và câu hỏi mới nhất của người dùng.

Nhiệm vụ:
1. Đánh giá xem câu hỏi có cần tra cứu tài liệu nghiệp vụ/kỹ thuật/nội bộ không ("need_rag": true/false).
   - Đặt "need_rag": false nếu câu hỏi là chào hỏi, cảm ơn, hỏi thời tiết, toán cơ bản, hoặc kiến thức đời sống phổ thông.
   - Đặt "need_rag": true nếu câu hỏi liên quan đến kiến thức chuyên môn, quy trình, hệ thống, bài học, tài liệu.
2. Nếu "need_rag" là true, hãy viết lại câu hỏi thành một câu truy vấn tìm kiếm độc lập (Search Query) rõ nghĩa, đầy đủ chủ ngữ/vị ngữ, thay thế các đại từ như "nó", "cái này", "phần đó" bằng thực thể cụ thể dựa vào lịch sử trò chuyện.
3. Trả về định dạng JSON thuần: {{"need_rag": boolean, "search_query": string}}

Lịch sử trò chuyện gần nhất:
{history_text if history_text else "(Không có lịch sử trước đó)"}

Câu hỏi mới nhất: "{message}"
"""

    try:
        res = llm_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        parsed = json.loads(res.choices[0].message.content)
        return {
            "need_rag": bool(parsed.get("need_rag", True)),
            "search_query": str(parsed.get("search_query", message)).strip() or message
        }
    except Exception:
        # Fallback an toàn nếu LLM parse JSON lỗi
        return {"need_rag": True, "search_query": message}

# ==========================================
# RETRIEVAL & RERANKING MODULE
# ==========================================
def retrieve_and_rerank(query: str, categories: list, top_k: int = 3, score_threshold: float = 0.0):
    """Truy xuất từ Qdrant (limit=25) -> CrossEncoder Rerank -> Lọc theo ngưỡng điểm -> Trích xuất Reference."""
    client = get_qdrant_client()
    embed_model = get_embedding_model()
    reranker = get_reranker()

    query_vector = embed_model.encode(query).tolist()

    # Dynamic Filter: Lọc theo category nếu có chọn, ngược lại tìm toàn bộ collection
    qdrant_filter = None
    if categories and len(categories) > 0:
        qdrant_filter = models.Filter(
            should=[
                models.FieldCondition(key="category", match=models.MatchValue(value=cat))
                for cat in categories
            ]
        )

    # Retrieval Candidate Pool
    search_response = client.query_points(
        collection_name="lms_rag_docs",
        query=query_vector,
        query_filter=qdrant_filter,
        limit=25
    )
    search_results = search_response.points

    retrieved_items = [
        (hit.payload.get("document", ""), hit.payload)
        for hit in search_results
        if hit.payload and "document" in hit.payload
    ]

    if not retrieved_items:
        return "", []

    # Post-Retrieval: Reranking
    cross_inp = [[query, chunk] for chunk, meta in retrieved_items]
    cross_scores = reranker.predict(cross_inp)

    scored_items = list(zip(cross_scores, retrieved_items))
    scored_items.sort(key=lambda x: x[0], reverse=True)

    context_chunks = []
    references = []
    seen_docs = set()

    for score, (chunk, meta) in scored_items:
        # Lọc bỏ các chunk dưới ngưỡng (ngưỡng logit chuẩn cho model cross-encoder này là 0.0)
        if score < score_threshold:
            continue
            
        if len(context_chunks) >= top_k:
            break

        context_chunks.append(chunk)
        doc_name = meta.get("doc_name")
        doc_title = meta.get("title") or doc_name

        if doc_name and doc_name not in seen_docs:
            file_url = frappe.db.get_value("RAG Document", doc_name, "upload_tai_lieu")
            final_url = file_url if file_url else f"/app/rag-document/{doc_name}"
            references.append({
                "title": doc_title,
                "url": final_url,
                "score": float(score)
            })
            seen_docs.add(doc_name)

    context = "\n---\n".join(context_chunks)
    return context, references

# ==========================================
# FRAPPE WHITELISTED APIS
# ==========================================
@frappe.whitelist()
def get_chat_history():
    user = frappe.session.user
    if user == "Guest":
        return []
        
    return frappe.get_all(
        "LMS Chat History",
        filters={"user": user},
        fields=["role", "message"],
        order_by="creation desc",
        limit=10
    )

@frappe.whitelist()
def ask_ai(message: str, categories: list | str = None):
    try:
        user = frappe.session.user
        if user == "Guest":
            return {"source": "error", "reply": "Bạn cần đăng nhập để sử dụng tính năng này."}

        api_url = frappe.conf.get("llm_api_url")
        api_key = frappe.conf.get("llm_api_key")
        llm_api_model = frappe.conf.get("llm_api_model")
        llm_api_temperature = frappe.conf.get("llm_api_temperature") or 0.2
        llm_api_top_p = frappe.conf.get("llm_api_top_p") or 0.2

        if not api_url or not api_key:
            frappe.log_error("Chưa cấu hình 'llm_api_url' hoặc 'llm_api_key' trong site_config.json", "LLM Configuration Error")
            return {"source": "error", "reply": "Hệ thống chưa cấu hình LLM. Vui lòng liên hệ quản trị viên."}

        if isinstance(categories, str):
            categories = frappe.parse_json(categories)
        if not categories:
            categories = []

        # 1. Lấy lịch sử hội thoại gần nhất
        recent_history = frappe.get_all(
            "LMS Chat History",
            filters={"user": user},
            fields=["role", "message"],
            order_by="creation desc",
            limit=4,
            ignore_permissions=True
        )
        recent_history.reverse()

        llm_client = OpenAI(
            base_url=api_url, 
            api_key=api_key,
            timeout=60.0
        )

        context = ""
        references = []
        rewritten_query = message
        need_rag = False

        # 2. Xử lý Routing & Retrieval
        if is_casual_query(message):
            # Tầng 1: Lọc bằng quy tắc (0ms) -> Bỏ qua RAG hoàn toàn
            need_rag = False
        else:
            # Tầng 2: Semantic Router & Query Rewriting qua LLM
            route_info = route_and_rewrite_query(llm_client, llm_api_model, message, recent_history)
            need_rag = route_info.get("need_rag", True)
            rewritten_query = route_info.get("search_query", message)

            if need_rag:
                context, references = retrieve_and_rerank(
                    query=rewritten_query,
                    categories=categories,
                    top_k=3,
                    score_threshold=0.0
                )

        # 3. Xây dựng System Prompt chuẩn Grounding
        base_instruction = (
            "Bạn là trợ lý AI thông minh chuyên nghiệp.\n"
            "- Đối với câu hỏi chào hỏi, xã giao hoặc kiến thức chung đời sống: Trả lời ngắn gọn, tự nhiên, thân thiện.\n"
            "- Khi có 'Ngữ cảnh tài liệu': Hãy ưu tiên sử dụng thông tin trong tài liệu để trả lời chính xác nhất.\n"
            "- Tuyệt đối không được bịa đặt cú pháp, quy trình hoặc thông tin sai lệch về hệ thống nội bộ.\n"
            "- Nếu thông tin không có trong tài liệu hoặc không chắc chắn, hãy trả lời 'tôi không rõ' hoặc đưa ra câu hỏi làm rõ phạm vi cho người dùng."
        )

        if context:
            system_prompt = f"{base_instruction}\n\nNgữ cảnh tài liệu tra cứu được:\n{context}"
        else:
            system_prompt = (
                f"{base_instruction}\n\n"
                "Hiện không có tài liệu nội bộ nào được áp dụng cho câu hỏi này. "
                "Hãy trả lời dựa trên hiểu biết chung hoặc yêu cầu làm rõ nếu cần thiết."
            )

        messages = [{"role": "system", "content": system_prompt}]
        for log in recent_history:
            messages.append({"role": log.role, "content": log.message})
        messages.append({"role": "user", "content": message})

        # 4. Sinh câu trả lời cuối cùng
        response = llm_client.chat.completions.create(
            model=llm_api_model,
            messages=messages,
            temperature=llm_api_temperature,
            top_p=llm_api_top_p
        )

        reply_text = response.choices[0].message.content

        # 5. Lưu lịch sử chat vào Frappe DB
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
            "references": references,
            "used_rag": need_rag,
            "search_query": rewritten_query if need_rag else None
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
        return [d.category_name for d in docs if d.category_name]
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "LMS AI Get Category Error")
        return []