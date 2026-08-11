import os
import json
import re
import frappe
from frappe import _

# =====================================================================
# 1. HELPER FUNCTIONS
# =====================================================================

def extract_text_from_file(file_url: str) -> str:
    if not file_url:
        return ""
    try:
        file_doc = frappe.get_doc("File", {"file_url": file_url})
        file_path = file_doc.get_full_path()
        if not file_path or not os.path.exists(file_path):
            return ""
        
        ext = os.path.splitext(file_path)[1].lower()
        if ext in [".txt", ".md", ".csv", ".json"]:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        elif ext == ".pdf":
            text = []
            try:
                import pypdf
                reader = pypdf.PdfReader(file_path)
                for page in reader.pages:
                    t = page.extract_text()
                    if t:
                        text.append(t)
            except Exception:
                pass
            return "\n".join(text)
        elif ext in [".docx", ".doc"]:
            text = []
            try:
                import docx
                doc = docx.Document(file_path)
                for para in doc.paragraphs:
                    if para.text:
                        text.append(para.text)
            except Exception:
                pass
            return "\n".join(text)
        else:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
    except Exception as e:
        frappe.logger().error(f"Error extracting text from file {file_url}: {e}")
        return ""

def get_course_content(course_name: str) -> str:
    """Trích xuất toàn bộ tên, mô tả, nội dung các chương và bài học của 1 khóa học"""
    if not course_name:
        return ""
    try:
        course = frappe.get_doc("LMS Course", course_name)
        lines = [
            f"Tên khóa học: {course.title}",
            f"Giới thiệu: {course.short_introduction or ''}",
            f"Mô tả chi tiết: {course.description or ''}"
        ]
        
        chapters = frappe.get_all(
            "Course Chapter",
            filters={"course": course_name},
            fields=["name", "title"],
            order_by="creation asc"
        )
        
        for ch in chapters:
            lines.append(f"\n--- Chương: {ch.title} ---")
            ch_doc = frappe.get_doc("Course Chapter", ch.name)
            if hasattr(ch_doc, "lessons") and ch_doc.lessons:
                for l_row in ch_doc.lessons:
                    l_name = l_row.get("lesson")
                    if l_name and frappe.db.exists("Course Lesson", l_name):
                        l_doc = frappe.get_doc("Course Lesson", l_name)
                        lines.append(f"Bài học: {l_doc.title}")
                        if l_doc.body:
                            lines.append(l_doc.body[:1000]) # Lấy 1000 ký tự đầu bài học
        return "\n".join(lines)
    except Exception as e:
        frappe.logger().error(f"Error getting course content for {course_name}: {e}")
        return ""

@frappe.whitelist()
def get_user_files():
    try:
        user = frappe.session.user
        if user == "Administrator":
            files = frappe.get_all("File", fields=["name", "file_name", "file_url", "creation"], order_by="creation desc", limit=50)
        else:
            files = frappe.get_all(
                "File",
                filters=[["is_private", "=", 0]],
                or_filters=[["owner", "=", user]],
                fields=["name", "file_name", "file_url", "creation"],
                order_by="creation desc",
                limit=50
            )
        return files
    except Exception:
        return []

@frappe.whitelist()
def get_courses_list():
    """API lấy danh sách các khóa học đã được lọc theo User hiện tại"""
    try:
        user = frappe.session.user
        filters = {}
        
        # Nếu không phải Admin, chỉ lấy các khóa học do user này tạo
        if user != "Administrator":
            filters["owner"] = user

        return frappe.get_all(
            "LMS Course",
            filters=filters,
            fields=["name", "title"],
            order_by="creation desc",
            limit=100
        )
    except Exception as e:
        frappe.logger().error(f"Error fetching course list: {str(e)}")
        return []


# =====================================================================
# 2. AI TOOLS DEFINITIONS
# =====================================================================

