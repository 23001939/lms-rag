// ==========================================
// KHÓA BẢO VỆ 1: CHỐNG CHẠY TRONG IFRAME
// ==========================================
if (window.self !== window.top) {
    console.log("🚫 LMS AI Chat: Đang ở trong iframe bài giảng, bỏ qua để tránh nhân đôi.");
} 
// ==========================================
// KHÓA BẢO VỆ 2: CHỐNG CHẠY 2 LẦN TRONG MAIN WINDOW
// ==========================================
else if (!window.LMS_CHAT_INITIALIZED) {
    window.LMS_CHAT_INITIALIZED = true;
    console.log("🚀 LMS AI Chat Script đang chạy (Đã bật Auto-Close & Bắt buộc mặc định Chat tự do)...");

    function injectLMSChat() {
        // ==========================================
        // 1. KIỂM TRA ĐĂNG NHẬP BẰNG COOKIE
        // ==========================================
        let userId = 'Guest';
        const match = document.cookie.match(new RegExp('(^| )user_id=([^;]+)'));
        if (match) { 
            userId = decodeURIComponent(match[2]); 
        }
        
        if (!userId || userId === 'Guest') return;
        if (window.location.pathname.includes('/login')) return;

        // ==========================================
        // 2. KIỂM TRA VÀ "XÍ CHỖ" NGAY LẬP TỨC TRÊN DOM
        // ==========================================
        if (document.getElementById('lms-chat-container')) {
            return; 
        }

        const chatContainer = document.createElement('div');
        chatContainer.id = 'lms-chat-container';
        document.body.appendChild(chatContainer);

        // ==========================================
        // 3. NHÚNG CSS VÀ THƯ VIỆN
        // ==========================================
        if (!document.getElementById('lms-chat-styles')) {
            const style = document.createElement('style');
            style.id = 'lms-chat-styles';
            style.innerHTML = `
                /* NÚT CHAT NỔI */
                #lms-chat-btn { position: fixed !important; bottom: 30px !important; right: 30px !important; height: 55px !important; padding: 0 20px !important; background: linear-gradient(135deg, #2563eb, #1d4ed8) !important; color: white !important; border-radius: 30px !important; display: flex !important; align-items: center !important; justify-content: center !important; gap: 10px !important; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important; font-size: 16px !important; font-weight: 600 !important; cursor: pointer !important; box-shadow: 0 4px 15px rgba(37, 99, 235, 0.4) !important; z-index: 2147483647 !important; transition: all 0.3s ease !important; }
                #lms-chat-btn i { font-size: 20px !important; }
                #lms-chat-btn:hover { transform: translateY(-3px) !important; box-shadow: 0 6px 20px rgba(37, 99, 235, 0.6) !important; }
                
                /* CỬA SỔ CHAT */
                #lms-chat-window { position: fixed !important; bottom: 100px !important; right: 30px !important; width: 380px !important; height: 580px !important; min-width: 300px !important; min-height: 400px !important; max-width: 90vw !important; max-height: 90vh !important; background: #ffffff !important; border-radius: 16px !important; box-shadow: 0 10px 30px rgba(0,0,0,0.15) !important; display: none; flex-direction: column !important; z-index: 2147483647 !important; border: 1px solid #e2e8f0 !important; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important; overflow: hidden !important; }
                
                /* ĐIỂM KÉO RESIZE GÓC TRÊN-TRÁI */
                .resize-handle { position: absolute; top: 0; left: 0; width: 25px; height: 25px; cursor: nwse-resize; z-index: 100; background: transparent; }
                
                .chat-header { background: linear-gradient(135deg, #2563eb, #1d4ed8) !important; color: white !important; padding: 15px 20px !important; display: flex !important; justify-content: space-between !important; align-items: center !important; }
                .chat-header-info { display: flex; flex-direction: column; }
                .chat-header-info h3 { font-size: 16px !important; font-weight: 600 !important; margin: 0 !important; color: white !important;}
                .chat-header-info p { font-size: 12px !important; opacity: 0.9 !important; margin: 0 !important; margin-top: 2px !important; }
                .close-btn { cursor: pointer !important; font-size: 18px !important; transition: opacity 0.2s; }
                .close-btn:hover { opacity: 0.7; }
                
                /* GIAO DIỆN CHỌN CHỦ ĐỀ */
                .category-toggle-btn { padding: 12px 15px !important; background: #f8fafc !important; border-bottom: 1px solid #e2e8f0 !important; display: flex !important; justify-content: space-between !important; align-items: center !important; cursor: pointer !important; font-size: 13px !important; font-weight: 600 !important; color: #334155 !important; transition: background 0.2s; overflow: hidden; }
                .category-toggle-btn:hover { background: #f1f5f9 !important; }
                .category-toggle-btn i { color: #64748b !important; flex-shrink: 0; }
                .chat-category-content { display: none !important; padding: 10px 15px !important; background: #ffffff !important; border-bottom: 1px solid #e2e8f0 !important; max-height: 140px !important; overflow-y: auto !important; box-shadow: inset 0 -5px 10px -10px rgba(0,0,0,0.1); }
                .chat-category-content.show { display: flex !important; }
                .category-list { flex-direction: column !important; gap: 8px !important; }
                .category-item { display: flex !important; align-items: center !important; gap: 8px !important; font-size: 13px !important; color: #334155 !important; cursor: pointer !important; padding: 2px 0; }
                .category-item input { cursor: pointer !important; width: 16px; height: 16px; accent-color: #2563eb !important; margin: 0;}
                
                /* VÙNG TIN NHẮN */
                .chat-messages { flex: 1 !important; padding: 15px !important; overflow-y: auto !important; background: #f8fafc !important; display: flex !important; flex-direction: column !important; gap: 12px !important; scroll-behavior: smooth; }
                .msg { max-width: 82% !important; padding: 12px 16px !important; border-radius: 16px !important; font-size: 14px !important; line-height: 1.5 !important; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
                .msg-bot { background: white !important; color: #1e293b !important; align-self: flex-start !important; border: 1px solid #e2e8f0 !important; border-bottom-left-radius: 4px !important; }
                .msg-user { background: #2563eb !important; color: white !important; align-self: flex-end !important; border-bottom-right-radius: 4px !important; }
                
                /* CSS MARKDOWN */
                .msg-content { word-wrap: break-word; overflow-wrap: break-word; width: 100%; }
                .msg-content p { margin: 0 0 10px 0; }
                .msg-content p:last-child { margin: 0; }
                .msg-content ul, .msg-content ol { padding-left: 20px !important; margin: 8px 0 !important; }
                .msg-content li { margin-bottom: 6px !important; line-height: 1.5; }
                .msg-content code { background-color: #e2e8f0 !important; color: #e11d48 !important; padding: 2px 6px !important; border-radius: 4px !important; font-family: 'Courier New', Courier, monospace !important; font-size: 13px !important; word-break: break-word; }
                .msg-content pre { background-color: #1e293b !important; color: #f8fafc !important; padding: 12px !important; border-radius: 8px !important; overflow-x: auto !important; margin: 10px 0 !important; font-family: 'Courier New', Courier, monospace !important; font-size: 13px !important; }
                .msg-content pre code { background-color: transparent !important; color: inherit !important; padding: 0 !important; font-size: inherit !important; }
                .msg-content table { border-collapse: collapse; width: 100%; margin: 10px 0; }
                .msg-content th, .msg-content td { border: 1px solid #cbd5e1; padding: 8px; text-align: left; }
                
                /* SCROLLBAR */
                .chat-messages::-webkit-scrollbar, .chat-category-content::-webkit-scrollbar { width: 6px; }
                .chat-messages::-webkit-scrollbar-track, .chat-category-content::-webkit-scrollbar-track { background: transparent; }
                .chat-messages::-webkit-scrollbar-thumb, .chat-category-content::-webkit-scrollbar-thumb { background-color: #cbd5e1; border-radius: 10px; }
                
                /* THANH CÔNG CỤ TẠO NHANH (AI ACTIONS) */
                                .chat-quick-actions { padding: 8px 12px !important; background: #f8fafc !important; border-top: 1px solid #e2e8f0 !important; display: flex !important; gap: 6px !important; overflow-x: auto !important; white-space: nowrap !important; }
                                .quick-action-btn { background: #eff6ff !important; color: #2563eb !important; border: 1px solid #dbeafe !important; padding: 4px 10px !important; border-radius: 12px !important; font-size: 12px !important; font-weight: 500 !important; cursor: pointer !important; display: inline-flex !important; align-items: center !important; gap: 4px !important; transition: all 0.2s; flex-shrink: 0; }
                                .quick-action-btn:hover { background: #2563eb !important; color: white !important; border-color: #2563eb !important; }
                                .quick-action-btn i { font-size: 11px !important; }

                                /* KHU VỰC NHẬP TEXT */
                                .chat-input-area { padding: 12px 15px !important; background: white !important; border-top: 1px solid #e2e8f0 !important; display: flex !important; gap: 10px !important; align-items: center; }
                .chat-input-area input { flex: 1 !important; padding: 12px 16px !important; border: 1px solid #cbd5e1 !important; border-radius: 24px !important; outline: none !important; color: #0f172a !important; font-size: 14px; transition: border-color 0.2s; background: #f8fafc; }
                .chat-input-area input:focus { border-color: #2563eb !important; background: white; }
                .chat-input-area button { background: #2563eb !important; color: white !important; border: none !important; border-radius: 50% !important; width: 42px !important; height: 42px !important; cursor: pointer !important; display: flex !important; align-items: center !important; justify-content: center !important; transition: background 0.2s, transform 0.2s; }
                .chat-input-area button:hover { background: #1d4ed8 !important; transform: scale(1.05); }
                .typing { display: none; margin-left: 15px !important; color: #64748b !important; font-size: 12px !important; font-style: italic !important; margin-bottom: 10px !important; }
            `;
            document.head.appendChild(style);
        }

        if (!document.querySelector('link[href*="font-awesome"]')) {
            const faLink = document.createElement('link');
            faLink.rel = 'stylesheet';
            faLink.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css';
            document.head.appendChild(faLink);
        }

        if (!document.querySelector('script[src*="marked.min.js"]')) {
            const markedScript = document.createElement('script');
            markedScript.src = 'https://cdn.jsdelivr.net/npm/marked/marked.min.js';
            document.head.appendChild(markedScript);
        }

        // ==========================================
        // 4. RÓT HTML VÀO CONTAINER ĐÃ TẠO
        // ==========================================
        chatContainer.innerHTML = `
            <div id="lms-chat-btn" onclick="toggleChat()">
                <i class="fa-solid fa-robot"></i>
                <span>Chat AI</span>
            </div>
            <div id="lms-chat-window">
                <div class="resize-handle" id="resize-handle" title="Kéo để thay đổi kích thước"></div>
                <div class="chat-header">
                    <div class="chat-header-info">
                        <h3>LMS Core AI</h3>
                        <p>Trợ lý AI thông minh</p>
                    </div>
                    <i class="fa-solid fa-xmark close-btn" onclick="toggleChat()"></i>
                </div>
                
                <div class="category-toggle-btn" onclick="toggleCategoryContent()">
                    <span style="display: flex; align-items: center; overflow: hidden; white-space: nowrap; flex: 1; margin-right: 10px;">
                        <i class="fa-regular fa-folder-open" style="margin-right: 6px; flex-shrink: 0;"></i> 
                        <span id="category-toggle-text" style="overflow: hidden; text-overflow: ellipsis; color: #2563eb;">Chat tự do (Mặc định)</span>
                    </span>
                    <i id="category-toggle-icon" class="fa-solid fa-chevron-down" style="flex-shrink: 0;"></i>
                </div>

                <div id="category-checkbox-container" class="chat-category-content category-list">
                    <span style="font-size: 12px; color: #94a3b8;">Đang tải chủ đề...</span>
                </div>
                                <div class="chat-messages" id="chat-messages"></div>
                <div class="typing" id="typing-indicator">AI đang suy nghĩ...</div>
                
                <!-- THANH CÔNG CỤ TẠO NHANH DỰA TRÊN TÀI LIỆU -->
                <div class="chat-quick-actions">
                    <button class="quick-action-btn" onclick="sendQuickAction('lesson')"><i class="fa-solid fa-book-open"></i> Tạo bài giảng</button>
                    <button class="quick-action-btn" onclick="sendQuickAction('quiz')"><i class="fa-solid fa-circle-question"></i> Tạo Quiz trắc nghiệm</button>
                    <button class="quick-action-btn" onclick="sendQuickAction('exercise')"><i class="fa-solid fa-pen-to-square"></i> Tạo bài tập</button>
                </div>

                <div class="chat-input-area">
                    <input type="text" id="chat-input" placeholder="Hỏi tôi bất cứ điều gì..." onkeypress="handleEnter(event)">
                    <button onclick="sendMessage()"><i class="fa-solid fa-paper-plane"></i></button>
                </div>
            </div>
        `;

        // Kích hoạt sự kiện Resize sau khi chèn HTML
        initResizeHandler();
    }

    setTimeout(injectLMSChat, 500);

    // ==========================================
    // HÀM BẮT SỰ KIỆN KÉO DÃN (RESIZE)
    // ==========================================
    function initResizeHandler() {
        const handle = document.getElementById('resize-handle');
        const win = document.getElementById('lms-chat-window');
        if (!handle || !win || handle.dataset.bound) return;
        handle.dataset.bound = 'true';

        handle.addEventListener('mousedown', (e) => {
            e.preventDefault();
            const startX = e.clientX;
            const startY = e.clientY;
            const startWidth = parseInt(window.getComputedStyle(win).width, 10);
            const startHeight = parseInt(window.getComputedStyle(win).height, 10);

            function doResize(moveEvent) {
                // Kéo sang trái (startX > clientX) -> Tăng chiều rộng
                const deltaX = startX - moveEvent.clientX;
                // Kéo lên trên (startY > clientY) -> Tăng chiều cao
                const deltaY = startY - moveEvent.clientY;

                const newWidth = startWidth + deltaX;
                const newHeight = startHeight + deltaY;

                // Áp dụng giới hạn min/max
                if (newWidth >= 300 && newWidth <= window.innerWidth * 0.9) {
                    win.style.width = newWidth + 'px';
                }
                if (newHeight >= 400 && newHeight <= window.innerHeight * 0.9) {
                    win.style.height = newHeight + 'px';
                }
            }

            function stopResize() {
                window.removeEventListener('mousemove', doResize);
                window.removeEventListener('mouseup', stopResize);
            }

            window.addEventListener('mousemove', doResize);
            window.addEventListener('mouseup', stopResize);
        });
    }

    // Observer bắt sự kiện đổi trang của Vue/SPA
    const observer = new MutationObserver(function() {
        if (!document.getElementById('lms-chat-container')) {
            injectLMSChat();
        }
    });
    observer.observe(document.body, { childList: true, subtree: true });

    let isHistoryLoaded = false;

    // Các hàm xử lý giao diện
    window.toggleCategoryContent = function() {
        const content = document.getElementById('category-checkbox-container');
        const icon = document.getElementById('category-toggle-icon');
        if (content.classList.contains('show')) {
            content.classList.remove('show');
            icon.classList.replace('fa-chevron-up', 'fa-chevron-down');
        } else {
            content.classList.add('show');
            icon.classList.replace('fa-chevron-down', 'fa-chevron-up');
        }
    }

    function updateCategoryToggleText() {
        const textElement = document.getElementById('category-toggle-text');
        if (!textElement) return;

        const container = document.getElementById('category-checkbox-container');
        const freeChatCheckbox = container.querySelector('input[name="chat_category"][value=""]');
        const allCategoriesCheckbox = container.querySelector('input[name="chat_category"][value="ALL_CATEGORIES"]');
        const checkedOtherBoxes = container.querySelectorAll('input[name="chat_category"]:not([value=""]):not([value="ALL_CATEGORIES"]):checked');

        if (allCategoriesCheckbox && allCategoriesCheckbox.checked) {
            textElement.innerText = "Tất cả chủ đề";
            textElement.style.color = "#2563eb";
        } 
        else if (checkedOtherBoxes.length > 0) {
            const selectedNames = Array.from(checkedOtherBoxes).map(cb => cb.value);
            textElement.innerText = selectedNames.join(', ');
            textElement.style.color = "#0f172a";
        } 
        else {
            if (freeChatCheckbox) freeChatCheckbox.checked = true;
            textElement.innerText = "Chat tự do (Mặc định)";
            textElement.style.color = "#64748b";
        }
    }

    function setupCategoryCheckboxLogic() {
        const container = document.getElementById('category-checkbox-container');
        if (!container) return;

        container.addEventListener('change', function(e) {
            if (e.target.name !== 'chat_category') return;
            const freeChatCheckbox = container.querySelector('input[name="chat_category"][value=""]');
            const allCategoriesCheckbox = container.querySelector('input[name="chat_category"][value="ALL_CATEGORIES"]');
            const otherCheckboxes = container.querySelectorAll('input[name="chat_category"]:not([value=""]):not([value="ALL_CATEGORIES"])');

            if (e.target.value === "") {
                if (e.target.checked) {
                    if (allCategoriesCheckbox) allCategoriesCheckbox.checked = false;
                    otherCheckboxes.forEach(cb => cb.checked = false);
                }
            } else if (e.target.value === "ALL_CATEGORIES") {
                if (e.target.checked) {
                    if (freeChatCheckbox) freeChatCheckbox.checked = false;
                    otherCheckboxes.forEach(cb => cb.checked = false);
                }
            } else {
                if (e.target.checked) {
                    if (freeChatCheckbox) freeChatCheckbox.checked = false;
                    if (allCategoriesCheckbox) allCategoriesCheckbox.checked = false;
                }
            }
            
            const anyChecked = container.querySelector('input[name="chat_category"]:checked');
            if (!anyChecked && freeChatCheckbox) {
                freeChatCheckbox.checked = true;
            }
            
            updateCategoryToggleText();
        });
    }

    window.loadCategories = async function() {
        const container = document.getElementById('category-checkbox-container');
        if (!container || container.getAttribute('data-loaded') === 'true') return;

        try {
            const response = await fetch('/api/method/lms_ai.api.get_categories', {
                method: 'GET',
                headers: { 'Accept': 'application/json', 'Content-Type': 'application/json' }
            });

            if (!response.ok) throw new Error(`Lỗi HTTP: ${response.status}`);
            
            const r = await response.json();
            container.innerHTML = ''; 

            const defaultLabel = document.createElement('label');
            defaultLabel.className = 'category-item';
            defaultLabel.innerHTML = `
                <input type="checkbox" name="chat_category" value="" checked>
                <span style="font-weight: 500; color: #0f172a;">Chat tự do (Không dùng tài liệu)</span>
            `;
            container.appendChild(defaultLabel);

            const allLabel = document.createElement('label');
            allLabel.className = 'category-item';
            allLabel.innerHTML = `
                <input type="checkbox" name="chat_category" value="ALL_CATEGORIES">
                <span style="font-weight: 600; color: #2563eb;">Tìm trong TẤT CẢ chủ đề</span>
            `;
            container.appendChild(allLabel);

            if (r.message && Array.isArray(r.message) && r.message.length > 0) {
                r.message.forEach((cat) => {
                    if (cat) {
                        const label = document.createElement('label');
                        label.className = 'category-item';
                        label.innerHTML = `
                            <input type="checkbox" name="chat_category" value="${cat}">
                            <span>${cat}</span>
                        `;
                        container.appendChild(label);
                    }
                });
            }
            
            container.setAttribute('data-loaded', 'true');
            setupCategoryCheckboxLogic();
            updateCategoryToggleText();

        } catch (error) {
            console.error("Lỗi khi load category:", error);
            container.innerHTML = '<span style="font-size: 12px; color: red;">Lỗi tải chủ đề</span>';
        }
    };

    window.toggleChat = async function() {
        const chatWindow = document.getElementById('lms-chat-window');
        if(chatWindow) {
            chatWindow.style.display = (chatWindow.style.display === 'flex') ? 'none' : 'flex';
            
            if (chatWindow.style.display === 'flex') {
                loadCategories(); 
                
                if (!isHistoryLoaded) {
                    const chatMessages = document.getElementById('chat-messages');
                    chatMessages.innerHTML = '<div style="text-align: center; color: #94a3b8; font-size: 13px; padding: 10px;"><i class="fa-solid fa-spinner fa-spin"></i> Đang tải lịch sử...</div>';
                    
                    try {
                        const response = await fetch('/api/method/lms_ai.api.get_chat_history', {
                            method: 'GET',
                            headers: { 'Accept': 'application/json', 'Content-Type': 'application/json' }
                        });

                        if (!response.ok) throw new Error(`Lỗi HTTP: ${response.status}`);
                        
                        const r = await response.json();
                        chatMessages.innerHTML = ''; 
                        
                        renderMessage('bot', "Xin chào! Tôi có thể giúp gì cho bạn hôm nay?", false);
                        
                        if (r.message && r.message.length > 0) {
                            r.message.reverse();
                            r.message.forEach(log => {
                                let sender = (log.role === 'user') ? 'user' : 'bot';
                                let logText = log.message;
                                
                                if (sender === 'bot') {
                                    if (typeof marked !== 'undefined') {
                                        logText = marked.parse(logText);
                                    } else {
                                        logText = logText.replace(/\n/g, '<br>');
                                    }
                                    renderMessage(sender, logText, true); 
                                } else {
                                    renderMessage(sender, logText, false); 
                                }
                            });
                        }
                        isHistoryLoaded = true;
                    } catch (error) {
                        console.error("Lỗi load lịch sử:", error);
                        chatMessages.innerHTML = '';
                        renderMessage('bot', "Xin chào! Tôi có thể giúp gì cho bạn hôm nay?", false);
                    }
                }
            }
        }
    };

        window.handleEnter = function(e) {
            if (e.key === 'Enter') sendMessage();
        }

        // HÀM TỰ ĐỘNG ĐIỀN DỮ LIỆU VÀO FORM LMS
        window.injectIntoLMSForm = function(btn) {
            const msgContent = btn.closest('.msg-content');
            if (!msgContent) return;
        
            // Lấy toàn bộ nội dung text thuần hoặc HTML của câu trả lời (loại bỏ phần tài liệu tham khảo và nút bấm)
            const clone = msgContent.cloneNode(true);
            const refDiv = clone.querySelector('div[style*="border-top: 1px dashed"]');
            if (refDiv) refDiv.remove();
            const btnDiv = clone.querySelector('div[style*="justify-content: flex-end"]');
            if (btnDiv) btnDiv.remove();
        
            const cleanText = clone.innerHTML.trim();
            const plainText = clone.innerText.trim();

            let filledCount = 0;

            // 1. Tìm các textarea hoặc input tiêu đề / nội dung bài học / câu hỏi trên trang
            const textareas = document.querySelectorAll('textarea, input[type="text"]');
            textareas.forEach(el => {
                // Kiểm tra xem trường này có phải là nơi nhập nội dung bài học, mô tả, câu hỏi hay không
                const placeholder = (el.getAttribute('placeholder') || '').toLowerCase();
                const name = (el.getAttribute('name') || '').toLowerCase();
                const id = (el.getAttribute('id') || '').toLowerCase();
            
                if (placeholder.includes('nội dung') || placeholder.includes('mô tả') || placeholder.includes('soạn') || 
                    name.includes('content') || name.includes('description') || name.includes('question') || 
                    id.includes('content') || id.includes('description') || id.includes('question')) {
                
                    if (el.value === '' || confirm('Trường nhập liệu đã có dữ liệu. Bạn có muốn ghi đè nội dung từ AI vào không?')) {
                        el.value = plainText;
                        el.dispatchEvent(new Event('input', { bubbles: true }));
                        el.dispatchEvent(new Event('change', { bubbles: true }));
                        filledCount++;
                    }
                }
            });

            // 2. Tìm các Frappe Rich Text Editor / Quill Editor nếu có
            const editors = document.querySelectorAll('.ql-editor, .frappe-control textarea');
            editors.forEach(ed => {
                ed.innerHTML = cleanText;
                ed.dispatchEvent(new Event('input', { bubbles: true }));
                filledCount++;
            });

            if (filledCount > 0) {
                alert(`Đã tự động điền nội dung thành công vào ${filledCount} trường trên form LMS!`);
            } else {
                // Fallback: Copy vào clipboard nếu không tìm thấy ô phù hợp
                navigator.clipboard.writeText(plainText).then(() => {
                    alert('Không tìm thấy ô nhập liệu tương thích trên trang hiện tại. Nội dung đã được copy vào clipboard để bạn dán (Paste) thủ công!');
                });
            }
        };

    // HÀM XỬ LÝ GỬI YÊU CẦU TẠO NHANH DỰA TRÊN TÀI LIỆU ĐÃ CHỌN
    window.sendQuickAction = function(actionType) {
        const input = document.getElementById('chat-input');
        let promptText = '';
        
        // Kiểm tra xem người dùng đang chọn chủ đề/tài liệu nào
        const toggleText = document.getElementById('category-toggle-text')?.innerText || 'tài liệu đã chọn';
        
        if (actionType === 'lesson') {
            promptText = `Dựa vào tài liệu thuộc chủ đề "${toggleText}", hãy soạn giúp tôi một bài giảng chi tiết bao gồm: Mục tiêu, Nội dung chính, Ví dụ minh họa và Tóm tắt bài học.`;
        } else if (actionType === 'quiz') {
            promptText = `Dựa vào tài liệu thuộc chủ đề "${toggleText}", hãy tạo giúp tôi 5 câu hỏi trắc nghiệm (có 4 đáp án A, B, C, D) kèm theo đáp án đúng và lời giải chi tiết.`;
        } else if (actionType === 'exercise') {
            promptText = `Dựa vào tài liệu thuộc chủ đề "${toggleText}", hãy thiết kế giúp tôi các bài tập thực hành hoặc câu hỏi tự luận kèm gợi ý trả lời.`;
        }

        if (promptText) {
            input.value = promptText;
            sendMessage();
        }
    };

    window.renderMessage = function(sender, text, isHtml = false) {
        const msgDiv = document.createElement('div');
        msgDiv.className = sender === 'user' ? 'msg msg-user' : 'msg msg-bot';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'msg-content';

        if (isHtml) {
            contentDiv.innerHTML = text; 
        } else {
            contentDiv.innerText = text; 
        }
        
        msgDiv.appendChild(contentDiv);
        
        const chatMessages = document.getElementById('chat-messages');
        if(chatMessages) {
            chatMessages.appendChild(msgDiv);
            setTimeout(() => { chatMessages.scrollTop = chatMessages.scrollHeight; }, 50);
        }
    }

    window.typewriterEffectHtml = function(element, htmlContent, callback) {
        const temp = document.createElement('div');
        temp.innerHTML = htmlContent;
        const children = Array.from(temp.childNodes);
        element.innerHTML = '';

        let index = 0;
        function showNext() {
            if (index < children.length) {
                const child = children[index];
                child.style = 'opacity: 0; transition: opacity 0.5s ease-in;';
                element.appendChild(child);
        
                void child.offsetWidth;
                child.style.opacity = 1;

                const chatMessages = document.getElementById('chat-messages');
                if (chatMessages) chatMessages.scrollTop = chatMessages.scrollHeight;
        
                index++;
                setTimeout(showNext, 150);
            } else if (callback) {
                callback();
            }
        }
        showNext();
    };

    window.sendMessage = async function() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();

        if (!message) return;

        let categories = [];
        const isAllChecked = document.querySelector('input[name="chat_category"][value="ALL_CATEGORIES"]')?.checked;

        if (isAllChecked) {
            const allBoxes = document.querySelectorAll('input[name="chat_category"]');
            categories = Array.from(allBoxes)
                .map(cb => cb.value)
                .filter(val => val !== "" && val !== "ALL_CATEGORIES"); 
        } else {
            const selectedCheckboxes = document.querySelectorAll('input[name="chat_category"]:checked');
            categories = Array.from(selectedCheckboxes)
                .map(cb => cb.value)
                .filter(val => val !== "" && val !== "ALL_CATEGORIES");
        }

        renderMessage('user', message, false);
        input.value = '';

        const typingIndicator = document.getElementById('typing-indicator');
        if(typingIndicator) typingIndicator.style.display = 'block';

        const chatMessages = document.getElementById('chat-messages');
        if(chatMessages) chatMessages.scrollTop = chatMessages.scrollHeight;

        try {
            const response = await fetch('/api/method/lms_ai.api.ask_ai', {
                method: 'POST',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'X-Frappe-CSRF-Token': (typeof frappe !== 'undefined' && frappe.csrf_token) ? frappe.csrf_token : (window.csrf_token || '')
                },
                body: JSON.stringify({ message: message, categories: categories })
            });

            if (!response.ok) throw new Error(`Lỗi HTTP: ${response.status}`);

            const r = await response.json();

            if(typingIndicator) typingIndicator.style.display = 'none';

            if(r.message && r.message.reply) {
                let replyText = r.message.reply;
                let finalReply = '';

                if (typeof marked !== 'undefined') {
                    finalReply = marked.parse(replyText);
                } else {
                    finalReply = replyText.replace(/\n/g, '<br>');
                }

                // Thêm tài liệu tham khảo và nút Đưa vào Form LMS
                if (r.message.references && r.message.references.length > 0 && categories.length > 0) {
                    finalReply += `<div style="margin-top: 15px; padding-top: 10px; border-top: 1px dashed #cbd5e1; font-size: 13px;">`;
                    finalReply += `<strong><i class="fa-solid fa-layer-group" style="margin-right: 5px; color: #2563eb;"></i> Tài liệu tham khảo:</strong>`;
                    finalReply += `<ul style="margin-top: 8px; padding-left: 20px !important; list-style-type: none; display: flex; flex-direction: column; gap: 5px;">`;
                    
                    r.message.references.forEach(ref => {
                        finalReply += `<li style="margin-bottom: 0 !important;">
                            <a href="${ref.url}" target="_blank" style="color: #2563eb; text-decoration: none; font-weight: 500; display: inline-flex; align-items: center; gap: 5px;">
                                <i class="fa-solid fa-file-lines" style="color: #64748b;"></i> ${ref.title}
                            </a>
                        </li>`;
                    });
                    finalReply += `</ul></div>`;
                }

                // Nút Đưa vào Form LMS
                finalReply += `<div style="margin-top: 12px; padding-top: 8px; border-top: 1px solid #e2e8f0; display: flex; justify-content: flex-end;">
                    <button onclick="injectIntoLMSForm(this)" style="background: #10b981; color: white; border: none; padding: 6px 12px; border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer; display: inline-flex; align-items: center; gap: 5px; transition: background 0.2s;">
                        <i class="fa-solid fa-file-arrow-down"></i> Đưa vào Form LMS
                    </button>
                </div>`;

                renderMessage('bot', '', true);
                const botMsgs = document.querySelectorAll('.msg-bot');
                const targetMsgContent = botMsgs[botMsgs.length - 1].querySelector('.msg-content');

                typewriterEffectHtml(targetMsgContent, finalReply, () => {
                    const chatMessages = document.getElementById('chat-messages');
                    if (chatMessages) chatMessages.scrollTop = chatMessages.scrollHeight;
                });
            } else {
                renderMessage('bot', "Xin lỗi, đã xảy ra lỗi khi xử lý dữ liệu từ AI.", false);
            }
        } catch (error) {
            if(typingIndicator) typingIndicator.style.display = 'none';
            console.error("Lỗi gọi AI:", error);
            renderMessage('bot', "Đã mất kết nối hoặc có lỗi xảy ra. Vui lòng thử lại sau.", false);
        }
    };

    // ==========================================
    // 5. AUTO-CLOSE KHI CLICK RA NGOÀI
    // ==========================================
    document.addEventListener('click', function(event) {
        const chatWindow = document.getElementById('lms-chat-window');
        const chatBtn = document.getElementById('lms-chat-btn');
        const categoryContainer = document.getElementById('category-checkbox-container');
        const categoryToggleBtn = document.querySelector('.category-toggle-btn');
        const categoryIcon = document.getElementById('category-toggle-icon');

        if (categoryContainer && categoryContainer.classList.contains('show')) {
            if (!categoryContainer.contains(event.target) && categoryToggleBtn && !categoryToggleBtn.contains(event.target)) {
                categoryContainer.classList.remove('show');
                if (categoryIcon) categoryIcon.classList.replace('fa-chevron-up', 'fa-chevron-down');
            }
        }

        if (chatWindow && chatWindow.style.display === 'flex') {
            if (!chatWindow.contains(event.target) && chatBtn && !chatBtn.contains(event.target)) {
                chatWindow.style.display = 'none';
            }
        }
    });

} else {
    console.warn("⚠️ LMS AI Chat đã được nạp trước đó. Bỏ qua để tránh duplicate.");
}