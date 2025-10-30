<template>
  <v-dialog v-model="dialog" max-width="600px" persistent>
    <v-card>
      <v-card-title class="d-flex justify-space-between align-center px-6 py-4">
        <span class="text-h6">上传数据集</span>
        <v-btn icon variant="text" size="small" @click="closeDialog">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>

      <v-divider></v-divider>

      <v-card-text class="px-6 py-6">
        <v-form ref="formRef" v-model="formValid">
          <!-- 文件上传区域 - 拖拽优化 -->
          <div
            class="file-upload-area"
            :class="{ 'drag-over': isDragOver }"
            @dragover.prevent="handleDragOver"
            @dragleave.prevent="handleDragLeave"
            @drop.prevent="handleDrop"
            @click="triggerFileInput"
          >
            <v-file-input
              ref="fileInputRef"
              v-model="selectedFile"
              accept=".csv,.xlsx,.xls,.et"
              prepend-icon=""
              :rules="fileRules"
              show-size
              class="file-input-hidden"
              @update:model-value="handleFileSelect"
            ></v-file-input>

            <div v-if="!selectedFile || selectedFile.length === 0" class="upload-placeholder">
              <v-icon size="48" color="primary" class="mb-3">mdi-cloud-upload</v-icon>
              <div class="text-h6 mb-2">拖拽文件到此处，或点击选择</div>
              <div class="text-caption text-medium-emphasis">
                支持 CSV、Excel (.xlsx, .xls, .et) 文件，最大 100MB
              </div>
            </div>

            <div v-else class="upload-file-info">
              <v-icon size="40" color="primary" class="mb-2">mdi-file-check</v-icon>
              <div class="text-body-1 font-weight-medium mb-1">{{ selectedFile[0].name }}</div>
              <div class="text-caption text-medium-emphasis">
                {{ formatFileSize(selectedFile[0].size) }}
              </div>
              <v-btn
                size="small"
                variant="text"
                color="error"
                class="mt-2"
                @click.stop="clearFile"
              >
                <v-icon start>mdi-close</v-icon>
                移除文件
              </v-btn>
            </div>
          </div>

          <!-- 数据集名称 -->
          <v-text-field
            v-model="logicalName"
            label="数据集名称"
            prepend-inner-icon="mdi-tag"
            :rules="nameRules"
            variant="outlined"
            density="comfortable"
            hint="为数据集起一个易于识别的名称"
            persistent-hint
            class="mt-6"
          ></v-text-field>

          <!-- 数据集描述 -->
          <v-textarea
            v-model="description"
            label="描述（可选）"
            prepend-inner-icon="mdi-text"
            variant="outlined"
            density="comfortable"
            rows="3"
            hint="简要描述数据集内容，帮助后续查询"
            persistent-hint
            class="mt-4"
          ></v-textarea>

          <!-- 上传进度 -->
          <v-progress-linear
            v-if="uploading"
            :model-value="uploadProgress"
            color="primary"
            height="24"
            rounded
            class="mt-6"
          >
            <template v-slot:default="{ value }">
              <strong class="text-white">{{ Math.ceil(value) }}%</strong>
            </template>
          </v-progress-linear>

          <!-- 解析状态 -->
          <v-alert
            v-if="parseStatus"
            :type="parseStatusType"
            :icon="parseStatusIcon"
            variant="tonal"
            class="mt-4"
          >
            <div>{{ parseStatusMessage }}</div>
            <v-progress-linear
              v-if="parseStatus === 'parsing' && parseProgress > 0"
              :model-value="parseProgress"
              color="primary"
              height="4"
              rounded
              class="mt-2"
            ></v-progress-linear>
          </v-alert>

          <!-- Embedding状态 -->
          <v-alert
            v-if="embeddingStatus && embeddingStatus !== 'pending'"
            :type="embeddingStatusType"
            :icon="embeddingStatusIcon"
            variant="tonal"
            class="mt-2"
          >
            <div>{{ embeddingStatusMessage }}</div>
            <v-progress-linear
              v-if="embeddingStatus === 'embedding' && embeddingProgress > 0"
              :model-value="embeddingProgress"
              color="secondary"
              height="4"
              rounded
              class="mt-2"
            ></v-progress-linear>
          </v-alert>
        </v-form>
      </v-card-text>

      <v-divider></v-divider>

      <v-card-actions class="px-6 py-4">
        <v-spacer></v-spacer>
        <v-btn
          v-if="parseStatus === 'parsed' && embeddingStatus === 'embedding'"
          variant="text"
          @click="closeDialogWithBackgroundTask"
          size="large"
        >
          <v-icon start>mdi-close</v-icon>
          后台处理
        </v-btn>
        <v-btn
          v-else
          variant="text"
          @click="closeDialog"
          :disabled="uploading && parseStatus !== 'parsed'"
          size="large"
        >
          {{ parseStatus === 'parsed' ? '关闭' : '取消' }}
        </v-btn>
        <v-btn
          v-if="!parseStatus"
          color="primary"
          variant="elevated"
          @click="handleUpload"
          :disabled="!formValid || uploading"
          :loading="uploading"
          size="large"
        >
          上传
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import axios from 'axios'