COURSE_CREATION_TOOL = {
    "type": "function",
    "function": {
        "name": "create_course",
        "description": "Create a fully structured learning course in the LMS system with chapters and lessons.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string", 
                    "description": "A smart, highly accurate, professional, and concise title for the course (max 6-8 words). Extract the core subject. NEVER copy the user's prompt verbatim."
                },
                "short_introduction": {"type": "string", "description": "Brief 1-2 sentence introduction of the course."},
                "description": {"type": "string", "description": "Detailed description of the course."},
                "chapters": {
                    "type": "array",
                    "description": "List of chapters in the course.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "Title of the chapter."},
                            "lessons": {
                                "type": "array",
                                "description": "List of lessons in this chapter.",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "title": {"type": "string", "description": "Title of the lesson."},
                                        "body": {
                                            "type": "string", 
                                            "description": "Markdown content/body of the lesson. CRITICAL: For math formulas, you MUST wrap block equations in $$...$$ and inline equations in $...$. Use valid LaTeX formatting."
                                        }
                                    },
                                    "required": ["title", "body"]
                                }
                            }
                        },
                        "required": ["title", "lessons"]
                    }
                }
            },
            "required": ["title", "short_introduction", "chapters"]
        }
    }
}

QUIZ_CREATION_TOOL = {
    "type": "function",
    "function": {
        "name": "create_quiz",
        "description": "Create a fully structured quiz with questions and options.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string", 
                    "description": "A smart, highly accurate, professional, and concise title for the quiz (max 3-8 words). Extract the core subject. NEVER copy the user's prompt verbatim."
                },
                "passing_percentage": {"type": "number", "description": "Passing percentage (e.g. 50)."},
                "questions": {
                    "type": "array",
                    "description": "List of questions. CRITICAL QUANTITY RULE: If the user asks for N questions (e.g., '5 câu'), you MUST generate EXACTLY N objects in this array.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "question": {"type": "string", "description": "Question text." },
                            "marks": {"type": "integer", "description": "Marks/points for this question. Default is 1."},
                            "type": {
                                "type": "string", 
                                "description": "Type of question. MUST be exactly one of: 'Choices', 'User Input', 'Open Ended'."
                            },
                            "options": {
                                "type": "array",
                                "description": "List of options. MUST contain at least 2 items for 'Choices' questions, and AT LEAST ONE option MUST have is_correct = 1.",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "option": {"type": "string"},
                                        "is_correct": {"type": "integer", "description": "1 if correct, 0 if wrong."},
                                        "explanation": {"type": "string", "description": "Explanation for this option (optional)"}
                                    },
                                    "required": ["option", "is_correct"]
                                }
                            }
                        },
                        "required": ["question", "options", "type"]
                    }
                }
            },
            "required": ["title", "questions"]
        }
    }
}

ASSIGNMENT_CREATION_TOOL = {
    "type": "function",
    "function": {
        "name": "create_assignment",
        "description": "Create one or multiple assignments with description, questions, and submission types.",
        "parameters": {
            "type": "object",
            "properties": {
                "assignments": {
                    "type": "array",
                    "description": "List of assignments to create. CRITICAL: If the user asks for N assignments, you MUST generate exactly N objects in this array.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string", 
                                "description": "Short title."
                            },
                            "submission_type": {
                                "type": "string", 
                                "description": "Type of submission required. MUST be exactly one of: 'Văn bản', 'Tài liệu', 'PDF', 'Hình ảnh', 'URL'. AI should determine this based on the context of the question."
                            },
                            "question": {
                                "type": "string", 
                                "description": "Detailed assignment prompt in markdown. CRITICAL: You MUST ALWAYS start this markdown with a Level 1 Heading (e.g., '# Bài tập về Vòng lặp For') on the very first line."
                            }
                        },
                        "required": ["title", "submission_type", "question"]
                    }
                }
            },
            "required": ["assignments"]
        }
    }
}


# =====================================================================
# 3. EXECUTION FUNCTIONS
# =====================================================================

