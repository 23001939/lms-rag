<template>
	<Dialog v-model="show" :options="{ title: __('Tạo bài giảng bằng AI (AI Course Assistant)') }" class="max-w-2xl">
		<template #body>
			<div class="flex flex-col space-y-4 max-h-[70vh] overflow-y-auto p-1">
				<!-- Chat Messages -->
				<div class="flex flex-col space-y-3 min-h-[200px] bg-surface-gray-2 p-4 rounded-lg">
					<div v-if="messages.length === 0" class="text-center text-ink-gray-5 py-8">
						<span class="lucide-bot size-8 mx-auto mb-2 text-ink-gray-4 block" />
						<p>{{ __('Xin chào! Hãy nhập yêu cầu (prompt) và đính kèm tài liệu để AI tự động thiết kế và tạo bài giảng mới cho bạn.') }}</p>
					</div>
					<div
						v-for="(msg, index) in messages"
						:key="index"
						class="flex flex-col"
						:class="msg.role === 'user' ? 'items-end' : 'items-start'"
					>
						<div
							class="max-w-[85%] rounded-lg px-4 py-2.5 text-sm"
							:class="msg.role === 'user' ? 'bg-surface-dark text-white' : 'bg-surface-base border text-ink-gray-9 shadow-sm'"
						>
							<div class="font-semibold text-xs mb-1 opacity-70">
								{{ msg.role === 'user' ? __('Bạn') : __('Trợ lý AI') }}
							</div>
							<div class="whitespace-pre-wrap">{{ msg.content }}</div>
							<div v-if="msg.courseRoute" class="mt-3">
								<Button variant="solid" theme="green" @click="viewCourse(msg.courseRoute)">
									{{ __('Xem bài giảng đã tạo') }}
								</Button>
							</div>
						</div>
					</div>
					<div v-if="loading" class="flex items-center space-x-2 text-ink-gray-5 text-sm py-2">
						<span class="lucide-loader-circle size-4 animate-spin" />
						<span>{{ __('AI đang phân tích tài liệu và tạo bài giảng...') }}</span>
					</div>
				</div>

				<!-- Selected / Uploaded Document Indicator (Hỗ trợ nhiều file) -->
				<div v-if="selectedFiles.length > 0" class="flex flex-col space-y-2 bg-surface-gray-1 border px-3 py-2 rounded-md">
					<div class="text-xs font-semibold text-ink-gray-6 flex justify-between">
						<span>{{ __('Tài liệu đã chọn') }} ({{ selectedFiles.length }})</span>
						<span @click="clearAllFiles" class="cursor-pointer text-red-500 hover:underline">{{ __('Xóa tất cả') }}</span>
					</div>
					<div class="max-h-24 overflow-y-auto space-y-1">
						<div v-for="(file, index) in selectedFiles" :key="index" class="flex items-center justify-between bg-surface-base border px-2 py-1.5 rounded text-sm shadow-sm">
							<div class="flex items-center space-x-2 truncate">
								<span class="lucide-file-text size-4 text-ink-gray-6 shrink-0" />
								<span class="truncate font-medium text-xs">{{ file.name }}</span>
							</div>
							<Button variant="ghost" size="sm" @click="removeFile(index)" class="shrink-0 h-6 w-6 !p-0">
								<template #prefix>
									<span class="lucide-x size-3 text-ink-gray-5 hover:text-red-500" />
								</template>
							</Button>
						</div>
					</div>
				</div>

				<!-- Document Selector & Upload Controls -->
				<div class="flex flex-wrap items-center gap-2 pt-2 border-t">
					<div class="relative">
						<Button @click="showFilePicker = !showFilePicker" variant="outline">
							<template #prefix>
								<span class="lucide-paperclip size-4" />
							</template>
							{{ __('Chọn tài liệu có sẵn') }}
						</Button>
						<!-- Existing Files Dropdown -->
						<div v-if="showFilePicker" class="absolute bottom-full mb-2 left-0 w-80 bg-surface-base border rounded-lg shadow-xl z-50 p-2 max-h-60 overflow-y-auto">
							<div class="text-xs font-semibold text-ink-gray-5 px-2 py-1">{{ __('Tài liệu đã tải lên hệ thống') }}</div>
							<div v-if="userFiles.length === 0" class="text-xs text-ink-gray-5 p-2">{{ __('Chưa có tài liệu nào.') }}</div>
							<div
								v-for="file in userFiles"
								:key="file.name"
								@click="selectExistingFile(file)"
								class="px-3 py-2 hover:bg-surface-gray-2 rounded cursor-pointer text-xs truncate flex items-center justify-between"
							>
								<span class="truncate">{{ file.display_name }}</span>
								<span v-if="isFileSelected(file.file_url)" class="lucide-check size-3 text-green-500 shrink-0 ml-2" />
							</div>
						</div>
					</div>

					<div>
						<Button variant="outline" @click="triggerFileInput">
							<template #prefix>
								<span class="lucide-upload size-4" />
							</template>
							{{ __('Tải tài liệu mới lên') }}
						</Button>
						<!-- Đặt ref="fileInput" để gọi trực tiếp từ JS -->
						<input ref="fileInput" type="file" multiple class="hidden" @change="uploadNewFile" accept=".pdf,.docx,.txt,.md" />
					</div>
				</div>

				<!-- Prompt Input -->
				<div class="flex flex-col gap-2">
					<FormControl
						v-model="promptText"
						type="textarea"
						:placeholder="__('Nhập prompt: Ví dụ: Tạo một khóa học Python cơ bản từ các tài liệu này...')"
						class="w-full"
						@keydown.enter.prevent="sendPrompt"
					/>
					<div class="flex justify-end gap-2 pt-2 border-t">
						<Button variant="subtle" @click="show = false">
							{{ __('Hủy') }}
						</Button>
						<Button variant="solid" :loading="loading" @click="sendPrompt">
							<template #prefix>
								<span class="lucide-sparkles size-4" />
							</template>
							{{ __('Tạo bài giảng') }}
						</Button>
					</div>
				</div>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
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

