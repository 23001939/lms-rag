# Copyright (c) 2026, manhtv and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils.file_manager import get_file_path
import chromadb
from chromadb.config import Settings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

# Import các Document Loaders của Langchain
from langchain_community.document_loaders import (
    PyPDFLoader,
    UnstructuredPowerPointLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredExcelLoader,
    TextLoader,
    CSVLoader
)



# Quản lý Embedding Model toàn cục để tránh load lại nhiều lần
_embedding_model = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        # Sử dụng model embedding chuẩn để tạo vector lưu vào ChromaDB
        # _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        _embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
		
    return _embedding_model


class RAGDocument(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        category: DF.Link | None
        status: DF.Literal["Pending", "Processing", "Completed", "Failed"]
        title: DF.Data | None
        upload_tai_lieu: DF.Attach | None
    # end: auto-generated types

    def validate(self):
        """
        CƠ CHẾ CHECK TRÙNG FILE
        Kiểm tra content_hash để chặn việc upload cùng một nội dung file nhiều lần, 
        ngay cả khi người dùng cố tình đổi tên file.
        """
        # Đã sửa triệt để self.file thành self.upload_tai_lieu
        if self.upload_tai_lieu:
            # 1. Lấy mã băm (hash) của file đang được lưu
            current_content_hash = frappe.db.get_value("File", {"file_url": self.upload_tai_lieu}, "content_hash")

            if current_content_hash:
                # 2. Tìm kiếm chéo xem có RAG Document nào đang chứa file có cùng mã băm không
                duplicate = frappe.db.sql("""
                    SELECT r.name 
                    FROM `tabRAG Document` r
                    JOIN `tabFile` f ON r.upload_tai_lieu = f.file_url
                    WHERE f.content_hash = %s AND r.name != %s
                    LIMIT 1
                """, (current_content_hash, self.name or ""))

                if duplicate:
                    frappe.throw(
                        f"Nội dung file này đã tồn tại trong hệ thống tại tài liệu: <b>{duplicate[0][0]}</b>. "
                        f"Vui lòng không tải lên dữ liệu trùng lặp để tránh rác Vector Database."
                    )

    def on_update(self):
        """
        Kích hoạt Background Job khi trạng thái là Pending.
        """
        if self.upload_tai_lieu and self.status == "Pending":
            self.db_set("status", "Processing")
            frappe.enqueue(
                "lms_ai.lms_ai.doctype.rag_document.rag_document.process_and_embed_file",
                doc_name=self.name,
                queue="long",
                timeout=1500
            )

    def on_trash(self):
        """
        Xóa dữ liệu Vector khi tài liệu bị xóa.
        """
        try:
            client = get_chroma_client()
            collection = client.get_or_create_collection(name="lms_rag_docs")
            collection.delete(where={"doc_name": self.name})
            frappe.logger().info(f"Đã xóa dữ liệu vector của tài liệu {self.name}")
        except Exception as e:
            frappe.log_error(f"Lỗi xóa vector {self.name}: {str(e)}", "RAG Deletion Error")


def get_chroma_client():
    return chromadb.HttpClient(
        host='chromadb',
        port=8000, 
        settings=Settings(allow_reset=True, anonymized_telemetry=False)
    )


def process_and_embed_file(doc_name):
    """
    Background Job: Đọc File bằng Langchain Loaders -> Chunking -> Embedding -> ChromaDB
    """
    doc = frappe.get_doc("RAG Document", doc_name)
    try:
        # 1. Lấy đường dẫn tuyệt đối của file
        file_path = get_file_path(doc.upload_tai_lieu)
        lower_filename = file_path.lower()
        loaded_docs = []

        # 2. Xử lý logic Load file dựa trên đuôi mở rộng (Sử dụng Langchain)
        if lower_filename.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
            loaded_docs = loader.load()
            
        elif lower_filename.endswith((".ppt", ".pptx")):
            loader = UnstructuredPowerPointLoader(file_path)
            loaded_docs = loader.load()
            
        elif lower_filename.endswith((".doc", ".docx")):
            loader = UnstructuredWordDocumentLoader(file_path)
            loaded_docs = loader.load()
            
        elif lower_filename.endswith((".xls", ".xlsx")):
            loader = UnstructuredExcelLoader(file_path)
            loaded_docs = loader.load()
            
        elif lower_filename.endswith(".csv"):
            loader = CSVLoader(file_path, encoding='utf-8')
            loaded_docs = loader.load()
            
        elif lower_filename.endswith(".txt"):
            loader = TextLoader(file_path, encoding='utf-8')
            loaded_docs = loader.load()
            
        else:
            raise Exception(f"Định dạng file không được hỗ trợ. Vui lòng kiểm tra lại đuôi file.")

        # 3. Trích xuất toàn bộ văn bản từ các trang/sheet đã load
        text_content = ""
        for page_doc in loaded_docs:
            if page_doc.page_content:
                text_content += page_doc.page_content + "\n"

        if not text_content.strip():
            raise Exception("File trống hoặc không thể trích xuất văn bản (có thể là file ảnh/scan).")

        # 4. Chia nhỏ văn bản (Chunking)
        splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=120, separators=["\n\n", "\n", " ", ""])
        chunks = splitter.split_text(text_content)
        
        if not chunks:
            raise Exception("Quá trình chia đoạn (chunking) thất bại.")

        # 5. Tạo Embeddings thủ công từ model
        model = get_embedding_model()
        embeddings = model.encode(chunks, show_progress_bar=False).tolist()

        # 6. Lưu vào ChromaDB (đẩy cả embeddings lên để kiểm soát tuyệt đối)
        client = get_chroma_client()
        collection = client.get_or_create_collection(name="lms_rag_docs")
        
        ids = [f"{doc_name}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "category": doc.category or "Uncategorized", 
                "doc_name": doc_name,    
                "title": doc.title or "Untitled Document"
            } 
            for _ in chunks
        ]
        
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas
        )
        
        doc.db_set("status", "Completed")
        frappe.db.commit()

    except Exception as e:
        doc.db_set("status", "Failed")
        frappe.db.commit()
        frappe.log_error(frappe.get_traceback(), f"RAG Processing Error: {doc_name}")