def execute_create_course(arguments: dict) -> dict:
    try:
        title = arguments.get("title")
        short_introduction = arguments.get("short_introduction", "")
        description = arguments.get("description", "")
        chapters_data = arguments.get("chapters", [])

        if not title or title.strip() == "":
            title = "Khóa học AI tạo tự động"

        current_user = frappe.session.user if frappe.session.user and frappe.session.user != "Guest" else "Administrator"

        built_chapters = []

        # 1. Tạo Course trước để lấy ID
        course_data = {
            "doctype": "LMS Course",
            "title": title,
            "published": 0,
            "status": "Approved",
            "short_introduction": short_introduction,
            "description": description or short_introduction or title,
            "instructors": [{"instructor": current_user}]
        }
        
        course_doc = frappe.get_doc(course_data)
        course_doc.insert(ignore_permissions=True)
        course_name = course_doc.name

        # 2. Tạo Chapter và Lessons có gắn đầy đủ liên kết chapter và course
        for c_idx, ch_data in enumerate(chapters_data, start=1):
            ch_title = ch_data.get("title", f"Chapter {c_idx}")
            
            chapter_doc = frappe.get_doc({
                "doctype": "Course Chapter",
                "course": course_name,
                "title": ch_title
            })
            chapter_doc.insert(ignore_permissions=True)
            chapter_name = chapter_doc.name

            lessons_data = ch_data.get("lessons", [])
            lesson_references = []
            
            for l_idx, ls_data in enumerate(lessons_data, start=1):
                ls_title = ls_data.get("title", f"Lesson {l_idx}")
                ls_body = ls_data.get("body", "")

                lesson_doc = frappe.get_doc({
                    "doctype": "Course Lesson",
                    "chapter": chapter_name,
                    "title": ls_title,
                    "body": ls_body
                })
                lesson_doc.insert(ignore_permissions=True)
                lesson_references.append({"lesson": lesson_doc.name})

            if lesson_references:
                for l_ref in lesson_references:
                    chapter_doc.append("lessons", l_ref)
                chapter_doc.save(ignore_permissions=True)

            built_chapters.append({"chapter": chapter_name})

        # 3. Gắn danh sách Chapter vào Course
        if built_chapters:
            course_doc.reload() # <--- QUAN TRỌNG: Làm mới object để tránh lỗi Timestamp Mismatch
            for c_ref in built_chapters:
                course_doc.append("chapters", c_ref)
            course_doc.save(ignore_permissions=True)

        frappe.db.commit()
        return {
            "success": True,
            "course_name": course_name,
            "title": title,
            "route": f"courses/{course_name}",
            "message": f"Course '{title}' successfully created with {len(built_chapters)} chapters!"
        }
    except Exception as e:
        frappe.db.rollback()
        frappe.logger().error(f"Error executing create_course: {str(e)}")
        return {"success": False, "error": str(e)}
def _apply_question_options(question_data: dict, formatted_options: list, q_type: str):
    """
    Map mảng options sang schema phẳng của LMS Question.
    - Choices: option_1 -> option_10, is_correct_1 -> is_correct_10
    - User Input: possibility_1 -> possibility_10
    - Open Ended: Bỏ qua
    """
    if q_type == "Choices":
        for i in range(1, 11):
            if i <= len(formatted_options):
                opt = formatted_options[i-1]
                question_data[f"option_{i}"] = str(opt.get("option", "")).strip()
                question_data[f"is_correct_{i}"] = opt.get("is_correct", 0)
                question_data[f"explanation_{i}"] = str(opt.get("explanation", "")).strip()
            else:
                question_data[f"option_{i}"] = None
                question_data[f"is_correct_{i}"] = 0
                question_data[f"explanation_{i}"] = None
                
    elif q_type == "User Input":
        for i in range(1, 11):
            if i <= len(formatted_options):
                opt = formatted_options[i-1]
                question_data[f"possibility_{i}"] = str(opt.get("option", "")).strip()
            else:
                question_data[f"possibility_{i}"] = None

