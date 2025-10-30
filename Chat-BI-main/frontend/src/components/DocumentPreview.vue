<template>
  <div class="document-preview">
    <!-- 文档信息头部 -->
    <v-card class="document-header mb-4" variant="outlined">
      <v-card-text>
        <div class="d-flex align-center justify-space-between flex-wrap">
          <div class="document-info">
            <h3 class="document-title text-h6 mb-2">{{ documentInfo?.dataset_name || '文档预览' }}</h3>
            <div class="document-meta d-flex flex-wrap gap-2" v-if="documentInfo?.file_info">
              <v-chip size="small" color="success" variant="tonal">
                {{ getFileTypeLabel(documentInfo.file_info.document_type) }}
              </v-chip>
              <v-chip size="small" color="info" variant="tonal" v-if="documentInfo.file_info.file_size">
                {{ formatFileSize(documentInfo.file_info.file_size) }}
              </v-chip>
              <v-chip size="small" variant="tonal">
                {{ documentInfo.file_info.extension }}
              </v-chip>
            </div>
          </div>
          
          <div class="d-flex align-center gap-3">
            <!-- 预览方法选择器 -->
            <div class="preview-controls" v-if="documentInfo?.file_info?.preview_methods?.length > 1">
              <v-select
                v-model="selectedMethod"
                @update:model-value="changePreviewMethod"
                :items="methodOptions"
                item-title="label"
                item-value="value"
                density="compact"
                variant="outlined"
                style="width: 150px"
                hide-details
              />
            </div>
            
            <!-- 操作按钮 -->
            <div class="document-actions d-flex gap-2">
              <v-btn
                color="primary"
                size="small"
                @click="downloadDocument"
                :loading="downloading"
                prepend-icon="mdi-download"
              >
                下载
              </v-btn>
              <v-btn
                size="small"
                @click="refreshPreview"
                :loading="loading"
                prepend-icon="mdi-refresh"
              >
                刷新
              </v-btn>
            </div>
          </div>
        </div>
      </v-card-text>
    </v-card>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="8" animated />
      <div class="loading-text">正在加载文档预览...</div>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="error-container">
      <el-result
        icon="error"
        :title="error.title || '预览失败'"
        :sub-title="error.message"
      >
        <template #extra>
          <el-button type="primary" @click="refreshPreview">重试</el-button>
          <el-button @click="downloadDocument">下载文件</el-button>
        </template>
      </el-result>
    </div>

    <!-- 预览内容 -->
    <div v-else-if="previewData" class="preview-content">
      <!-- 表格预览 -->
      <div v-if="previewData.content_type === 'table'" class="table-preview">
        <div class="table-info">
          <span>共 {{ previewData.total_rows }} 行，{{ previewData.total_columns }} 列</span>
          <span v-if="previewData.message" class="preview-message">{{ previewData.message }}</span>
        </div>
        <el-table 
          :data="previewData.data" 
          stripe 
          border
          height="500"
          style="width: 100%"
        >
          <el-table-column
            v-for="column in previewData.columns"
            :key="column"
            :prop="column"
            :label="column"
            :width="getColumnWidth(column)"
            show-overflow-tooltip
          />
        </el-table>
      </div>

      <!-- HTML预览 -->
      <div v-else-if="previewData.content_type === 'html'" class="html-preview">
        <div class="preview-message" v-if="previewData.message">{{ previewData.message }}</div>
        <div v-html="previewData.html_content" class="html-content"></div>
      </div>

      <!-- PDF预览 -->
      <div v-else-if="previewData.content_type === 'pdf'" class="pdf-preview">
        <div class="pdf-controls">
          <span class="preview-message">{{ previewData.message }}</span>
          <div class="pdf-page-controls">
            <el-button-group>
              <el-button size="small" @click="previousPage" :disabled="currentPage <= 1">
                <el-icon><ArrowLeft /></el-icon>
                上一页
              </el-button>
              <el-button size="small" @click="nextPage">
                下一页
                <el-icon><ArrowRight /></el-icon>
              </el-button>
            </el-button-group>
            <span class="page-info">第 {{ currentPage }} 页</span>
          </div>
        </div>
        <div class="pdf-container">
          <iframe 
            :src="getPdfDataUrl(previewData.pdf_data)"
            width="100%"
            height="600px"
            frameborder="0"
          ></iframe>
        </div>
      </div>

      <!-- 文本预览 -->
      <div v-else-if="previewData.content_type === 'text'" class="text-preview">
        <div class="text-info">
          <span class="preview-message">{{ previewData.message }}</span>
          <span v-if="previewData.encoding" class="encoding-info">编码: {{ previewData.encoding }}</span>
          <span v-if="previewData.truncated" class="truncated-warning">内容已截断</span>
        </div>
        <pre class="text-content">{{ previewData.text_content }}</pre>
      </div>

      <!-- 代码预览 -->
      <div v-else-if="previewData.content_type === 'code'" class="code-preview">
        <div class="code-info">
          <span class="preview-message">{{ previewData.message }}</span>
          <span class="language-info">语言: {{ previewData.language }}</span>
          <span v-if="previewData.truncated" class="truncated-warning">内容已截断</span>
        </div>
        <pre class="code-content"><code :class="`language-${previewData.language}`">{{ previewData.text_content }}</code></pre>
      </div>

      <!-- 图片预览 -->
      <div v-else-if="previewData.content_type === 'image'" class="image-preview">
        <div class="image-info">
          <span class="preview-message">{{ previewData.message }}</span>
        </div>
        <div class="image-container">
          <img 
            :src="getImageDataUrl(previewData.image_data, previewData.mime_type)"
            alt="图片预览"
            class="preview-image"
          />
        </div>
      </div>

      <!-- 消息预览（用于不支持的格式） -->
      <div v-else-if="previewData.content_type === 'message'" class="message-preview">
        <el-result
          icon="info"
          :title="previewData.message"
          :sub-title="previewData.suggestion"
        >
          <template #extra>
            <el-button type="primary" @click="downloadDocument">下载文件</el-button>
          </template>
        </el-result>
      </div>

      <!-- 未知内容类型 -->
      <div v-else class="unknown-preview">
        <el-result
          icon="warning"
          title="未知的预览格式"
          sub-title="无法识别的预览内容类型"
        >
          <template #extra>
            <el-button type="primary" @click="downloadDocument">下载文件</el-button>
          </template>
        </el-result>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="empty-container">
      <el-empty description="暂无预览内容" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import axios from 'axios'