// THÊM 2 ĐOẠN NÀY
const fileInput = ref(null)
const triggerFileInput = () => {
	if (fileInput.value) {
		fileInput.value.click()
	}
}
// Chuyển sang dùng mảng để lưu nhiều file
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
                file.display_name = name // Mặc định hiển thị tên gốc
                
                const dotIndex = name.lastIndexOf('.')
                const baseName = dotIndex !== -1 ? name.substring(0, dotIndex) : name
                const ext = dotIndex !== -1 ? name.substring(dotIndex).toLowerCase() : ''
                
                let isDuplicate = false
                
                for (let existing of uniqueFiles) {
                    const exName = existing.file_name || ''
                    const exDot = exName.lastIndexOf('.')
                    const exBase = exDot !== -1 ? exName.substring(0, exDot) : exName
                    const exExt = exDot !== -1 ? exName.substring(exDot).toLowerCase() : ''
                    
                    if (ext !== exExt) continue // Khác đuôi thì không phải trùng
                    if (baseName === exBase) {
                        isDuplicate = true; break;
                    }
                    
                    // TH1: File hiện tại là gốc (PSL), file đã lưu có hash (PSLa8a006)
                    // -> Update tên hiển thị của file đã lưu thành tên gốc cho đẹp!
                    if (exBase.startsWith(baseName) && exBase.length === baseName.length + 6) {
                        existing.display_name = name 
                        isDuplicate = true; break;
                    }
                    
                    // TH2: File hiện tại có hash (PSLa8a006), file đã lưu là gốc (PSL)
                    if (baseName.startsWith(exBase) && baseName.length === exBase.length + 6) {
                        isDuplicate = true; break;
                    }
                    
                    // TH3: Cả 2 đều có hash sinh ra từ cùng 1 gốc (PSLa8a006 và PSLb9c112)
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
	event.target.value = '' // Reset input
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
		// Chỉ gửi những tin nhắn quan trọng làm history
		const historyPayload = JSON.stringify(messages.value.slice(0, -1).map(m => ({
			role: m.role === 'user' ? 'user' : 'assistant',
			content: m.content
		})))
		
		// Map danh sách file thành mảng URL dạng string JSON
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
		// Cuộn xuống dòng tin nhắn cuối cùng
		setTimeout(() => {
			const chatContainer = document.querySelector('.max-h-\\[70vh\\]')
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