def execute_create_quiz(arguments: dict, course_name: str = None) -> dict:
    try:
        parent_title = (
            arguments.get("title") if isinstance(arguments, dict) else None
        )

        # Giải (Unwrap) nếu AI bọc dữ liệu trong 'quiz' hoặc 'data'
        if isinstance(arguments, dict):
            if "quiz" in arguments and isinstance(arguments["quiz"], dict):
                arguments = arguments["quiz"]
            elif "data" in arguments and isinstance(arguments["data"], dict):
                arguments = arguments["data"]

        # 2. Lấy title từ dict đã unwrap, nếu không có thì khôi phục từ parent_title
        title = arguments.get("title") or parent_title or "Bài kiểm tra kiến thức"
        title = str(title).strip()

        passing_percentage = arguments.get("passing_percentage", 50)
        questions_data = arguments.get("questions", [])

        if not questions_data or not isinstance(questions_data, list):
            return {
                "success": False,
                "error": "AI không tạo được danh sách câu hỏi hợp lệ.",
            }

        # 3. Tạo Quiz Document cha với title chuẩn
        quiz_doc = frappe.get_doc({
            "doctype": "LMS Quiz",
            "title": title,
            "passing_percentage": passing_percentage,
            "course": course_name or None,
        })
        quiz_doc.insert(ignore_permissions=True)

        for idx, q_data in enumerate(questions_data, start=1):
            q_text = q_data.get("question") or f"Câu hỏi {idx}"
            raw_type = str(q_data.get("type") or "Choices").strip().lower()

            # Standardize kiểu câu hỏi
            if any(k in raw_type for k in ["choice", "single", "multiple", "mcq", "select", "trắc nghiệm"]):
                q_type = "Choices"
            elif any(k in raw_type for k in ["input", "fill", "blank", "điền"]):
                q_type = "User Input"
            elif any(k in raw_type for k in ["open", "essay", "tự luận"]):
                q_type = "Open Ended"
            else:
                q_type = "Choices"
            
            is_choice_type = (q_type == "Choices")

            # Trích xuất options raw
            options_input = (
                q_data.get("options") or 
                q_data.get("choices") or 
                q_data.get("answers") or 
                []
            )

            # Phân tích cú pháp nếu options_input là chuỗi JSON
            if isinstance(options_input, str):
                try:
                    parsed = json.loads(options_input)
                    options_input = parsed if isinstance(parsed, (list, dict)) else [options_input]
                except Exception:
                    options_input = [o.strip() for o in re.split(r'[\n,;]+', options_input) if o.strip()]

            formatted_options = []

            if isinstance(options_input, dict):
                for k, v in options_input.items():
                    opt_text = str(v).strip()
                    if opt_text:
                        is_corr = 1 if str(k).lower() in ["correct", "right", "1", "true", "đúng"] else 0
                        formatted_options.append({"option": opt_text, "is_correct": is_corr, "explanation": ""})
            elif isinstance(options_input, list):
                for opt in options_input:
                    if isinstance(opt, dict):
                        opt_text = str(opt.get("option") or opt.get("text") or opt.get("value") or opt.get("answer") or "").strip()
                        if opt_text:
                            is_correct_val = opt.get("is_correct") or opt.get("correct") or opt.get("isCorrect") or 0
                            is_correct = 1 if str(is_correct_val).lower() in ["1", "true", "yes", "đúng"] else 0
                            formatted_options.append({
                                "option": opt_text,
                                "is_correct": is_correct,
                                "explanation": str(opt.get("explanation") or "").strip()
                            })
                    elif isinstance(opt, str) and opt.strip():
                        formatted_options.append({"option": opt.strip(), "is_correct": 0, "explanation": ""})

            # Lọc bỏ tuỳ chọn rỗng
            formatted_options = [opt for opt in formatted_options if str(opt.get("option", "")).strip()]

            # Áp dụng logic chốt chặn tuỳ theo loại câu hỏi
            if is_choice_type:
                # Phải có >= 2 options và có 1 đáp án đúng
                if len(formatted_options) == 0:
                    formatted_options = [
                        {"option": "Lựa chọn A", "is_correct": 1, "explanation": ""},
                        {"option": "Lựa chọn B", "is_correct": 0, "explanation": ""}
                    ]
                elif len(formatted_options) == 1:
                    formatted_options.append({"option": "Lựa chọn B", "is_correct": 0, "explanation": ""})
                
                if not any(opt.get("is_correct") == 1 for opt in formatted_options):
                    formatted_options[0]["is_correct"] = 1
                    
            elif q_type == "User Input":
                # Cần ít nhất 1 possibility
                if len(formatted_options) == 0:
                    formatted_options = [{"option": "Đáp án tham khảo"}]
            else:
                formatted_options = [] # Tự luận không cần mảng options

            # 2. Khởi tạo LMS Question với Schema phẳng
            question_data = {
                "doctype": "LMS Question",
                "question": q_text,
                "type": q_type
            }

            # Map danh sách `formatted_options` vào `option_1`, `option_2`... hoặc `possibility_1`...
            _apply_question_options(question_data, formatted_options, q_type)

            question_doc = frappe.get_doc(question_data)
            question_doc.insert(ignore_permissions=True)

            # 3. Gắn vào Quiz và map 'marks' vào child table `LMS Quiz Question`
            marks_val = q_data.get("marks", 1)
            try:
                marks_val = float(marks_val)
            except ValueError:
                marks_val = 1.0

            quiz_doc.append("questions", {
                "question": question_doc.name,
                "marks": marks_val
            })

        quiz_doc.save(ignore_permissions=True)
        frappe.db.commit()

        return {
            "success": True,
            "quiz_name": quiz_doc.name,
            "title": title,
            "route": f"quizzes/{quiz_doc.name}",
            "message": f"Quiz '{title}' successfully created!"
        }
    except Exception as e:
        frappe.db.rollback()
        frappe.logger().error(f"Error executing create_quiz: {str(e)}")
        return {"success": False, "error": str(e)}