interface Props {
  modelValue: boolean
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'uploadSuccess', datasetId: string): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const dialog = computed({
  get: () => props.modelValue,
  set: (value: boolean) => emit('update:modelValue', value)
})

const formRef = ref()
const formValid = ref(false)
const selectedFile = ref<File[]>([])
const logicalName = ref('')
const description = ref('')
const uploading = ref(false)
const uploadProgress = ref(0)
const parseStatus = ref<'parsing' | 'parsed' | 'failed' | null>(null)
const parseProgress = ref(0)
const embeddingStatus = ref<'pending' | 'embedding' | 'completed' | 'failed' | null>(null)
const embeddingProgress = ref(0)
const embeddingError = ref<string | null>(null)
const datasetId = ref<string | null>(null)
const isDragOver = ref(false)
const fileInputRef = ref()

// 文件验证规则
const fileRules = [
  (v: File[]) => !!v && v.length > 0 || '请选择文件',
  (v: File[]) => {
    if (!v || v.length === 0) return true
    const file = v[0]
    const maxSize = 100 * 1024 * 1024 // 100MB
    return file.size <= maxSize || '文件大小不能超过 100MB'
  },
  (v: File[]) => {
    if (!v || v.length === 0) return true
    const file = v[0]
    const validExtensions = ['.csv', '.xlsx', '.xls', '.et']
    const fileName = file.name.toLowerCase()
    return validExtensions.some(ext => fileName.endsWith(ext)) || '仅支持 CSV 和 Excel (.xlsx, .xls, .et) 文件'
  }
]

// 名称验证规则
const nameRules = [
  (v: string) => !!v || '请输入数据集名称',
  (v: string) => (v && v.length >= 2) || '名称至少 2 个字符',
  (v: string) => (v && v.length <= 50) || '名称不能超过 50 个字符'
]

// 格式化文件大小
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

// 拖拽处理
const handleDragOver = () => {
  isDragOver.value = true
}

const handleDragLeave = () => {
  isDragOver.value = false
}

const handleDrop = (e: DragEvent) => {
  isDragOver.value = false
  const files = e.dataTransfer?.files
  if (files && files.length > 0) {
    selectedFile.value = [files[0]]
    handleFileSelect()
  }
}

const handleFileSelect = () => {
  if (selectedFile.value && selectedFile.value.length > 0 && !logicalName.value) {
    const fileName = selectedFile.value[0].name
    logicalName.value = fileName.replace(/\.(csv|xlsx|xls|et)$/i, '')
  }
}

const clearFile = () => {
  selectedFile.value = []
  logicalName.value = ''
}

