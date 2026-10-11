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
    // console.log("🚀 LMS AI Chat Script đang chạy (Đã bật Auto-Close & Bắt buộc mặc định Chat tự do)...");

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
                #chat-send:disabled { opacity: .45; cursor: not-allowed !important; }
                #lms-chat-window .document-evidence { border-left: 3px solid #cbd5e1; margin: 6px 0; padding-left: 9px; white-space: pre-wrap; overflow-wrap: anywhere; }
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

                <div class="category-toggle-btn" onclick="toggleDocumentContent()">
                    <span style="display: flex; align-items: center; overflow: hidden; white-space: nowrap; flex: 1; margin-right: 10px;">
                        <i class="fa-regular fa-folder-open" style="margin-right: 6px; flex-shrink: 0; color: #F2B814;"></i>
                        <span id="document-toggle-text" style="overflow: hidden; text-overflow: ellipsis; color: #F2B814;">Chọn tài liệu để hỏi</span>
                    </span>
                    <i id="document-toggle-icon" class="fa-solid fa-chevron-down" style="flex-shrink: 0; color: #F2B814;"></i>
                </div>

                <div id="document-checkbox-container" class="chat-category-content category-list">
                    <span style="font-size: 12px; color: #F2B814;">Đang tải tài liệu...</span>
                </div>
                <div class="chat-messages" id="chat-messages"></div>
                <div class="typing" id="typing-indicator">AI đang suy nghĩ...</div>
                <div class="chat-input-area">
                    <input type="text" id="chat-input" maxlength="16000" aria-label="Câu hỏi" placeholder="Hỏi tôi bất cứ điều gì..." onkeypress="handleEnter(event)">
                    <button id="chat-send" aria-label="Gửi câu hỏi" disabled onclick="sendMessage()"><i class="fa-solid fa-paper-plane"></i></button>
                </div>
            </div>
        `;

        // Kích hoạt sự kiện Resize sau khi chèn HTML
        initResizeHandler();
        isHistoryLoaded = false;
        updateControls();
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
                    win.style.setProperty('width', newWidth + 'px', 'important');
                }
                if (newHeight >= 400 && newHeight <= window.innerHeight * 0.9) {
                    win.style.setProperty('height', newHeight + 'px', 'important');
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


    // The original presentation is retained; requests use the OpenKB backend.
    let isHistoryLoaded = false;
    let historyLoading = null;
    let selected = new Set();
    let titles = new Map();
    let busy = false;
    const newContext = () => typeof crypto.randomUUID === 'function' ? crypto.randomUUID()
        : Array.from(crypto.getRandomValues(new Uint8Array(16)), byte => byte.toString(16).padStart(2, '0')).join('');
    let contextId = newContext();
    const apiRoot = '/api/method/lms_ai.api.';
    const byId = id => document.getElementById(id);

    async function api(method, payload) {
        const headers = {Accept: 'application/json'};
        const options = {credentials: 'same-origin', headers};
        if (payload) {
            options.method = 'POST';
            headers['Content-Type'] = 'application/json';
            headers['X-Frappe-CSRF-Token'] = window.frappe?.csrf_token || window.csrf_token || '';
            options.body = JSON.stringify(payload);
        }
        const response = await fetch(apiRoot + method, options);
        const result = await response.json();
        if (!response.ok || result.exc) throw new Error('Yêu cầu chưa thành công. Kiểm tra đăng nhập và trạng thái tài liệu, hoặc liên hệ quản trị viên.');
        return result.message;
    }

    function updateControls() {
        const send = byId('chat-send');
        const input = byId('chat-input');
        if (!send || !input) return;
        send.disabled = busy || !selected.size || !input.value.trim();
        input.disabled = busy;
        byId('document-checkbox-container').querySelectorAll('input').forEach(box => { box.disabled = busy; });
        const summary = byId('document-toggle-text');
        summary.textContent = selected.size ? [...selected].map(id => titles.get(id) || id).join(', ') : 'Chọn tài liệu để hỏi';
        summary.title = selected.size ? summary.textContent : 'Chọn ít nhất một tài liệu đã xử lý thành công';
    }

    async function loadDocuments() {
        const holder = byId('document-checkbox-container');
        if (!holder || busy) return;
        try {
            const docs = await api('get_documents');
            const available = new Set(docs.map(doc => doc.name));
            const previous = [...selected].sort().join('|');
            selected = new Set([...selected].filter(id => available.has(id)));
            if (previous !== [...selected].sort().join('|')) contextId = newContext();
            titles = new Map(docs.map(doc => [doc.name, doc.title || doc.name]));
            holder.replaceChildren();
            if (!docs.length) holder.textContent = 'Chưa có tài liệu xử lý thành công.';
            docs.forEach(doc => {
                const label = document.createElement('label');
                label.className = 'category-item';
                const box = document.createElement('input');
                box.type = 'checkbox';
                box.name = 'chat_document';
                box.value = doc.name;
                box.checked = selected.has(doc.name);
                box.addEventListener('change', () => {
                    if (box.checked) selected.add(doc.name); else selected.delete(doc.name);
                    contextId = newContext();
                    updateControls();
                });
                const title = document.createElement('span');
                title.textContent = doc.title || doc.name;
                label.append(box, title);
                holder.append(label);
            });
        } catch (error) { holder.textContent = error.message; }
        updateControls();
    }

    window.toggleDocumentContent = function() {
        const content = byId('document-checkbox-container');
        const icon = byId('document-toggle-icon');
        const opening = !content.classList.contains('show');
        content.classList.toggle('show', opening);
        icon.classList.replace(opening ? 'fa-chevron-down' : 'fa-chevron-up', opening ? 'fa-chevron-up' : 'fa-chevron-down');
        if (opening && !busy) loadDocuments();
    };

    // Render Markdown with the old styles, allowing only safe content and links.
    function markdownFragment(text) {
        const fragment = document.createDocumentFragment();
        if (typeof window.marked?.parse !== 'function') {
            const plain = document.createElement('div');
            plain.style.whiteSpace = 'pre-wrap';
            plain.textContent = text;
            fragment.append(plain);
            return fragment;
        }
        const parsed = new DOMParser().parseFromString(window.marked.parse(String(text)), 'text/html');
        const allowed = new Set(['P', 'BR', 'STRONG', 'EM', 'DEL', 'S', 'UL', 'OL', 'LI', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'PRE', 'CODE', 'BLOCKQUOTE', 'TABLE', 'THEAD', 'TBODY', 'TR', 'TH', 'TD', 'HR', 'A', 'SPAN', 'DIV']);
        const blocked = new Set(['SCRIPT', 'STYLE', 'IFRAME', 'OBJECT', 'EMBED', 'SVG', 'MATH', 'FORM', 'INPUT', 'BUTTON', 'TEXTAREA']);
        function copy(node, parent) {
            if (node.nodeType === Node.TEXT_NODE) { parent.append(document.createTextNode(node.textContent)); return; }
            if (node.nodeType !== Node.ELEMENT_NODE || blocked.has(node.tagName)) return;
            let target = parent;
            if (allowed.has(node.tagName)) {
                target = document.createElement(node.tagName.toLowerCase());
                if (node.tagName === 'A') {
                    try {
                        const url = new URL(node.getAttribute('href') || '', location.origin);
                        if (['http:', 'https:', 'mailto:'].includes(url.protocol)) {
                            target.href = url.href;
                            target.target = '_blank';
                            target.rel = 'noopener noreferrer';
                        }
                    } catch (_) { /* Invalid links stay plain text. */ }
                }
                parent.append(target);
            }
            Array.from(node.childNodes).forEach(child => copy(child, target));
        }
        Array.from(parsed.body.childNodes).forEach(node => copy(node, fragment));
        return fragment;
    }

    function appendReferences(content, references) {
        if (!Array.isArray(references) || !references.length) return;
        const section = document.createElement('div');
        section.style.cssText = 'margin-top:15px;padding-top:10px;border-top:1px dashed #cbd5e1;font-size:13px';
        const heading = document.createElement('strong');
        heading.textContent = 'Tài liệu tham khảo:';
        section.append(heading);
        const list = document.createElement('ul');
        list.style.cssText = 'margin-top:8px;list-style-type:none';
        references.forEach(ref => {
            const item = document.createElement('li');
            const link = document.createElement('a');
            link.href = apiRoot + 'open_document?document_id=' + encodeURIComponent(ref.document_id);
            if (Number.isInteger(ref.page) && ref.page > 0) link.href += '#page=' + ref.page;
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
            const icon = document.createElement('i');
            icon.className = 'fa-solid fa-file-lines';
            link.append(icon, document.createTextNode(' ' + ref.title + (ref.page != null ? ' — trang ' + ref.page : '')));
            const evidence = document.createElement('blockquote');
            evidence.className = 'document-evidence';
            evidence.textContent = ref.excerpt;
            item.append(link, evidence);
            list.append(item);
        });
        section.append(list);
        content.append(section);
    }

    function scrollMessages() {
        const messages = byId('chat-messages');
        if (messages) messages.scrollTop = messages.scrollHeight;
    }

    function renderMessage(sender, text, references = [], animate = false) {
        const row = document.createElement('div');
        row.className = sender === 'user' ? 'msg msg-user' : 'msg msg-bot';
        const content = document.createElement('div');
        content.className = 'msg-content';
        if (sender === 'user') content.textContent = text;
        else {
            content.append(markdownFragment(text));
            appendReferences(content, references);
        }
        row.append(content);
        byId('chat-messages').append(row);
        if (!animate) { scrollMessages(); return Promise.resolve(); }
        const children = Array.from(content.childNodes);
        content.replaceChildren();
        return new Promise(resolve => {
            let index = 0;
            function showNext() {
                if (index === children.length) { scrollMessages(); resolve(); return; }
                const child = children[index++];
                if (child.nodeType === Node.ELEMENT_NODE) {
                    child.style.opacity = '0';
                    child.style.transition = 'opacity .5s ease-in';
                }
                content.append(child);
                if (child.nodeType === Node.ELEMENT_NODE) { void child.offsetWidth; child.style.opacity = '1'; }
                scrollMessages();
                setTimeout(showNext, 150);
            }
            showNext();
        });
    }

    async function loadHistory() {
        if (isHistoryLoaded) return;
        if (historyLoading) return historyLoading;
        historyLoading = (async () => {
            const messages = byId('chat-messages');
            try {
                const rows = await api('get_chat_history');
                messages.replaceChildren();
                renderMessage('bot', 'Xin chào! Tôi có thể giúp gì cho bạn hôm nay?');
                rows.reverse().forEach(row => renderMessage(row.role === 'user' ? 'user' : 'bot', row.message, row.references));
                isHistoryLoaded = true;
            } catch (error) { renderMessage('bot', error.message); }
            finally { historyLoading = null; }
        })();
        return historyLoading;
    }

    window.toggleChat = async function() {
        const panel = byId('lms-chat-window');
        if (!panel) return;
        const opening = panel.style.display !== 'flex';
        panel.style.display = opening ? 'flex' : 'none';
        if (opening) await Promise.all([loadHistory(), loadDocuments()]);
    };

    window.handleEnter = function(event) {
        if (event.key === 'Enter' && !event.isComposing) { event.preventDefault(); window.sendMessage(); }
    };

    window.sendMessage = async function() {
        const input = byId('chat-input');
        const question = input.value.trim();
        if (busy || !selected.size || !question) return;
        busy = true;
        updateControls();
        // Finish history rendering first so it cannot erase the new question.
        await loadHistory();
        renderMessage('user', question);
        input.value = '';
        const progress = byId('typing-indicator');
        progress.textContent = 'AI đang suy nghĩ...';
        progress.style.display = 'block';
        scrollMessages();
        try {
            const request = await api('ask_ai', {message: question, document_ids: [...selected], context_id: contextId});
            const started = Date.now();
            while (true) {
                await new Promise(resolve => setTimeout(resolve, 2000));
                const result = await api('get_answer?request_id=' + encodeURIComponent(request.request_id));
                if (result.status === 'Completed') {
                    progress.style.display = 'none';
                    await renderMessage('bot', result.reply, result.references, true);
                    break;
                }
                if (result.status === 'Failed') throw new Error(result.reply);
                progress.textContent = result.stage || 'AI đang suy nghĩ...';
                if (Date.now() - started > 7200000) throw new Error('Yêu cầu đã hết thời gian chờ. Hãy tải lại trang.');
            }
        } catch (error) { renderMessage('bot', error.message); }
        finally { progress.style.display = 'none'; busy = false; updateControls(); }
    };

    document.addEventListener('input', event => {
        if (event.target.id === 'chat-input') updateControls();
    });

    // ==========================================
    // 5. AUTO-CLOSE KHI CLICK RA NGOÀI
    // ==========================================
    document.addEventListener('click', function(event) {
        const chatWindow = document.getElementById('lms-chat-window');
        const chatBtn = document.getElementById('lms-chat-btn');
        const categoryContainer = document.getElementById('document-checkbox-container');
        const categoryToggleBtn = document.querySelector('.category-toggle-btn');
        const categoryIcon = document.getElementById('document-toggle-icon');

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