def execute_create_assignment(arguments: dict, course_name: str = None) -> dict:
    try:
        # Giải bọc mảng assignments từ AI
        if "assignments" in arguments and isinstance(arguments["assignments"], list):
            assignments_data = arguments["assignments"]
        elif "data" in arguments and isinstance(arguments["data"], list):
            assignments_data = arguments["data"]
        elif isinstance(arguments, list):
            assignments_data = arguments
        else:
            # Fallback nếu AI lỡ trả về 1 object đơn lẻ
            assignments_data = [arguments]

        if not assignments_data:
            return {"success": False, "error": "AI không tạo được danh sách bài tập hợp lệ."}

        created_names = []
        created_titles = []
        
        from frappe.utils import markdown

        # Vòng lặp tạo N bài tập
        for asg in assignments_data:
            raw_question = asg.get("question", "")
            
            # 1. TRÍCH XUẤT HEADING ĐẦU TIÊN (H1 -> H6) ĐỂ LÀM TITLE
            extracted_title = ""
            if raw_question:
                match = re.search(r'^(#{1,6})\s+(.+)$', raw_question, re.MULTILINE)
                if match:
                    extracted_title = match.group(2).strip()
                    # Cắt dòng heading ra khỏi body
                    raw_question = raw_question.replace(match.group(0), "", 1).strip()
            
            # 2. XỬ LÝ TIÊU ĐỀ
            raw_title = extracted_title or asg.get("title")
            title = str(raw_title).strip() if raw_title else "AI Generated Assignment"
            
            # 3. XỬ LÝ SUBMISSION TYPE (Ánh xạ chính xác các tùy chọn hệ thống cho phép)
            raw_type = str(asg.get("submission_type") or asg.get("type") or "Text").strip().lower()
            
            if any(k.lower() in raw_type for k in ["pdf"]):
                asg_type = "PDF"
            elif any(k.lower() in raw_type for k in ["image", "hình", "ảnh", "picture", "photo"]):
                asg_type = "Image"
            elif any(k.lower() in raw_type for k in ["upload", "file", "tệp", "document", "tài liệu"]):
                asg_type = "Document"
            elif any(k.lower() in raw_type for k in ["url", "link", "đường dẫn"]):
                asg_type = "URL"
            else:
                asg_type = "Text" # Mặc định nếu AI trả về Text hoặc không rõ ràng
            
            # 4. CHUYỂN MARKDOWN THÀNH HTML
            question_html = markdown(raw_question) if raw_question else ""
            
            # 5. INSERT VÀO DB
            asg_doc = frappe.get_doc({
                "doctype": "LMS Assignment",
                "title": title,
                "type": asg_type,
                "question": question_html,
                "course": course_name or None
            })

            asg_doc.insert(ignore_permissions=True)
            
            created_names.append(asg_doc.name)
            created_titles.append(title)
            
        frappe.db.commit()
        
        return {
            "success": True,
            "count": len(created_names),
            "assignment_names": created_names,
            "titles": created_titles,
            "route": f"assignments/{created_names[0]}" if created_names else "",
            "message": f"Successfully created {len(created_names)} assignments!"
        }
    except Exception as e:
        frappe.db.rollback()
        frappe.logger().error(f"Error executing create_assignment: {str(e)}")
        return {"success": False, "error": str(e)}


# =====================================================================
# 4. AI API ENDPOINTS
# =====================================================================