const triggerFileInput = () => {
  const input = fileInputRef.value?.$el?.querySelector('input[type="file"]')
  if (input) {
    input.click()
  }
}

// 解析状态提示
const parseStatusType = computed(() => {
  switch (parseStatus.value) {
    case 'parsing':
      return 'info'
    case 'parsed':
      return 'success'
    case 'failed':
      return 'error'
    default:
      return 'info'
  }
})

const parseStatusIcon = computed(() => {
  switch (parseStatus.value) {
    case 'parsing':
      return 'mdi-loading mdi-spin'
    case 'parsed':
      return 'mdi-check-circle'
    case 'failed':
      return 'mdi-alert-circle'
    default:
      return 'mdi-information'
  }
})

const parseStatusMessage = computed(() => {
  switch (parseStatus.value) {
    case 'parsing':
      return '正在解析文件，请稍候...'
    case 'parsed':
      return '文件解析成功！'
    case 'failed':
      return '文件解析失败，请检查文件格式后重试。'
    default:
      return ''
  }
})

// Embedding状态样式
const embeddingStatusType = computed(() => {
  switch (embeddingStatus.value) {
    case 'embedding':
      return 'info'
    case 'completed':
      return 'success'
    case 'failed':
      return 'warning'
    default:
      return 'info'
  }
})

const embeddingStatusIcon = computed(() => {
  switch (embeddingStatus.value) {
    case 'embedding':
      return 'mdi-loading mdi-spin'
    case 'completed':
      return 'mdi-check-circle'
    case 'failed':
      return 'mdi-alert-circle'
    default:
      return 'mdi-information'
  }
})

const embeddingStatusMessage = computed(() => {
  switch (embeddingStatus.value) {
    case 'embedding':
      return '正在生成向量索引，这可能需要几分钟...'
    case 'completed':
      return '向量索引生成完成！数据集已可用于智能查询。'
    case 'failed':
      return `向量索引生成失败${embeddingError.value ? ': ' + embeddingError.value : ''}。数据集仍可用于基本查询。`
    default:
      return ''
  }
})

// 上传文件
const handleUpload = async () => {
  if (!selectedFile.value || selectedFile.value.length === 0) {
    return
  }

  uploading.value = true
  uploadProgress.value = 0
  parseStatus.value = null

  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value[0])
    formData.append('logical_name', logicalName.value)
    if (description.value) {
      formData.append('description', description.value)
    }

    const response = await axios.post(
      `${import.meta.env.VITE_API_BASE_URL}/api/upload_dataset`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            uploadProgress.value = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            )
          }
        }
      }
    )

    console.log('上传响应:', response.data)
    datasetId.value = response.data.dataset_id

    // 开始轮询解析状态
    parseStatus.value = 'parsing'
    pollParseStatus(response.data.dataset_id)

  } catch (error: any) {
    console.error('上传失败:', error)
    uploading.value = false

    // 处理重复文件错误
    if (error.response?.status === 409) {
      const errorDetail = error.response.data.detail
      if (errorDetail && errorDetail.error === 'duplicate_file') {
        parseStatus.value = 'failed'
        // 可以在这里显示更详细的重复文件信息
        alert(`${errorDetail.message}\n上传时间: ${new Date(errorDetail.existing_dataset.created_at).toLocaleString()}`)
      }
    } else {
      parseStatus.value = 'failed'
    }
  }
}

