<template>
    <Dialog v-model="show" :options="{ title: __('Tạo bài giảng bằng AI (AI Course Assistant)') }" class="max-w-2xl">
        <template #body>
            <div class="flex flex-col gap-4 max-h-[75vh] overflow-y-auto p-2 scroll-smooth">
                
                <!-- Chat Messages Area -->
                <div class="flex flex-col gap-3 min-h-[250px] bg-[#F4F8F8] p-5 rounded-xl border border-[#E0F2F1]">
                    
                    <!-- Empty State -->
                    <div v-if="messages.length === 0" class="flex flex-col items-center justify-center text-center py-10 h-full opacity-80">
                        <div class="bg-white p-4 rounded-full shadow-sm mb-4 border border-[#E0F2F1]">
                            <span class="lucide-bot size-10 text-[#005754] block" />
                        </div>
                        <h4 class="text-[#074942] font-semibold text-base mb-1">{{ __('Trợ lý AI tạo bài giảng') }}</h4>
                        <p class="text-[#183D3C] text-sm max-w-sm">
                            {{ __('Hãy nhập yêu cầu và đính kèm tài liệu, AI sẽ tự động phân tích và thiết kế bài giảng cho bạn.') }}
                        </p>
                    </div>

                    <!-- Chat Bubbles -->
                    <div
                        v-for="(msg, index) in messages"
                        :key="index"
                        class="flex flex-col w-full"
                        :class="msg.role === 'user' ? 'items-end' : 'items-start'"
                    >
                        <div
                            class="max-w-[85%] rounded-2xl px-4 py-3 text-[14px] leading-relaxed shadow-sm"
                            :class="msg.role === 'user' 
                                ? 'bg-[#005754] text-white rounded-tr-sm' 
                                : 'bg-white border border-[#E0F2F1] text-[#0B2827] rounded-tl-sm'"
                        >
                            <div class="font-semibold text-[11px] mb-1.5 uppercase tracking-wide opacity-80"
                                 :class="msg.role === 'user' ? 'text-[#E0F2F1]' : 'text-[#005754]'">
                                {{ msg.role === 'user' ? __('Bạn') : __('Trợ lý AI') }}
                            </div>
                            
                            <div class="whitespace-pre-wrap">{{ msg.content }}</div>
                            
                            <!-- Action Button from AI -->
                            <div v-if="msg.courseRoute" class="mt-4 border-t border-gray-100 pt-3">
                                <Button variant="solid" class="!bg-[#005754] hover:!bg-[#0a4542] !text-white border-none shadow-sm" @click="viewCourse(msg.courseRoute)">
                                    <template #prefix>
                                        <span class="lucide-external-link size-4" />
                                    </template>
                                    {{ __('Xem bài giảng đã tạo') }}
                                </Button>
                            </div>
                        </div>
                    </div>

                    <!-- Loading Indicator -->
                    <div v-if="loading" class="flex items-center gap-3 text-[#005754] text-sm py-2 px-1 animate-pulse">
                        <span class="lucide-loader-circle size-5 animate-spin" />
                        <span class="font-medium">{{ __('AI đang phân tích và soạn bài giảng...') }}</span>
                    </div>
                </div>

                <!-- Selected Documents Indicator -->
                <div v-if="selectedFiles.length > 0" class="flex flex-col gap-2 bg-white border border-[#E0F2F1] px-4 py-3 rounded-xl shadow-sm">
                    <div class="text-xs font-bold text-[#074942] flex justify-between items-center uppercase tracking-wide">
                        <div class="flex items-center gap-1.5">
                            <span class="lucide-layers size-4" />
                            <span>{{ __('Tài liệu đính kèm') }} ({{ selectedFiles.length }})</span>
                        </div>
                        <button @click="clearAllFiles" class="text-red-500 hover:text-red-700 transition-colors normal-case font-medium hover:underline">
                            {{ __('Xóa tất cả') }}
                        </button>
                    </div>
                    <div class="max-h-28 overflow-y-auto flex flex-col gap-1.5 pr-1 custom-scrollbar">
                        <div v-for="(file, index) in selectedFiles" :key="index" 
                             class="flex items-center justify-between bg-[#F4F8F8] border border-[#E0F2F1] px-3 py-2 rounded-lg group">
                            <div class="flex items-center gap-2 truncate">
                                <span class="lucide-file-text size-4 text-[#005754] shrink-0" />
                                <span class="truncate font-medium text-xs text-[#183D3C]">{{ file.name }}</span>
                            </div>
                            <button @click="removeFile(index)" class="shrink-0 text-gray-400 hover:text-red-500 transition-colors p-1">
                                <span class="lucide-x size-3.5 block" />
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Action Bar: Document Selector & Input -->
                <div class="flex flex-col gap-3 pt-3 border-t border-gray-100">
                    
                    <!-- File Upload Buttons -->
                    <div class="flex flex-wrap items-center gap-2 relative">
                        <Button @click="showFilePicker = !showFilePicker" variant="subtle" class="!text-[#005754] hover:!bg-[#E0F2F1] border border-transparent hover:border-[#E0F2F1]">
                            <template #prefix>
                                <span class="lucide-library size-4" />
                            </template>
                            {{ __('Chọn tài liệu hệ thống') }}
                        </Button>
                        
                        <!-- Dropdown Existing Files -->
                        <div v-if="showFilePicker" class="absolute bottom-full mb-2 left-0 w-80 bg-white border border-[#E0F2F1] rounded-xl shadow-xl z-50 p-2 max-h-60 overflow-y-auto custom-scrollbar">
                            <div class="text-[11px] font-bold text-[#005754] uppercase px-2 py-1.5">{{ __('Kho tài liệu của bạn') }}</div>
                            <div v-if="userFiles.length === 0" class="text-xs text-gray-500 p-2 italic">{{ __('Chưa có tài liệu nào.') }}</div>
                            <div
                                v-for="file in userFiles"
                                :key="file.name"
                                @click="selectExistingFile(file)"
                                class="px-3 py-2 hover:bg-[#F4F8F8] rounded-lg cursor-pointer text-xs truncate flex items-center justify-between group transition-colors"
                            >
                                <span class="truncate text-[#183D3C] group-hover:text-[#005754] font-medium">{{ file.display_name }}</span>
                                <span v-if="isFileSelected(file.file_url)" class="lucide-check-circle size-4 text-[#005754] shrink-0 ml-2" />
                            </div>
                        </div>

                        <Button variant="subtle" class="!text-[#005754] hover:!bg-[#E0F2F1]" @click="triggerFileInput">
                            <template #prefix>
                                <span class="lucide-upload-cloud size-4" />
                            </template>
                            {{ __('Tải lên từ máy') }}
                        </Button>
                        <input ref="fileInput" type="file" multiple class="hidden" @change="uploadNewFile" accept=".pdf,.docx,.txt,.md" />
                    </div>

                    <!-- Prompt Input Area -->
                    <div class="flex flex-col gap-3">
                        <FormControl
                            v-model="promptText"
                            type="textarea"
                            :placeholder="__('Nhập yêu cầu chi tiết. Ví dụ: Dựa vào tài liệu, hãy lên khung khóa học gồm 3 chương...')"
                            class="w-full !border-[#E0F2F1] focus-within:!border-[#005754] focus-within:!ring-1 focus-within:!ring-[#005754] rounded-xl"
                            :rows="3"
                            @keydown.enter.prevent="sendPrompt"
                        />
                        <div class="flex justify-end items-center gap-3 pt-1">
                            <Button variant="ghost" class="!text-gray-500 hover:!text-gray-800" @click="show = false">
                                {{ __('Đóng') }}
                            </Button>
                            
                            <!-- Nút nhấn chính -->
                            <Button variant="solid" :loading="loading" class="!bg-[#005754] hover:!bg-[#0a4542] !text-[#F2B814] border-none shadow-md px-5" @click="sendPrompt">
                                <template #prefix>
                                    <span class="lucide-sparkles size-4" />
                                </template>
                                <span class="font-semibold">{{ __('Tạo bài giảng') }}</span>
                            </Button>
                        </div>
                    </div>

                </div>
            </div>
        </template>
    </Dialog>