def _prepare_llm_context(file_urls: str = None, course_name: str = None) -> str:
    doc_content = ""
    
    # Nạp nội dung Khóa học nếu chọn
    if course_name:
        course_text = get_course_content(course_name)
        if course_text:
            doc_content += f"\n--- [Nội dung Khóa học tham chiếu: {course_name}] ---\n{course_text}\n"

    # Nạp nội dung các File tài liệu
    urls = []
    if file_urls:
        try:
            urls = json.loads(file_urls)
            if not isinstance(urls, list):
                urls = [urls]
        except Exception:
            urls = [file_urls]

    for url in urls:
        text = extract_text_from_file(url)
        if text:
            doc_content += f"\n--- [Tài liệu: {url.split('/')[-1]}] ---\n{text}\n"

    if len(doc_content) > 250000: 
        doc_content = doc_content[:250000] + "\n\n...[Nội dung đã được cắt bớt do quá dài]"
        
    return doc_content

def _extract_fallback_json(content: str) -> dict:
    match = re.search(r'```(?:json)?(.*?)```', content, re.DOTALL)
    if match:
        json_str = match.group(1).strip()
    else:
        start = content.find('{')
        end = content.rfind('}') + 1
        json_str = content[start:end] if start != -1 else ""
    if json_str:
        try:
            return json.loads(json_str)
        except Exception:
            return None
    return None

@frappe.whitelist()
def ai_chat_generate_course(prompt: str, file_urls: str = None, message_history: str = None):
    try:
        if isinstance(message_history, str):
            message_history = json.loads(message_history)
    except Exception:
        message_history = []

    doc_content = _prepare_llm_context(file_urls=file_urls)
    llm_api_url = frappe.conf.get("llm_api_url")
    llm_api_key = frappe.conf.get("llm_api_key")
    llm_api_model = frappe.conf.get("llm_api_model")
    llm_api_temperature = frappe.conf.get("llm_api_temperature") or 0.2
    llm_api_topp = frappe.conf.get("llm_api_mollm_api_toppdel") or 0.2

    system_prompt = (
        "You are an expert AI instructional designer for an LMS system. "
        "CRITICAL RULES FOR TITLE: "
        "1. You MUST generate a professional, concise course title (maximum 3-8 words) in the 'title' field based on the core subject. "
        "2. NEVER use conversational words like 'Hãy tạo', 'Làm cho tôi', or copy the raw prompt. "
        "3. You MUST call the `create_course` tool function."
    )

    messages = [{"role": "system", "content": system_prompt}]
    if doc_content:
        messages.append({"role": "user", "content": f"[Reference Document Content]:\n{doc_content}\n\nUse the documents above to generate the course content."})
    if message_history:
        messages.extend([msg for msg in message_history if isinstance(msg, dict) and "role" in msg and "content" in msg])
    messages.append({"role": "user", "content": prompt})

    try:
        import openai
        client = openai.OpenAI(base_url=llm_api_url, api_key=llm_api_key)

        response = client.chat.completions.create(
            model=llm_api_model,
            messages=messages,
            tools=[COURSE_CREATION_TOOL],
            tool_choice="auto",
            temperature=llm_api_temperature,        
            top_p=llm_api_topp
        )
        response_message = response.choices[0].message
        args = None
        
        if response_message.tool_calls:
            args = json.loads(response_message.tool_calls[0].function.arguments)
        elif response_message.content:
            args = _extract_fallback_json(response_message.content)

        if args and isinstance(args, dict):
            if "course" in args and "chapters" not in args:
                args = args["course"]

            if not args.get("title") or len(args.get("title", "")) > 60:
                clean_prompt = prompt[:30].strip().capitalize()
                args["title"] = f"Khóa học: {clean_prompt}..." if len(prompt) > 30 else f"Khóa học: {clean_prompt}"

            result = execute_create_course(args)
            if result.get("success"):
                course_title = result.get('title') or args.get('title')
                return {"status": "success", "tool_result": result, "reply": f"Khóa học **{course_title}** đã được khởi tạo thành công!"}
            else:
                return {"status": "error", "reply": f"Lỗi lưu dữ liệu: {result.get('error')}"}

        return {"status": "message", "reply": response_message.content or "Tôi không thể tạo khóa học, vui lòng cung cấp thêm thông tin."}
    except Exception as e:
        frappe.logger().error(f"AI Course Gen Error: {str(e)}")
        return {"status": "error", "reply": f"Lỗi hệ thống: {str(e)}"}


