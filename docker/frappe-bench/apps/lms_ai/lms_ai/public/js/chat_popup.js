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
                #lms-chat-btn { position: fixed !important; bottom: 30px !important; right: 30px !important; height: 55px !important; padding: 0 20px !important; background: #074942 !important; color: #F2B814 !important; border-radius: 30px !important; display: flex !important; align-items: center !important; justify-content: center !important; gap: 10px !important; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important; font-size: 16px !important; font-weight: 600 !important; cursor: pointer !important; box-shadow: 0 4px 15px rgba(7, 73, 66, 0.4) !important; z-index: 2147483647 !important; transition: all 0.3s ease !important; }
                #lms-chat-btn i { font-size: 20px !important; }
                #lms-chat-btn:hover { transform: translateY(-3px) !important; box-shadow: 0 6px 20px rgba(7, 73, 66, 0.6) !important; }
                
                /* CỬA SỔ CHAT */
                #lms-chat-window { position: fixed !important; bottom: 100px !important; right: 30px !important; width: 380px !important; height: 580px !important; min-width: 300px !important; min-height: 400px !important; max-width: 90vw !important; max-height: 90vh !important; background: #ffffff !important; border-radius: 16px !important; box-shadow: 0 10px 30px rgba(0,0,0,0.15) !important; display: none; flex-direction: column !important; z-index: 2147483647 !important; border: 1px solid #e2e8f0 !important; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important; overflow: hidden !important; }
                
                /* ĐIỂM KÉO RESIZE GÓC TRÊN-TRÁI */
                .resize-handle { position: absolute; top: 0; left: 0; width: 25px; height: 25px; cursor: nwse-resize; z-index: 100; background: transparent; }
                
                /* HEADER */
                .chat-header { background: #074942 !important; color: #F2B814 !important; padding: 15px 20px !important; display: flex !important; justify-content: space-between !important; align-items: center !important; }
                .chat-header-info { display: flex; flex-direction: column; }
                .chat-header-info h3 { font-size: 16px !important; font-weight: 600 !important; margin: 0 !important; color: #F2B814 !important;}
                .chat-header-info p { font-size: 12px !important; opacity: 0.9 !important; margin: 0 !important; margin-top: 2px !important; color: #F2B814 !important;}
                .close-btn { cursor: pointer !important; font-size: 18px !important; transition: opacity 0.2s; color: #F2B814 !important; }
                .close-btn:hover { opacity: 0.7; }
                
                /* GIAO DIỆN CHỌN CHỦ ĐỀ */
                .category-toggle-btn { padding: 12px 15px !important; background: #074942 !important; border-top: 1px solid #063d37 !important; border-bottom: 1px solid #063d37 !important; display: flex !important; justify-content: space-between !important; align-items: center !important; cursor: pointer !important; font-size: 13px !important; font-weight: 600 !important; color: #F2B814 !important; transition: background 0.2s; overflow: hidden; }
                .category-toggle-btn:hover { background: #0a5c53 !important; }
                .category-toggle-btn i { color: #F2B814 !important; flex-shrink: 0; }
                .chat-category-content { display: none !important; padding: 10px 15px !important; background: #074942 !important; border-bottom: 1px solid #063d37 !important; max-height: 140px !important; overflow-y: auto !important; box-shadow: inset 0 -5px 10px -10px rgba(0,0,0,0.3); }
                .chat-category-content.show { display: flex !important; }
                .category-list { flex-direction: column !important; gap: 8px !important; }
                .category-item { display: flex !important; align-items: center !important; gap: 8px !important; font-size: 13px !important; color: #ffffff !important; cursor: pointer !important; padding: 2px 0; }
                .category-item input { cursor: pointer !important; width: 16px; height: 16px; accent-color: #F2B814 !important; margin: 0;}
                
                /* VÙNG TIN NHẮN (Độc lập tuyệt đối khỏi Dark Theme của trang cha) */
                .chat-messages { flex: 1 !important; padding: 15px !important; overflow-y: auto !important; background: #f8fafc !important; color: #1e293b !important; display: flex !important; flex-direction: column !important; gap: 12px !important; scroll-behavior: smooth; }
                .msg { max-width: 82% !important; padding: 12px 16px !important; border-radius: 16px !important; font-size: 14px !important; line-height: 1.5 !important; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }

                /* BONG BÓNG BOT & USER */
                .msg-bot { background: #ffffff !important; color: #1e293b !important; align-self: flex-start !important; border: 1px solid #e2e8f0 !important; border-bottom-left-radius: 4px !important; }
                .msg-user { background: #074942 !important; color: #ffffff !important; align-self: flex-end !important; border-bottom-right-radius: 4px !important; }
                .msg-user, .msg-user * { color: #ffffff !important; }

                /* CHỮ & TIÊU ĐỀ BÊN TRONG BOT */
                .msg-bot p, .msg-bot span, .msg-bot div, .msg-bot li, .msg-bot strong, .msg-bot em { 
                    color: #1e293b !important; 
                }
                [data-theme='dark'] #lms-chat-window .msg-bot h1,
                [data-theme='dark'] #lms-chat-window .msg-bot h2,
                [data-theme='dark'] #lms-chat-window .msg-bot h3,
                [data-theme='dark'] #lms-chat-window .msg-bot h4,
                [data-theme='dark'] #lms-chat-window .msg-bot h5,
                [data-theme='dark'] #lms-chat-window .msg-bot h6,
                .msg-bot h1, .msg-bot h2, .msg-bot h3, .msg-bot h4, .msg-bot h5, .msg-bot h6 {
                    color: #0f172a !important;
                    font-weight: 700 !important;
                }
                .msg-bot a { color: #074942 !important; text-decoration: underline !important; }

                /* CSS MARKDOWN */
                .msg-content { word-wrap: break-word; overflow-wrap: break-word; width: 100%; }
                .msg-content p { margin: 0 0 10px 0; }
                .msg-content p:last-child { margin: 0; }
                .msg-content ul, .msg-content ol { padding-left: 20px !important; margin: 8px 0 !important; }
                .msg-content li { margin-bottom: 6px !important; line-height: 1.5; }

                /* INLINE CODE */
                .msg-content :not(pre) > code,
                #lms-chat-window .msg-content :not(pre) > code { 
                    background-color: #f1f5f9 !important; 
                    color: #b91c1c !important; 
                    padding: 2px 6px !important; 
                    border-radius: 4px !important; 
                    border: 1px solid #e2e8f0 !important;
                    font-family: 'JetBrains Mono', 'Fira Code', Consolas, Monaco, monospace !important; 
                    font-size: 12.5px !important; 
                    font-weight: 600 !important;
                    word-break: break-word; 
                }

                /* CODE BLOCK HIỆN ĐẠI (Dark Slate) */
                .msg-content pre,
                #lms-chat-window .msg-content pre { 
                    background: #1e293b !important; 
                    color: #e2e8f0 !important; 
                    padding: 14px 16px !important; 
                    border-radius: 10px !important; 
                    border: 1px solid #334155 !important; 
                    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08) !important;
                    overflow-x: auto !important; 
                    margin: 12px 0 !important; 
                    font-family: 'JetBrains Mono', 'Fira Code', Consolas, Monaco, monospace !important; 
                    font-size: 13px !important; 
                    line-height: 1.6 !important;
                }

                .msg-content pre *,
                .msg-content pre code,
                #lms-chat-window .msg-content pre *,
                #lms-chat-window .msg-content pre code { 
                    color: #e2e8f0 !important; 
                    background-color: transparent !important; 
                    font-family: inherit !important;
                }

                /* Scrollbar mini cho code block */
                .msg-content pre::-webkit-scrollbar {
                    height: 5px !important;
                }
                .msg-content pre::-webkit-scrollbar-track {
                    background: #1e293b !important;
                    border-radius: 4px !important;
                }
                .msg-content pre::-webkit-scrollbar-thumb {
                    background: #475569 !important;
                    border-radius: 4px !important;
                }
                .msg-content pre::-webkit-scrollbar-thumb:hover {
                    background: #64748b !important;
                }

                .msg-content table { border-collapse: collapse; width: 100%; margin: 10px 0; }
                .msg-content th, .msg-content td { border: 1px solid #cbd5e1; padding: 8px; text-align: left; color: inherit !important; }
                
                /* SCROLLBAR CHUNG */
                .chat-messages::-webkit-scrollbar, .chat-category-content::-webkit-scrollbar { width: 6px; }
                .chat-messages::-webkit-scrollbar-track, .chat-category-content::-webkit-scrollbar-track { background: transparent; }
                .chat-messages::-webkit-scrollbar-thumb { background-color: #cbd5e1; border-radius: 10px; }
                .chat-category-content::-webkit-scrollbar-thumb { background-color: #0a5c53; border-radius: 10px; }
                
                /* KHU VỰC NHẬP TEXT */
                .chat-input-area { padding: 15px !important; background: #ffffff !important; border-top: 1px solid #e2e8f0 !important; display: flex !important; gap: 10px !important; align-items: center; }
                .chat-input-area input { flex: 1 !important; padding: 12px 16px !important; border: 1px solid #cbd5e1 !important; border-radius: 24px !important; outline: none !important; color: #0f172a !important; font-size: 14px; transition: border-color 0.2s; background: #f8fafc !important; }
                .chat-input-area input:focus { border-color: #074942 !important; background: #ffffff !important; }
                .chat-input-area button { background: #074942 !important; color: #F2B814 !important; border: none !important; border-radius: 50% !important; width: 42px !important; height: 42px !important; cursor: pointer !important; display: flex !important; align-items: center !important; justify-content: center !important; transition: background 0.2s, transform 0.2s; }
                .chat-input-area button:hover { background: #053732 !important; transform: scale(1.05); }
                .chat-input-area button i { color: #F2B814 !important; }
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
                        <i class="fa-regular fa-folder-open" style="margin-right: 6px; flex-shrink: 0; color: #F2B814;"></i> 
                        <span id="category-toggle-text" style="overflow: hidden; text-overflow: ellipsis; color: #F2B814;">Chat tự do (Mặc định)</span>
                    </span>
                    <i id="category-toggle-icon" class="fa-solid fa-chevron-down" style="flex-shrink: 0; color: #F2B814;"></i>
                </div>

                <div id="category-checkbox-container" class="chat-category-content category-list">
                    <span style="font-size: 12px; color: #F2B814;">Đang tải chủ đề...</span>
                </div>
                <div class="chat-messages" id="chat-messages"></div>
                <div class="typing" id="typing-indicator">AI đang suy nghĩ...</div>
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
                const deltaX = startX - moveEvent.clientX;
                const deltaY = startY - moveEvent.clientY;

                const newWidth = startWidth + deltaX;
                const newHeight = startHeight + deltaY;

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
    };

    function updateCategoryToggleText() {
        const textElement = document.getElementById('category-toggle-text');
        if (!textElement) return;

        const container = document.getElementById('category-checkbox-container');
        const freeChatCheckbox = container.querySelector('input[name="chat_category"][value=""]');
        const allCategoriesCheckbox = container.querySelector('input[name="chat_category"][value="ALL_CATEGORIES"]');
        const checkedOtherBoxes = container.querySelectorAll('input[name="chat_category"]:not([value=""]):not([value="ALL_CATEGORIES"]):checked');

        textElement.style.color = "#F2B814";

        if (allCategoriesCheckbox && allCategoriesCheckbox.checked) {
            textElement.innerText = "Tất cả chủ đề";
        } 
        else if (checkedOtherBoxes.length > 0) {
            const selectedNames = Array.from(checkedOtherBoxes).map(cb => cb.value);
            textElement.innerText = selectedNames.join(', ');
        } 
        else {
            if (freeChatCheckbox) freeChatCheckbox.checked = true;
            textElement.innerText = "Chat tự do (Mặc định)";
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
                <span style="font-weight: 500; color: #F2B814;">Chat tự do (Không dùng tài liệu)</span>
            `;
            container.appendChild(defaultLabel);

            const allLabel = document.createElement('label');
            allLabel.className = 'category-item';
            allLabel.innerHTML = `
                <input type="checkbox" name="chat_category" value="ALL_CATEGORIES">
                <span style="font-weight: 600; color: #F2B814;">Tìm trong TẤT CẢ chủ đề</span>
            `;
            container.appendChild(allLabel);

            if (r.message && Array.isArray(r.message) && r.message.length > 0) {
                r.message.forEach((cat) => {
                    if (cat) {
                        const label = document.createElement('label');
                        label.className = 'category-item';
                        label.innerHTML = `
                            <input type="checkbox" name="chat_category" value="${cat}">
                            <span style="color: #ffffff;">${cat}</span>
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
            container.innerHTML = '<span style="font-size: 12px; color: #ef4444;">Lỗi tải chủ đề</span>';
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
    };

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