</template>

<script setup>
// Giữ nguyên phần script như cũ của bạn
import { Dialog, Button, FormControl, call, toast } from 'frappe-ui'
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
    modelValue: Boolean,
    courses: Object,
})
const emit = defineEmits(['update:modelValue', 'course-created'])

const show = computed({
    get: () => props.modelValue,
    set: (val) => emit('update:modelValue', val),
})

const router = useRouter()
const promptText = ref('')
const loading = ref(false)
const messages = ref([])
const userFiles = ref([])
const showFilePicker = ref(false)

const fileInput = ref(null)
const triggerFileInput = () => {
    if (fileInput.value) {
        fileInput.value.click()
    }
}
const selectedFiles = ref([])

onMounted(() => {
    fetchUserFiles()
})

const fetchUserFiles = async () => {
    try {
        const res = await call('lms.lms.ai_course.get_user_files')
        if (res) {
            const uniqueFiles = []
            
            res.forEach(file => {
                const name = file.file_name || ''
                file.display_name = name 
                
                const dotIndex = name.lastIndexOf('.')
                const baseName = dotIndex !== -1 ? name.substring(0, dotIndex) : name
                const ext = dotIndex !== -1 ? name.substring(dotIndex).toLowerCase() : ''
                
                let isDuplicate = false
                
                for (let existing of uniqueFiles) {
                    const exName = existing.file_name || ''
                    const exDot = exName.lastIndexOf('.')
                    const exBase = exDot !== -1 ? exName.substring(0, exDot) : exName
                    const exExt = exDot !== -1 ? exName.substring(exDot).toLowerCase() : ''
                    
                    if (ext !== exExt) continue 
                    if (baseName === exBase) {
                        isDuplicate = true; break;
                    }
                    
                    if (exBase.startsWith(baseName) && exBase.length === baseName.length + 6) {
                        existing.display_name = name 
                        isDuplicate = true; break;
                    }
                    
                    if (baseName.startsWith(exBase) && baseName.length === exBase.length + 6) {
                        isDuplicate = true; break;
                    }
                    
                    if (baseName.length > 6 && exBase.length > 6) {
                        const root1 = baseName.substring(0, baseName.length - 6)
                        const root2 = exBase.substring(0, exBase.length - 6)
                        if (root1 === root2 && root1.length > 0) {
                            isDuplicate = true; break;
                        }
                    }
                }

                if (!isDuplicate) {
                    uniqueFiles.push(file)
                }
            })
            
            userFiles.value = uniqueFiles
        }
    } catch (e) {
        console.error(e)
    }
}