// 轮询解析状态
const pollParseStatus = async (id: string) => {
  const maxAttempts = 120  // 增加到120次,因为embedding可能需要更长时间
  let attempts = 0

  const checkStatus = async () => {
    try {
      const response = await axios.get(
        `${import.meta.env.VITE_API_BASE_URL}/api/dataset/${id}/status`
      )

      const status = response.data.parse_status
      parseProgress.value = response.data.parse_progress || 0

      // 更新embedding状态
      embeddingStatus.value = response.data.embedding_status
      embeddingProgress.value = response.data.embedding_progress || 0
      embeddingError.value = response.data.embedding_error

      if (status === 'parsed') {
        parseStatus.value = 'parsed'

        // 检查embedding是否也完成
        if (embeddingStatus.value === 'completed') {
          uploading.value = false
          emit('uploadSuccess', id)

          setTimeout(() => {
            closeDialog()
          }, 3000)
        } else if (embeddingStatus.value === 'failed') {
          // Embedding失败,但文件解析成功,仍然可以使用
          uploading.value = false
          emit('uploadSuccess', id)

          setTimeout(() => {
            closeDialog()
          }, 5000)
        } else {
          // 继续轮询等待embedding完成
          attempts++
          if (attempts < maxAttempts) {
            setTimeout(checkStatus, 2000)
          } else {
            uploading.value = false
            emit('uploadSuccess', id)
          }
        }
      } else if (status === 'failed') {
        parseStatus.value = 'failed'
        uploading.value = false
      } else if (status === 'parsing' || status === 'pending') {
        attempts++
        if (attempts < maxAttempts) {
          setTimeout(checkStatus, 2000)
        } else {
          parseStatus.value = 'failed'
          uploading.value = false
        }
      }
    } catch (error) {
      console.error('查询解析状态失败:', error)
      attempts++
      if (attempts < maxAttempts) {
        setTimeout(checkStatus, 2000)
      } else {
        parseStatus.value = 'failed'
        uploading.value = false
      }
    }
  }

  checkStatus()
}

// 关闭对话框
const closeDialog = () => {
  if (!uploading.value || parseStatus.value === 'parsed') {
    selectedFile.value = []
    logicalName.value = ''
    description.value = ''
    uploadProgress.value = 0
    parseStatus.value = null
    parseProgress.value = 0
    embeddingStatus.value = null
    embeddingProgress.value = 0
    embeddingError.value = null
    datasetId.value = null

    dialog.value = false
  }
}

// 关闭对话框并让embedding在后台继续
const closeDialogWithBackgroundTask = () => {
  // 通知用户embedding将在后台继续
  alert('向量索引将在后台继续生成\n\n您可以在"我的数据集"中查看进度')

  // 通知父组件刷新数据集列表
  if (datasetId.value) {
    emit('uploadSuccess', datasetId.value)
  }

  // 重置表单
  selectedFile.value = []
  logicalName.value = ''
  description.value = ''
  uploadProgress.value = 0
  parseStatus.value = null
  parseProgress.value = 0
  embeddingStatus.value = null
  embeddingProgress.value = 0
  embeddingError.value = null
  datasetId.value = null

  dialog.value = false
}

// 监听文件选择
watch(selectedFile, (newFile) => {
  if (newFile && newFile.length > 0 && !logicalName.value) {
    const fileName = newFile[0].name
    logicalName.value = fileName.replace(/\.(csv|xlsx|xls|et)$/i, '')
  }
})
</script>

<style scoped>
.file-upload-area {
  position: relative;
  border: 2px dashed rgba(var(--v-theme-on-surface), 0.2);
  border-radius: 12px;
  padding: 3rem 2rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background-color: transparent;
}

.file-upload-area:hover {
  border-color: rgb(var(--v-theme-primary));
  background-color: rgba(var(--v-theme-primary), 0.03);
}

.file-upload-area.drag-over {
  border-color: rgb(var(--v-theme-primary));
  border-width: 2px;
  background-color: rgba(var(--v-theme-primary), 0.08);
  transform: scale(1.01);
}

.file-input-hidden {
  position: absolute;
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
  opacity: 0;
  cursor: pointer;
}

.upload-placeholder {
  pointer-events: none;
}

.upload-file-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  pointer-events: none;
}

.upload-file-info .v-btn {
  pointer-events: auto;
}

:deep(.v-field--variant-outlined) {
  border-radius: 8px;
}
</style>
