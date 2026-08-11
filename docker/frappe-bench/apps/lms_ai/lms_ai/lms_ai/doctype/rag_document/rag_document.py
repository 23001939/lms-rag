# Copyright (c) 2026, manhtv and contributors
# For license information, please see license.txt

import frappe
import uuid
from frappe.model.document import Document
from frappe.utils.file_manager import get_file_path
from qdrant_client import QdrantClient
from qdrant_client.http import models
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

from langchain_community.document_loaders import (
    PyPDFLoader,
    UnstructuredPowerPointLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredExcelLoader,
    TextLoader,
    CSVLoader
)

_embedding_model = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    return _embedding_model

def get_qdrant_client():
    return QdrantClient(host='qdrant', port=6333)

def ensure_qdrant_collection_exists(client: QdrantClient, vector_size: int = 384):
    collection_name = "lms_rag_docs"
    collections = client.get_collections().collections
    exists = any(col.name == collection_name for col in collections)
    
    if not exists:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=vector_size,
                distance=models.Distance.COSINE
            )
        )


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
        if not self.title and self.upload_tai_lieu: # Thay 'upload_tai_lieu' bằng tên field thực tế
            file_url = self.upload_tai_lieu
            
            # Cắt lấy tên file và bỏ đuôi mở rộng
            file_name_with_ext = file_url.split('/')[-1]
            import os
            file_name_clean = os.path.splitext(file_name_with_ext)[0]
            
            # Làm sạch chuỗi (Bỏ gạch dưới, gạch ngang, viết hoa chữ cái đầu)
            self.title = file_name_clean.replace("_", " ").replace("-", " ").capitalize()
        if self.upload_tai_lieu:
            current_content_hash = frappe.db.get_value("File", {"file_url": self.upload_tai_lieu}, "content_hash")

            if current_content_hash:
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
        if self.upload_tai_lieu and self.status == "Pending":
            self.db_set("status", "Processing")
            frappe.enqueue(
                "lms_ai.lms_ai.doctype.rag_document.rag_document.process_and_embed_file",
                doc_name=self.name,
                queue="long",
                timeout=1500
            )

    def on_trash(self):
        try:
            client = get_qdrant_client()
            client.delete(
                collection_name="lms_rag_docs",
                points_selector=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="doc_name",
                            match=models.MatchValue(value=self.name)
                        )
                    ]
                )
            )
            frappe.logger().info(f"Đã xóa dữ liệu vector của tài liệu {self.name} khỏi Qdrant")
        except Exception as e:
            frappe.log_error(f"Lỗi xóa vector {self.name}: {str(e)}", "RAG Deletion Error")


def process_and_embed_file(doc_name):
    doc = frappe.get_doc("RAG Document", doc_name)
    try:
        file_path = get_file_path(doc.upload_tai_lieu)
        lower_filename = file_path.lower()
        loaded_docs = []

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
            raise Exception("Định dạng file không được hỗ trợ.")

        text_content = ""
        for page_doc in loaded_docs:
            if page_doc.page_content:
                text_content += page_doc.page_content + "\n"

        if not text_content.strip():
            raise Exception("File trống hoặc không thể trích xuất văn bản.")

        splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=120, separators=["\n\n", "\n", " ", ""])
        chunks = splitter.split_text(text_content)
        
        if not chunks:
            raise Exception("Quá trình chia đoạn (chunking) thất bại.")

        # 1. Tạo Embeddings từ SentenceTransformer
        model = get_embedding_model()
        embeddings = model.encode(chunks, show_progress_bar=False).tolist()

        # 2. Lưu vào Qdrant chuẩn API
        client = get_qdrant_client()
        ensure_qdrant_collection_exists(client, vector_size=len(embeddings[0]))

        points = []
        for i, (chunk, vector) in enumerate(zip(chunks, embeddings)):
            # Qdrant yêu cầu ID dạng UUID hoặc integer, tạo UUID cố định từ tên chunk
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{doc_name}_chunk_{i}"))
            points.append(
                models.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "document": chunk,
                        "category": doc.category or "Uncategorized",
                        "doc_name": doc_name,
                        "title": doc.title or "Untitled Document"
                    }
                )
            )

        client.upsert(
            collection_name="lms_rag_docs",
            points=points
        )
        
        doc.db_set("status", "Completed")
        frappe.db.commit()

    except Exception as e:
        doc.db_set("status", "Failed")
        frappe.db.commit()
        frappe.log_error(frappe.get_traceback(), f"RAG Processing Error: {doc_name}")