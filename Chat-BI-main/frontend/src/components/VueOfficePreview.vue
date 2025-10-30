<template>
  <div class="vue-office-preview">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <v-progress-circular indeterminate color="primary" />
      <div class="loading-text mt-2">正在加载文档...</div>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="error-container">
      <v-alert type="error" variant="tonal">
        <v-alert-title>加载失败</v-alert-title>
        {{ error }}
      </v-alert>
      <v-btn color="primary" class="mt-4" @click="loadDocument">
        <v-icon start>mdi-refresh</v-icon>
        重新加载
      </v-btn>
    </div>

    <!-- 文档预览 - 使用 vue-files-preview -->
    <div v-else-if="fileForPreview" class="document-container">
      <VueFilesPreview 
        :file="fileForPreview" 
        @success="onPreviewSuccess"
        @error="onPreviewError"
      />
    </div>

    <!-- 空状态 -->
    <div v-else class="empty-container">
      <v-alert type="info" variant="tonal">
        <v-alert-title>无文档内容</v-alert-title>
        未找到可预览的文档内容。
      </v-alert>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import VueFilesPreview from 'vue-files-preview'

// 定义Props
interface Props {
  dataset?: any
}

const props = defineProps<Props>()

// 定义Emits
interface Emits {
  (e: 'rendered'): void
  (e: 'error', error: string): void
  (e: 'download', datasetId: string): void
}

const emit = defineEmits<Emits>()

// 响应式数据
const loading = ref(false)
const error = ref<string | null>(null)
const fileForPreview = ref<File | null>(null)

// 计算属性
const apiBaseUrl = computed(() => {
  return import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
})

// 方法
const getDocumentType = (filename: string): string => {
  const ext = filename.toLowerCase().split('.').pop()
  switch (ext) {
    case 'docx':
    case 'doc':
      return 'docx'
    case 'xlsx':
    case 'xls':
      return 'excel'
    case 'pdf':
      return 'pdf'
    case 'pptx':
    case 'ppt':
      return 'pptx'
    default:
      return 'unsupported'
  }
}

// 加载文档
const loadDocument = async () => {
  if (!props.dataset) {
    error.value = '数据集信息不存在'
    return
  }

  loading.value = true
  error.value = null

  try {
    // 获取文档下载URL
    const downloadUrl = `${apiBaseUrl.value}/api/datasets/${props.dataset.id}/download-original`
    
    // 获取文件并转换为File对象
    const response = await fetch(downloadUrl)
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const blob = await response.blob()
    const fileName = props.dataset.name || 'document'
    const file = new File([blob], fileName, { type: blob.type })
    
    fileForPreview.value = file
    loading.value = false
    
  } catch (err) {
    console.error('加载文档失败:', err)
    error.value = '加载文档失败，请重试'
    loading.value = false
  }
}

// vue-files-preview 事件处理
const onPreviewSuccess = () => {
  console.log('文档预览成功')
  emit('rendered')
}

const onPreviewError = (err: any) => {
  console.error('文档预览错误:', err)
  error.value = '文档预览失败'
  emit('error', '文档预览失败')
}

const downloadDocument = () => {
  if (props.dataset?.id) {
    emit('download', props.dataset.id)
  }
}

// 监听数据集变化
watch(() => props.dataset, (newDataset) => {
  if (newDataset) {
    loadDocument()
  }
}, { immediate: true })

// 组件挂载时加载文档
onMounted(() => {
  if (props.dataset) {
    loadDocument()
  }
})
</script>

<style scoped>
.vue-office-preview {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
}

.loading-text {
  color: rgba(var(--v-theme-on-surface), 0.6);
  font-size: 0.875rem;
}

.error-container {
  padding: 2rem;
  text-align: center;
}

.document-container {
  flex: 1;
  width: 100%;
  overflow: hidden;
}

.unsupported-container {
  padding: 2rem;
  text-align: center;
}

.empty-container {
  padding: 2rem;
  text-align: center;
}

/* vue-office组件样式覆盖 */
:deep(.vue-office-docx) {
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  border-radius: 4px;
}

:deep(.vue-office-excel) {
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  border-radius: 4px;
}

:deep(.vue-office-pdf) {
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  border-radius: 4px;
}

:deep(.vue-office-pptx) {
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  border-radius: 4px;
}
</style>