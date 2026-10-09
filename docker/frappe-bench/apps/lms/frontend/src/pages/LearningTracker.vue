<template>
  <div class="p-6 space-y-6 max-w-5xl mx-auto">
    <!-- Header -->
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold text-ink-gray-9">{{ __('Learning Hours Tracker') }}</h1>
      <Button @click="saveData" :loading="saving">{{ __('Save Changes') }}</Button>
    </div>

    <!-- Summary & Target Card -->
    <div class="bg-surface-base p-6 rounded-lg shadow-sm border space-y-4">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div>
          <label class="text-sm text-ink-gray-6 font-medium">{{ __('Total Hours Studied') }}</label>
          <div class="text-3xl font-bold text-ink-gray-9 mt-1">{{ totalHours }} hrs</div>
        </div>
        <div>
          <label class="text-sm text-ink-gray-6 font-medium">{{ __('Target Hours per Year') }}</label>
          <input
            type="number"
            v-model.number="tracker.target_hours"
            class="mt-1 w-full border rounded px-3 py-2 text-sm bg-surface-white focus:outline-none focus:ring-1 focus:ring-primary-500"
          />
        </div>
        <div>
          <label class="text-sm text-ink-gray-6 font-medium">{{ __('Progress') }}</label>
          <div class="text-3xl font-bold text-primary-600 mt-1">{{ progressPercent }}%</div>
        </div>
      </div>
      <div class="w-full bg-surface-gray-2 h-3 rounded-full overflow-hidden">
        <div
          class="bg-primary-500 h-full transition-all duration-300"
          :style="{ width: Math.min(progressPercent, 100) + '%' }"
        />
      </div>
    </div>

    <!-- Completed LMS Courses -->
    <div class="bg-surface-base p-6 rounded-lg shadow-sm border space-y-4">
      <h2 class="text-lg font-semibold text-ink-gray-9">{{ __('Completed LMS Courses') }}</h2>
      <div class="border rounded-lg overflow-hidden">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="bg-surface-gray-2 text-xs uppercase text-ink-gray-6">
              <th class="p-3">{{ __('Course Name') }}</th>
              <th class="p-3">{{ __('Hours') }}</th>
              <th class="p-3">{{ __('Source') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(course, idx) in completedLMSCourses" :key="idx" class="border-t">
              <td class="p-3">{{ course.course_name }}</td>
              <td class="p-3">{{ course.hours }} hrs</td>
              <td class="p-3">
                <span class="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">LMS</span>
              </td>
            </tr>
            <tr v-if="completedLMSCourses.length === 0">
              <td colspan="3" class="p-4 text-center text-ink-gray-5">
                {{ __('No completed LMS courses yet.') }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- External Courses & Proofs -->
    <div class="bg-surface-base p-6 rounded-lg shadow-sm border space-y-4">
      <div class="flex justify-between items-center">
        <h2 class="text-lg font-semibold text-ink-gray-9">{{ __('External Courses & Proofs') }}</h2>
        <Button @click="addExternalCourse">{{ __('Add External Course') }}</Button>
      </div>

      <div class="border rounded-lg overflow-x-auto">
        <table class="w-full text-left border-collapse table-fixed min-w-[760px]">
          <thead>
            <tr class="bg-surface-gray-2 text-xs uppercase text-ink-gray-6 font-semibold">
              <th class="p-3 w-[30%]">{{ __('Tên khóa học') }}</th>
              <th class="p-3 w-[12%]">{{ __('Hours') }}</th>
              <th class="p-3 w-[18%]">{{ __('Completion Date') }}</th>
              <th class="p-3 w-[26%]">{{ __('Proof Files') }}</th>
              <th class="p-3 w-[14%] text-center">{{ __('Hành động') }}</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr
              v-for="(course, idx) in tracker.external_courses"
              :key="idx"
              class="hover:bg-surface-gray-1 transition-colors"
            >
              <!-- Tên khóa học -->
              <td class="p-3 align-middle">
                <input
                  type="text"
                  v-model="course.course_name"
                  class="w-full border rounded-md px-3 py-1.5 text-sm bg-surface-white focus:outline-none focus:ring-1 focus:ring-primary-500"
                  placeholder="Nhập tên khóa học"
                />
              </td>

              <!-- Số giờ -->
              <td class="p-3 align-middle">
                <div class="relative flex items-center">
                  <input
                    type="number"
                    min="0"
                    step="0.5"
                    v-model.number="course.hours"
                    class="w-full border rounded-md pl-2.5 pr-6 py-1.5 text-sm bg-surface-white focus:outline-none focus:ring-1 focus:ring-primary-500"
                    placeholder="0"
                  />
                  <span class="absolute right-2 text-xs text-ink-gray-5 pointer-events-none">h</span>
                </div>
              </td>

              <!-- Ngày hoàn thành -->
              <td class="p-3 align-middle">
                <input
                  type="date"
                  v-model="course.completion_date"
                  class="w-full border rounded-md px-2.5 py-1.5 text-sm bg-surface-white focus:outline-none focus:ring-1 focus:ring-primary-500"
                />
              </td>

              <!-- File minh chứng -->
              <td class="p-3 align-middle">
                <div class="flex flex-col gap-1.5">
                  <div>
                    <label class="inline-flex items-center gap-1 px-2.5 py-1 border border-dashed border-gray-300 hover:border-primary-500 rounded text-xs text-ink-gray-7 cursor-pointer bg-surface-white transition-colors">
                      <span class="text-sm font-bold leading-none text-ink-gray-5">+</span>
                      <span>{{ __('Upload files') }}</span>
                      <input
                        type="file"
                        multiple
                        @change="(e) => uploadFiles(e, course)"
                        class="hidden"
                      />
                    </label>
                  </div>

                  <!-- Danh sách các link View Proof -->
                  <div v-if="course.proof_files && course.proof_files.length" class="flex flex-wrap gap-1">
                    <span
                      v-for="(fileUrl, fIdx) in course.proof_files"
                      :key="fIdx"
                      class="inline-flex items-center gap-1.5 bg-gray-100 hover:bg-gray-200 text-ink-gray-8 px-2 py-0.5 rounded text-xs border transition-colors"
                    >
                      <a
                        :href="fileUrl"
                        target="_blank"
                        class="text-primary-600 font-medium hover:underline flex items-center gap-1"
                      >
                        <span>👁️</span> {{ __('View') }} {{ course.proof_files.length > 1 ? (fIdx + 1) : '' }}
                      </a>
                      <button
                        type="button"
                        @click="removeFile(course, fIdx)"
                        class="text-gray-400 hover:text-red-500 font-bold ml-1 text-sm leading-none"
                        title="Xóa file này"
                      >
                        &times;
                      </button>
                    </span>
                  </div>
                </div>
              </td>

              <!-- Nút xóa dòng -->
              <td class="p-3 align-middle text-center">
                <button
                  type="button"
                  @click="removeExternalCourse(idx)"
                  class="px-2.5 py-1 text-xs font-medium text-red-600 hover:text-red-800 hover:bg-red-50 rounded transition-colors whitespace-nowrap"
                >
                  {{ __('Xóa') }}
                </button>
              </td>
            </tr>

            <tr v-if="!tracker.external_courses || tracker.external_courses.length === 0">
              <td colspan="5" class="p-6 text-center text-ink-gray-5 text-sm">
                {{ __('No external courses added yet.') }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { call, Button, toast } from 'frappe-ui'

const MAX_FILE_SIZE = 10 * 1024 * 1024 // 10MB

const tracker = ref({
  target_hours: 100,
  year: new Date().getFullYear(),
  external_courses: []
})
const completedLMSCourses = ref([])
const saving = ref(false)

onMounted(() => {
  fetchData()
})

const fetchData = () => {
  call('lms.lms.doctype.learning_tracker.learning_tracker_api.get_user_learning_data').then((res) => {
    if (res) {
      if (res.tracker?.external_courses) {
        res.tracker.external_courses.forEach((item) => {
          // Chuẩn hóa: Nếu proof_file trả về từ DB là string ngăn cách dấu phẩy, split ra mảng
          if (typeof item.proof_file === 'string' && item.proof_file.trim() !== '') {
            item.proof_files = item.proof_file.split(',').map((s) => s.trim()).filter(Boolean)
          } else if (Array.isArray(item.proof_files)) {
            // Giữ nguyên nếu đã là mảng
          } else {
            item.proof_files = []
          }
        })
      }
      tracker.value = res.tracker
      completedLMSCourses.value = res.completed_lms_courses || []
    }
  })
}

const totalHours = computed(() => {
  const lmsTotal = completedLMSCourses.value.reduce((sum, c) => sum + (Number(c.hours) || 0), 0)
  const extTotal = (tracker.value.external_courses || []).reduce((sum, c) => sum + (Number(c.hours) || 0), 0)
  return lmsTotal + extTotal
})

const progressPercent = computed(() => {
  if (!tracker.value.target_hours || tracker.value.target_hours <= 0) return 0
  return Math.round((totalHours.value / tracker.value.target_hours) * 100)
})

const addExternalCourse = () => {
  if (!tracker.value.external_courses) {
    tracker.value.external_courses = []
  }
  tracker.value.external_courses.push({
    course_name: '',
    hours: 0,
    completion_date: '',
    proof_file: '',
    proof_files: []
  })
}

const removeExternalCourse = (idx) => {
  tracker.value.external_courses.splice(idx, 1)
}

const removeFile = (course, fIdx) => {
  course.proof_files.splice(fIdx, 1)
  course.proof_file = course.proof_files.join(',')
}

const uploadFiles = async (e, course) => {
  const files = Array.from(e.target.files || [])
  if (!files.length) return

  if (!Array.isArray(course.proof_files)) {
    course.proof_files = []
  }

  // 1. Kiểm tra kích thước từng file < 10MB
  const oversizedFiles = files.filter((f) => f.size >= MAX_FILE_SIZE)
  if (oversizedFiles.length > 0) {
    toast.error(`File vượt quá 10MB: ${oversizedFiles.map((f) => f.name).join(', ')}`)
    e.target.value = ''
    return
  }

  // 2. Upload file
  for (const file of files) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('is_private', 0)

    try {
      const res = await fetch('/api/method/upload_file', {
        method: 'POST',
        body: formData,
        headers: {
          'X-Frappe-CSRF-Token': window.csrf_token
        }
      })
      const data = await res.json()
      if (data.message && data.message.file_url) {
        course.proof_files.push(data.message.file_url)
      } else {
        toast.error(`Không thể tải lên file: ${file.name}`)
      }
    } catch {
      toast.error(`Lỗi kết nối khi tải file: ${file.name}`)
    }
  }

  // Đồng bộ lại string proof_file sau khi upload
  course.proof_file = course.proof_files.join(',')
  toast.success('Đã tải lên file minh chứng')
  e.target.value = ''
}

const saveData = () => {
  saving.value = true

  // Clone payload và đồng bộ mảng proof_files về chuỗi proof_file cho Frappe DocType
  const payloadDoc = JSON.parse(JSON.stringify(tracker.value))
  if (payloadDoc.external_courses) {
    payloadDoc.external_courses.forEach((course) => {
      if (Array.isArray(course.proof_files)) {
        course.proof_file = course.proof_files.join(',')
      }
    })
  }

  call('lms.lms.doctype.learning_tracker.learning_tracker_api.save_learning_tracker', {
    doc: payloadDoc
  })
    .then(() => {
      saving.value = false
      toast.success('Learning tracker saved successfully')
    })
    .catch(() => {
      saving.value = false
      toast.error('Failed to save learning tracker')
    })
}
</script>