@frappe.whitelist()
def ai_chat_generate_quiz(prompt: str, file_urls: str = None, course_name: str = None, message_history: str = None):
    try:
        if isinstance(message_history, str):
            message_history = json.loads(message_history)
    except Exception:
        message_history = []

    doc_content = _prepare_llm_context(file_urls=file_urls, course_name=course_name)
    llm_api_url = frappe.conf.get("llm_api_url")
    llm_api_key = frappe.conf.get("llm_api_key")
    llm_api_model = frappe.conf.get("llm_api_model")
    llm_api_temperature = frappe.conf.get("llm_api_temperature") or 0.2
    llm_api_topp = frappe.conf.get("llm_api_mollm_api_toppdel") or 0.2
    
    # ĐÃ THÊM RULE SỐ 3 ĐỂ ÉP AI PHẢI CÓ ĐÁP ÁN ĐÚNG
    system_prompt = (
        "You are an expert AI quiz generator for Frappe Learning (LMS). "
        "CRITICAL RULES: "
        "1. If the user requests a specific number of questions (e.g., '5 câu'), you MUST generate exactly that number of items in the 'questions' array. "
        "2. TITLE RULE: The 'title' MUST be a smart, concise topic name (max 4-8 words) extracted from the subject. NEVER copy the user's prompt or include instructional words like 'Tạo', 'Hãy', 'Làm cho tôi'. "
        "3. OPTIONS RULE: For 'Choices' type questions, you MUST generate at least 2 options, and AT LEAST ONE option MUST have 'is_correct' set to 1. "
        "4. MATH RULE: For ANY math formulas, you MUST wrap block equations in $$...$$ and inline equations in $...$. Use valid LaTeX." # <--- THÊM DÒNG NÀY
        "5. You MUST use the `create_quiz` tool function."
    )

    messages = [{"role": "system", "content": system_prompt}]
    if doc_content:
        messages.append({"role": "user", "content": f"[Context Content]:\n{doc_content}"})
    if message_history:
        messages.extend([msg for msg in message_history if isinstance(msg, dict) and "role" in msg and "content" in msg])
    messages.append({"role": "user", "content": prompt})

    try:
        import openai
        client = openai.OpenAI(base_url=llm_api_url, api_key=llm_api_key)
        
        response = client.chat.completions.create(
            model=llm_api_model,
            messages=messages,
            tools=[QUIZ_CREATION_TOOL],
            tool_choice="auto",
            temperature=llm_api_temperature,        
            top_p=llm_api_topp
        )
        response_message = response.choices[0].message
        args = None

        if response_message.tool_calls:
            args = json.loads(response_message.tool_calls[0].function.arguments)
        elif response_message.content:
            args = _extract_fallback_json(response_message.content)

        if args and isinstance(args, dict):
            # 1. Bắt lấy title của AI trước khi gỡ bọc (đề phòng AI để title ở ngoài root)
            raw_ai_title = args.get("title")
            
            # 2. Gỡ bọc an toàn (Unwrap)
            if "quiz" in args and isinstance(args["quiz"], dict):
                args = args["quiz"]
            elif "data" in args and isinstance(args["data"], dict):
                args = args["data"]
                
            # Phục hồi title nếu bên trong không có mà bên ngoài lại có
            if not args.get("title") and raw_ai_title:
                args["title"] = raw_ai_title

            if "questions" in args:
                # 3. Lấy title và xử lý cẩn thận kiểu dữ liệu (tránh rủi ro AI trả về null)
                title_val = args.get("title")
                title_val = str(title_val).strip() if title_val else ""

                args["title"] = title_val # Nhận chính xác tên do AI tạo ra

                # 5. Thực thi tạo Quiz
                result = execute_create_quiz(args, course_name=course_name)
                if result.get("success"):
                    quiz_title = result.get('title') or args.get('title')
                    return {"status": "success", "tool_result": result, "reply": f"Bài trắc nghiệm **{quiz_title}** đã được tạo thành công!"}
                else:
                    return {"status": "error", "reply": f"Lỗi lưu dữ liệu: {result.get('error')}"}

        return {"status": "message", "reply": response_message.content or "Đã xử lý."}

    except Exception as e:
        frappe.logger().error(f"AI Quiz Gen Error: {e}")
        return {"status": "error", "reply": f"Lỗi hệ thống: {str(e)}"}