// 定义props
interface Props {
  dataset?: any
}

const props = defineProps<Props>()

// 响应式数据
const loading = ref(false)
const downloading = ref(false)
const error = ref<{ title?: string; message: string } | null>(null)
const documentInfo = ref<any>(null)
const previewData = ref<any>(null)
const selectedMethod = ref<string>('')
const currentPage = ref(1)
const totalPages = ref(1)
const selectedMethodIndex = ref(0)

// 计算属性
const availableMethods = computed(() => {
  if (!documentInfo.value?.file_info?.preview_methods) return []
  
  return documentInfo.value.file_info.preview_methods.map((method: string) => ({
    value: method,
    label: getMethodLabel(method)
  }))
})

const methodOptions = computed(() => {
  return availableMethods.value
})

const tableHeaders = computed(() => {
  if (!previewData.value?.columns) return []
  
  return previewData.value.columns.map((column: string) => ({
    title: column,
    key: column,
    sortable: false
  }))
})

const apiBaseUrl = computed(() => {
  return import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
})

// 方法
const getMethodLabel = (method: string): string => {
  const labels: Record<string, string> = {
    'table_view': '表格视图',
    'html_preview': 'HTML预览',
    'pdf_viewer': 'PDF查看器',
    'text_view': '文本视图',
    'syntax_highlight': '代码高亮',
    'image_view': '图片预览'
  }
  return labels[method] || method
}

