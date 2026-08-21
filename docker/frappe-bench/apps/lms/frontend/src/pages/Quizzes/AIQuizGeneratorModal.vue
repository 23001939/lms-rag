<template>
    <Dialog v-model="show" :options="{ title: __('Tạo bài trắc nghiệm bằng AI') }">
        <template #body>
            <div class="px-5 pb-5 sm:px-6 sm:pb-6">
                
                <!-- PHẦN 1: FORM NHẬP LIỆU -->
                <div class="flex flex-col gap-4 max-h-[55vh] overflow-y-auto p-1 custom-scrollbar">
                    
                    <!-- Chọn Khóa học -->
                    <div class="flex flex-col gap-1.5">
                        <label class="text-[12px] font-bold text-[#074942] uppercase tracking-wide">
                            {{ __('Chọn Khóa học (Tùy chọn)') }}
                        </label>
                        <select v-model="selectedCourse" class="w-full text-sm rounded-xl border border-[#E0F2F1] p-2.5 bg-[#F4F8F8] text-[#183D3C] focus:outline-none focus:ring-1 focus:ring-[#005754] focus:border-[#005754] transition-colors">
                            <option :value="null">-- {{ __('Không chọn (Tạo tự do / Theo chủ đề bên dưới)') }} --</option>
                            <option v-for="c in coursesList" :key="c.name" :value="c.name">
                                {{ c.title }}
                            </option>
                        </select>
                    </div>

                    <FormControl
                        v-model="topic"
                        type="text"
                        :label="__('Chủ đề / Yêu cầu')"
                        :placeholder="__('Ví dụ: Giới thiệu lập trình Python, Lịch sử thế giới...')"
                        required
                        class="[&>label]:!text-[#074942] [&>label]:!font-bold [&>label]:!uppercase [&>label]:!text-[12px]"
                    />
                    
                    <div class="grid grid-cols-2 gap-4">
                        <FormControl
                            v-model="numberOfQuestions"
                            type="number"
                            :label="__('Số lượng câu hỏi')"
                            :min="1"
                            :max="20"
                            class="[&>label]:!text-[#074942] [&>label]:!font-bold [&>label]:!uppercase [&>label]:!text-[12px]"
                        />
                        <FormControl
                            v-model="difficulty"
                            type="select"
                            :label="__('Độ khó')"
                            :options="[
                                { label: __('Dễ'), value: 'Easy' },
                                { label: __('Trung bình'), value: 'Medium' },
                                { label: __('Khó'), value: 'Hard' },
                            ]"
                            class="[&>label]:!text-[#074942] [&>label]:!font-bold [&>label]:!uppercase [&>label]:!text-[12px]"
                        />
                    </div>

                    <FormControl
                        v-model="additionalInstructions"
                        type="textarea"
                        :label="__('Hướng dẫn bổ sung (Tùy chọn)')"
                        :placeholder="__('Ví dụ: Bao gồm các đoạn mã, tập trung vào chủ đề phụ...')"
                        class="[&>label]:!text-[#074942] [&>label]:!font-bold [&>label]:!uppercase [&>label]:!text-[12px]"
                    />
                </div>

                <!-- PHẦN 2: NÚT BẤM -->
                <div class="flex justify-end gap-3 pt-4 border-t border-gray-100 mt-5">
                    <Button variant="ghost" class="!text-gray-500 hover:!text-gray-800 font-medium" @click="show = false">
                        {{ __('Hủy') }}
                    </Button>
                    <Button
                        variant="solid"
                        :loading="loading"
                        :disabled="!topic"
                        class="!bg-[#005754] hover:!bg-[#0a4542] !text-[#F2B814] border-none shadow-md px-5"
                        @click="generateQuiz"
                    >
                        <template #prefix>
                            <span class="lucide-sparkles size-4" />
                        </template>
                        <span class="font-semibold">{{ __('Tạo Quiz') }}</span>
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

const emit = defineEmits(['update:modelValue', 'generated'])

const show = computed({
    get: () => props.modelValue,
    set: (val) => emit('update:modelValue', val),
})

const topic = ref('')
const numberOfQuestions = ref(5)
const difficulty = ref('Medium')
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

const generateQuiz = async () => {
    if (!topic.value) return
    loading.value = true

    try {
        let fullPrompt = `Tạo một bài trắc nghiệm (quiz) về chủ đề: "${topic.value}".\n`
        fullPrompt += `- Số lượng: ${numberOfQuestions.value} câu hỏi.\n`
        fullPrompt += `- Độ khó: ${difficulty.value}.\n`
        
        if (additionalInstructions.value) {
            fullPrompt += `- Hướng dẫn thêm: ${additionalInstructions.value}`
        }

        const res = await call('lms.lms.ai_course.ai_chat_generate_quiz', {
            prompt: fullPrompt,
            course_name: selectedCourse.value
        })

        if (res && res.status === 'success' && res.tool_result) {
            toast.success(__('Tạo Quiz bằng AI thành công!'))
            emit('generated', res.tool_result)
            show.value = false
        } else {
            toast.error(res?.reply || __('Không thể tạo Quiz lúc này'))
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