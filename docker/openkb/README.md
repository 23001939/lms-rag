# OpenKB in the LMS Compose stack

The image builds VectifyAI/OpenKB at commit
`ff54396e575ee6feb0113b631a34caa082b441cc`, including its Knowledge Workbench.
OpenKB uses the existing 9Router gateway; it does not need a LiteLLM Proxy
container. Its Python dependencies are isolated from the Frappe Bench environment.

## Sử dụng trong LMS

1. Tải lại trang LMS bằng **Ctrl+F5** để nhận chat mới.
2. System Manager mở **RAG Document**, upload file và lưu. Đường dẫn file gốc
   vẫn nằm ở `upload_tai_lieu`; việc xử lý chạy nền sau khi lưu thành công.
3. Chờ trạng thái **Completed**. Nếu **Failed**, đọc `Processing error`,
   kiểm tra logs rồi bấm **Xử lý lại với OpenKB**.
4. Mở **Hỏi tài liệu**, chọn một hoặc nhiều file và nhập câu hỏi. Không chọn
   file thì nút Gửi bị khóa. Danh sách chỉ có tài liệu đã xử lý thành công.
5. Câu trả lời có nguồn, đoạn trích và liên kết mở file gốc. Đổi lựa chọn sẽ
   bắt đầu ngữ cảnh mới; các tin nhắn đã hiển thị vẫn được giữ.

Mọi người đã đăng nhập được hỏi và mở các file Completed. Quyền upload vẫn
thuộc System Manager. Category không còn được dùng.

Trên máy khác, cấu hình site/9Router của máy đó rồi chạy `prepare.py` trước
Compose theo phần dưới. Nếu chuyển dữ liệu từ máy cũ, khôi phục cả database
và các file upload public/private của Frappe; bản ghi đường dẫn trong database
không chứa nội dung file. Các KB mới sẽ tự được tạo và xử lý từ những file này.

## First setup on a machine

Configure `llm_api_url`, `llm_api_key`, and `llm_api_model` in the local LMS
`docker/frappe-bench/sites/lms.localhost/site_config.json`, then run from the
repository root:

```powershell
python docker/openkb/prepare.py
cd docker
docker compose up -d --build
docker compose ps openkb frappe
```

From the repository root, run `python docker/openkb/check.py` to check API
authentication, the Workbench, and upstream API routes without LLM calls.

`prepare.py` writes `docker/.env.openkb` and `docker/.env.openkb-frappe`, both
ignored by Git. It reuses the gateway settings and preserves an existing
OpenKB API token. Re-run it after changing the gateway credentials, then
recreate the OpenKB and Frappe containers. Do not copy these files between machines or
commit them.

- Workbench: <http://localhost:7566/>
- API documentation: <http://localhost:7566/docs>
- API prefix: `http://openkb:7566/api/v1` for other Compose services.
- Authentication: `Authorization: Bearer <OPENKB_API_TOKEN>`.

The token is in the local ignored environment file. The gateway API key and
the OpenKB API token have different purposes; the 9Router dashboard password
is not a gateway API key.

## Persistence and model setup

`openkb-data` stores KBs and their source/wiki artifacts. `openkb-config`
stores the OpenKB registry and global configuration. Ordinary Compose
container recreation preserves these named volumes.

New KBs inherit the generated runtime template: Vietnamese output, the
existing LMS model using the `openai/` LiteLLM provider prefix, PDF PageIndex
threshold of 20 pages, and ingest concurrency of 1. Existing KB configuration
is not rewritten when the service restarts.

Upstream `/add` expects a multipart file upload. A Frappe file URL alone is
not its upload payload. `/query` returns an answer and expects a KB name; it
does not provide the LMS document-selection filter by itself.

## RAG Document and chat

1. A System Manager uploads a file in `RAG Document`. The original Frappe
   file URL stays in `upload_tai_lieu`; category is removed from the form.
2. After commit, a long-queue worker reads that saved File and calls OpenKB
   `/init` and multipart `/add`. Status becomes Processing, Completed or Failed.
   Existing documents are automatically queued during the initial migration.
3. Logged-in users select one or more Completed documents in the existing
   chat popup. No selection disables Send and is rejected by the backend.
4. One selected file uses its own KB. A multi-file selection uses a separate
   KB keyed by site, document IDs and content hashes. First use compiles
   exactly those files; later requests reuse that KB. No Qdrant retrieval is
   involved in this chat flow.
5. A background job on the short queue calls `/query`; the widget polls its
   result. The dedicated `frappe-chat-worker` serves this queue while the
   Bench worker ingests large files on the long queue. Ready KBs can be
   queried while another KB compiles. Visible
   history stays when selection changes, but the new context ID excludes all
   previous messages from prompts sent for the new selection.
6. Citations are checked against ingested original source text. The small
   authenticated `/lms/v1/source-pages` read-only extension preserves page
   numbers from long-document source JSON; it does not replace upstream APIs.
   Short documents have excerpts without a page number. Original private
   files are opened through an authenticated LMS endpoint, as all logged-in
   users are allowed to read successfully processed documents.

For Failed documents inspect `Processing error` and OpenKB/9Router logs, then
click **Xử lý lại với OpenKB**. Pending/Processing jobs are recovered on restart
and hourly; failed LLM calls do not trigger unlimited automatic recompilation.
Compilation requires a gateway model supporting tool calls and JSON output.
It may use many LLM calls for large files and new multi-file combinations.

Supported uploads: PDF, TXT, Markdown, HTML, CSV, DOCX, PPTX, XLSX, XLS.
Convert legacy DOC/PPT before uploading. Image-only scans require OCR before
uploading. Cached KB combinations remain in the named volumes; changing or
deleting an LMS document makes its old KB unavailable to the LMS chat, but
does not automatically erase that historical KB from disk.

Routine `docker compose down` preserves the database and OpenKB volumes.
On other machines run `prepare.py` with that machine's own local site/gateway
config before Compose. The first startup updates the schema; later startups
skip migration when the schema fingerprint matches. Existing category
columns/data are retained by Frappe migration but have no role in this UI.

Runtime diagnostics:

```powershell
docker compose logs --tail 80 openkb
docker compose exec frappe tail -n 80 /workspace/frappe-bench/logs/worker.error.log
```