@frappe.whitelist()
def ai_chat_generate_assignment(prompt: str, file_urls: str = None, course_name: str = None, message_history: str = None):
    try:
        if isinstance(message_history, str):
            message_history = json.loads(message_history)
    except Exception:
        message_history = []
        
    doc_content = _prepare_llm_context(file_urls=file_urls, course_name=course_name)
    llm_api_url = frappe.conf.get("llm_api_url")
    llm_api_key = frappe.conf.get("llm_api_key")
    llm_api_model = frappe.conf.get("llm_api_model")
    llm_api_temperature = frappe.conf.get("llm_api_temperature") or 0.2
    llm_api_topp = frappe.conf.get("llm_api_mollm_api_toppdel") or 0.2

    # Cập nhật System Prompt: Ép AI trả về Array và tuân thủ định dạng Submission Type
    system_prompt = (
        "You are an expert AI assignment creator for Frappe Learning (LMS). "
        "CRITICAL RULES: "
        "1. QUANTITY RULE: If requested for multiple exercises, you MUST generate exactly that number in the 'assignments' array. "
        "2. HEADING RULE: The 'question' markdown MUST ALWAYS start with a Level 1 Heading (e.g. '# Bài tập Lập trình Python') on the very first line. This will be used as the title. "
        "3. SUBMISSION TYPE RULE: You must accurately define 'submission_type' (Must be one of: Text, Image, URL, PDF, Document) based on the requirement. "
        "4. MATH RULE: For ANY math formulas, you MUST wrap block equations in $$...$$ and inline equations in $...$. Use valid LaTeX." # <--- THÊM DÒNG NÀY
        "5. You MUST use the `create_assignment` tool function."
    )

    messages = [{"role": "system", "content": system_prompt}]
    if doc_content:
        messages.append({"role": "user", "content": f"[Context Content]:\n{doc_content}"})
    if message_history:
        messages.extend([msg for msg in message_history if isinstance(msg, dict) and "role" in msg and "content" in msg])
    messages.append({"role": "user", "content": prompt})

    try:
        import openai
        client = openai.OpenAI(base_url=llm_api_url, api_key=llm_api_key)
        
        response = client.chat.completions.create(
            model=llm_api_model,
            messages=messages,
            tools=[ASSIGNMENT_CREATION_TOOL],
            tool_choice="auto",
            temperature=llm_api_temperature,        
            top_p=llm_api_topp
        )
        response_message = response.choices[0].message
        args = None

        if response_message.tool_calls:
            args = json.loads(response_message.tool_calls[0].function.arguments)
        elif response_message.content:
            args = _extract_fallback_json(response_message.content)

        if args and isinstance(args, dict):
            # Hàm execute_create_assignment (ở bước 2) đã được nâng cấp để tự động xử lý mảng 'assignments'
            # Nên ở đây chúng ta chỉ việc truyền trực tiếp args vào
            result = execute_create_assignment(args, course_name=course_name)
            
            if result.get("success"):
                count = result.get("count", 1)
                titles = result.get("titles", [])
                
                # Logic hiển thị câu thông báo (Reply) thông minh dựa trên số lượng
                if count > 1:
                    titles_str = "\n".join([f"- **{t}**" for t in titles])
                    reply_msg = f"Đã tạo thành công {count} bài tập:\n{titles_str}"
                else:
                    asg_title = titles[0] if titles else "Bài tập"
                    reply_msg = f"Bài tập **{asg_title}** đã được tạo thành công!"
                    
                return {"status": "success", "tool_result": result, "reply": reply_msg}
            else:
                return {"status": "error", "reply": f"Lỗi lưu dữ liệu: {result.get('error')}"}

        return {"status": "message", "reply": response_message.content or "Đã xử lý."}

    except Exception as e:
        frappe.logger().error(f"AI Assignment Gen Error: {e}")
        return {"status": "error", "reply": f"Lỗi hệ thống: {str(e)}"}