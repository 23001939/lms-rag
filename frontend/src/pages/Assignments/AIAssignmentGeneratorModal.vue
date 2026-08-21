<template>
    <Dialog v-model="show" :options="{ title: __('Tạo bài tập bằng AI') }">
        <template #body>
            <div class="px-5 pb-5 sm:px-6 sm:pb-6">
                
                <!-- 1. PHẦN FORM NHẬP LIỆU -->
                <div class="flex flex-col gap-4 max-h-[55vh] overflow-y-auto p-1 custom-scrollbar">
                    
                    <!-- Dropdown chọn Khóa học -->
                    <div class="flex flex-col gap-1.5">
                        <label class="text-[12px] font-bold text-[#074942] uppercase tracking-wide">
                            {{ __('Chọn Khóa học (Tùy chọn)') }}
                        </label>
                        <select v-model="selectedCourse" class="w-full text-sm rounded-xl border border-[#E0F2F1] p-2.5 bg-[#F4F8F8] text-[#183D3C] focus:outline-none focus:ring-1 focus:ring-[#005754] focus:border-[#005754] transition-colors">
                            <option :value="null">-- {{ __('Không chọn (Tạo tự do)') }} --</option>
                            <option v-for="c in coursesList" :key="c.name" :value="c.name">
                                {{ c.title }}
                            </option>
                        </select>
                    </div>

                    <FormControl 
                        v-model="topic" 
                        type="text" 
                        :label="__('Chủ đề / Yêu cầu')" 
                        required 
                        class="[&>label]:!text-[#074942] [&>label]:!font-bold [&>label]:!uppercase [&>label]:!text-[12px]"
                    />
                    
                    <div class="grid grid-cols-2 gap-4">
                        <FormControl 
                            v-model="numberOfQuestions" 
                            type="number" 
                            :label="__('Số lượng (Yêu cầu con)')" 
                            :min="1" 
                            :max="20" 
                            class="[&>label]:!text-[#074942] [&>label]:!font-bold [&>label]:!uppercase [&>label]:!text-[12px]"
                        />
                        <FormControl 
                            v-model="difficulty" 
                            type="select" 
                            :label="__('Độ khó')" 
                            :options="[
                                { label: 'Dễ', value: 'Easy' }, 
                                { label: 'Trung bình', value: 'Medium' }, 
                                { label: 'Khó', value: 'Hard' }
                            ]" 
                            class="[&>label]:!text-[#074942] [&>label]:!font-bold [&>label]:!uppercase [&>label]:!text-[12px]"
                        />
                    </div>

                    <FormControl 
                        v-model="assignmentType" 
                        type="select" 
                        :label="__('Hình thức nộp bài')" 
                        :options="[
                            { label: 'Text (Nhập văn bản)', value: 'Text' }, 
                            { label: 'Document (Tài liệu)', value: 'Document' }, 
                            { label: 'PDF', value: 'PDF' }, 
                            { label: 'Image (Hình ảnh)', value: 'Image' }, 
                            { label: 'URL (Đường dẫn)', value: 'URL' }
                        ]" 
                        class="[&>label]:!text-[#074942] [&>label]:!font-bold [&>label]:!uppercase [&>label]:!text-[12px]"
                    />

                    <FormControl 
                        v-model="additionalInstructions" 
                        type="textarea" 
                        :label="__('Hướng dẫn bổ sung (Tùy chọn)')" 
                        class="[&>label]:!text-[#074942] [&>label]:!font-bold [&>label]:!uppercase [&>label]:!text-[12px]"
                    />
                </div>

                <!-- 2. PHẦN NÚT BẤM -->
                <div class="flex justify-end gap-3 pt-4 border-t border-gray-100 mt-5">
                    <Button variant="ghost" class="!text-gray-500 hover:!text-gray-800 font-medium" @click="show = false">
                        {{ __('Hủy') }}
                    </Button>
                    <Button
                        variant="solid"
                        :loading="loading"
                        :disabled="!topic"
                        class="!bg-[#005754] hover:!bg-[#0a4542] !text-[#F2B814] border-none shadow-md px-5"
                        @click="generateAssignment"
                    >
                        <template #prefix>
                            <span class="lucide-sparkles size-4" />
                        </template>
                        <span class="font-semibold">{{ __('Tạo Bài tập') }}</span>
                    </Button>
                </div>

            </div>
        </template>
    </Dialog>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Dialog, FormControl, Button, toast, call } from 'frappe-ui'

const props = defineProps({
    modelValue: {
        type: Boolean,
        default: false,
    },
})

const emit = defineEmits(['update:modelValue', 'assignment-created'])

const show = computed({
    get: () => props.modelValue,
    set: (val) => emit('update:modelValue', val),
})

const topic = ref('')
const numberOfQuestions = ref(5)
const difficulty = ref('Medium')
const assignmentType = ref('Text')
const additionalInstructions = ref('')
const loading = ref(false)

const selectedCourse = ref(null)
const coursesList = ref([])

onMounted(() => {
    fetchCourses()
})

const fetchCourses = async () => {
    try {
        const res = await call('lms.lms.ai_course.get_courses_list')
        if (res) coursesList.value = res
    } catch (e) {
        console.error(e)
    }
}

const generateAssignment = async () => {
    if (!topic.value) return
    loading.value = true

    try {
        let fullPrompt = `Tạo một bài tập (assignment) về chủ đề: "${topic.value}".\n`
        fullPrompt += `- Bao gồm: ${numberOfQuestions.value} yêu cầu hoặc câu hỏi nhỏ bên trong bài tập.\n`
        fullPrompt += `- Mức độ khó: ${difficulty.value}.\n`
        fullPrompt += `- Hình thức học viên nộp bài dự kiến: ${assignmentType.value}.\n`
        
        if (additionalInstructions.value) {
            fullPrompt += `- Hướng dẫn/Yêu cầu chi tiết thêm: ${additionalInstructions.value}`
        }

        const res = await call('lms.lms.ai_course.ai_chat_generate_assignment', {
            prompt: fullPrompt,
            course_name: selectedCourse.value
        })

        if (res && res.status === 'success' && res.tool_result) {
            toast.success(__('Tạo bài tập bằng AI thành công!'))
            emit('assignment-created', res.tool_result)
            show.value = false
        } else {
            toast.error(res?.reply || __('Không thể tạo bài tập lúc này'))
        }

    } catch (error) {
        console.error(error)
        const errorMsg = error.exc_type ? error.exc_type : (error.messages?.[0] || error.message || __('Lỗi khi kết nối với AI'));
        toast.error(errorMsg)
    } finally {
        loading.value = false
    }
}
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 6px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background-color: #cbd5e1; border-radius: 10px; }
</style>