const isFileSelected = (url) => {
    return selectedFiles.value.some(f => f.url === url)
}

const selectExistingFile = (file) => {
    if (!isFileSelected(file.file_url)) {
        selectedFiles.value.push({ url: file.file_url, name: file.file_name })
        toast.success(__('Đã thêm: ') + file.file_name)
    } else {
        toast.info(__('Tài liệu này đã được chọn!'))
    }
}

const uploadNewFile = async (event) => {
    const files = event.target.files
    if (!files || files.length === 0) return

    toast.info(`Đang tải lên ${files.length} tài liệu...`)

    for (let i = 0; i < files.length; i++) {
        const file = files[i]
        const formData = new FormData()
        formData.append('file', file, file.name)
        formData.append('is_private', 0)
        formData.append('folder', 'Home/Attachments')

        try {
            const response = await fetch('/api/method/upload_file', {
                method: 'POST',
                headers: {
                    'X-Frappe-CSRF-Token': window.csrf_token || (typeof frappe !== 'undefined' && frappe.csrf_token) || '',
                },
                body: formData,
            })
            const data = await response.json()
            if (data.message && data.message.file_url) {
                selectedFiles.value.push({
                    url: data.message.file_url,
                    name: data.message.file_name || file.name
                })
            }
        } catch (e) {
            console.error(e)
            toast.error(__('Lỗi khi tải lên file: ') + file.name)
        }
    }
    
    toast.success(__('Đã hoàn tất tải lên!'))
    fetchUserFiles()
    event.target.value = '' 
}

const removeFile = (index) => {
    selectedFiles.value.splice(index, 1)
}

const clearAllFiles = () => {
    selectedFiles.value = []
}

const sendPrompt = async () => {
    if (!promptText.value.trim() && selectedFiles.value.length === 0) return

    const userMsg = promptText.value.trim() || __('Tạo bài giảng từ các tài liệu đã chọn.')
    messages.value.push({ role: 'user', content: userMsg })
    const currentPrompt = userMsg
    promptText.value = ''
    loading.value = true

    try {
        const historyPayload = JSON.stringify(messages.value.slice(0, -1).map(m => ({
            role: m.role === 'user' ? 'user' : 'assistant',
            content: m.content
        })))
        
        const fileUrlsPayload = JSON.stringify(selectedFiles.value.map(f => f.url))

        const res = await call('lms.lms.ai_course.ai_chat_generate_course', {
            prompt: currentPrompt,
            file_urls: fileUrlsPayload,
            message_history: historyPayload,
        })

        if (res) {
            let replyText = res.reply || __('Đã xử lý yêu cầu.')
            let courseRoute = null
            
            if (res.status === 'success' && res.tool_result && res.tool_result.route) {
                courseRoute = res.tool_result.route
                if (props.courses && typeof props.courses.reload === 'function') {
                    props.courses.reload()
                }
                emit('course-created')
                toast.success(__('Tạo bài giảng thành công!'))
            } else if (res.status === 'error') {
                toast.error(__('AI gặp sự cố khi tạo khóa học.'))
            }

            messages.value.push({
                role: 'assistant',
                content: replyText,
                courseRoute: courseRoute,
            })
        }
    } catch (e) {
        console.error(e)
        const errorMsg = e.exc_type ? e.exc_type : (e.messages?.[0] || e.message || __('Lỗi không xác định'));
        messages.value.push({
            role: 'assistant',
            content: __('Có lỗi xảy ra: ') + errorMsg,
        })
    } finally {
        setTimeout(() => {
            const chatContainer = document.querySelector('.max-h-\\[75vh\\]')
            if(chatContainer) chatContainer.scrollTop = chatContainer.scrollHeight
        }, 100)
        loading.value = false
    }
}

const viewCourse = (routePath) => {
    emit('update:modelValue', false)
    router.push({ name: 'CourseDetail', params: { courseName: routePath.replace('courses/', '') } })
}
</script>

<style scoped>
/* Optional: Làm đẹp thanh cuộn cho khu vực hiển thị file và dropdown */
.custom-scrollbar::-webkit-scrollbar {
    width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
    background-color: #cbd5e1;
    border-radius: 10px;
}
</style>