const getFileTypeLabel = (type: string): string => {
  const labels: Record<string, string> = {
    'spreadsheet': '电子表格',
    'pdf': 'PDF文档',
    'word': 'Word文档',
    'presentation': '演示文稿',
    'text': '文本文件',
    'image': '图片文件'
  }
  return labels[type] || type
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const getColumnWidth = (column: string) => {
  // 根据列名长度动态设置宽度
  const minWidth = 120
  const maxWidth = 300
  const charWidth = 12
  const calculatedWidth = column.length * charWidth + 40
  return Math.min(Math.max(calculatedWidth, minWidth), maxWidth)
}

const getPdfDataUrl = (base64Data: string) => {
  return `data:application/pdf;base64,${base64Data}`
}

const getImageDataUrl = (base64Data: string, mimeType: string) => {
  return `data:${mimeType};base64,${base64Data}`
}

const loadDocumentInfo = async () => {
  if (!props.dataset) return
  
  try {
    loading.value = true
    error.value = null
    
    const response = await axios.get(`/api/datasets/${props.dataset.id}/document-info`)
    documentInfo.value = response.data
    
    // 设置默认预览方法
    if (documentInfo.value?.file_info?.preview_methods?.length > 0) {
      selectedMethod.value = documentInfo.value.file_info.preview_methods[0]
      selectedMethodIndex.value = 0
      await loadPreview()
    }
  } catch (err: any) {
    console.error('加载文档信息失败:', err)
    error.value = {
      title: '加载失败',
      message: err.response?.data?.detail || '无法加载文档信息'
    }
  } finally {
    loading.value = false
  }
}

const loadPreview = async () => {
  if (!props.dataset || !selectedMethod.value) return
  
  try {
    loading.value = true
    error.value = null
    
    const params: any = {
      method: selectedMethod.value
    }
    
    // 如果是PDF预览，添加页码参数
    if (selectedMethod.value === 'pdf_viewer') {
      params.page = currentPage.value
    }
    
    const response = await axios.get(`/api/datasets/${props.dataset.id}/document-preview`, {
      params
    })
    
    previewData.value = response.data
    
    // 如果是PDF，更新总页数
    if (selectedMethod.value === 'pdf_viewer' && response.data.total_pages) {
      totalPages.value = response.data.total_pages
    }
  } catch (err: any) {
    console.error('加载预览失败:', err)
    error.value = {
      title: '预览失败',
      message: err.response?.data?.detail || '无法加载文档预览'
    }
  } finally {
    loading.value = false
  }
}

const changePreviewMethod = async () => {
  currentPage.value = 1
  await loadPreview()
}

const handleMethodChange = (index: number) => {
  if (availableMethods.value[index]) {
    selectedMethod.value = availableMethods.value[index].value
    changePreviewMethod()
  }
}

const refreshPreview = async () => {
  await loadDocumentInfo()
}

const downloadDocument = async () => {
  if (!props.dataset) return
  
  try {
    downloading.value = true
    
    const response = await axios.get(`/api/datasets/${props.dataset.id}/download`, {
      responseType: 'blob'
    })
    
    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', props.dataset.name || 'document')
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  } catch (err: any) {
    console.error('下载失败:', err)
    // 这里可以添加错误提示
  } finally {
    downloading.value = false
  }
}

const downloadFile = downloadDocument

const previousPage = async () => {
  if (currentPage.value > 1) {
    currentPage.value--
    await loadPreview()
  }
}

const nextPage = async () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
    await loadPreview()
  }
}

// 监听器
watch(() => props.dataset, async (newDataset) => {
  if (newDataset) {
    await loadDocumentInfo()
  }
}, { immediate: true })

// 生命周期
onMounted(async () => {
  if (props.dataset) {
    await loadDocumentInfo()
  }
})
</script>

<style scoped>
.document-preview {
  width: 100%;
  height: 100%;
}

.info-card {
  margin-bottom: 16px;
}

.document-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-item .label {
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), 0.6);
  font-weight: 500;
}

.info-item .value {
  font-size: 14px;
  color: rgba(var(--v-theme-on-surface), 0.87);
}

.preview-methods-card {
  margin-bottom: 16px;
}

.methods-header {
  margin-bottom: 12px;
  font-weight: 500;
}

.action-buttons {
  margin-bottom: 16px;
}

.preview-content-card {
  min-height: 400px;
}

.preview-container {
  min-height: 300px;
}

.error-state {
  padding: 40px 20px;
}

.table-preview {
  width: 100%;
}

.table-info {
  margin-top: 12px;
  text-align: center;
}

.html-preview {
  max-height: 600px;
  overflow-y: auto;
}

.html-content {
  padding: 16px;
  border: 1px solid rgba(var(--v-theme-outline), 0.12);
  border-radius: 4px;
}

.pdf-preview {
  text-align: center;
}

.pdf-controls {
  margin-bottom: 16px;
}

.pdf-page-image {
  max-width: 100%;
  max-height: 600px;
  border: 1px solid rgba(var(--v-theme-outline), 0.12);
  border-radius: 4px;
}

.text-preview,
.code-preview {
  max-height: 600px;
  overflow-y: auto;
}

.text-content {
  font-family: 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}

.code-content {
  font-family: 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.5;
}

.image-preview {
  padding: 20px;
}

.preview-image {
  max-width: 100%;
  max-height: 600px;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.image-info {
  margin-top: 16px;
}

.empty-state {
  padding: 60px 20px;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .document-info {
    grid-template-columns: 1fr;
  }
  
  .action-buttons {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  
  .pdf-controls {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12px;
  }
}

/* 深色模式适配 */
.v-theme--dark .html-content,
.v-theme--dark .pdf-page-image {
  border-color: rgba(var(--v-theme-outline), 0.24);
}

.v-theme--dark .preview-image {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}
</style>