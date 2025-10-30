<template>
  <div class="dataset-management-wrapper">
    <v-container fluid class="dataset-management pa-6">
      <!-- 标题行 -->
      <div class="d-flex align-center justify-space-between mb-4">
        <h2 class="text-h4 font-weight-bold">数据集管理</h2>
        <div class="d-flex gap-2">
          <v-btn
            color="primary"
            prepend-icon="mdi-refresh"
            @click="loadDatasets"
            :loading="loading"
          >
            刷新
          </v-btn>
        </div>
      </div>

      <!-- 统计卡片 -->
      <v-row class="mb-4">
        <v-col cols="12" md="3">
          <StatCard
            icon="mdi-file-multiple"
            :value="datasets.length"
            label="总数据集"
            color="primary"
          />
        </v-col>

        <v-col cols="12" md="3">
          <StatCard
            icon="mdi-check-circle"
            :value="completedCount"
            label="已完成"
            color="success"
          />
        </v-col>

        <v-col cols="12" md="3">
          <StatCard
            icon="mdi-clock-outline"
            :value="processingCount"
            label="处理中"
            color="warning"
          />
        </v-col>

        <v-col cols="12" md="3">
          <StatCard
            icon="mdi-alert-circle"
            :value="failedCount"
            label="失败"
            color="error"
          />
        </v-col>
      </v-row>

      <!-- 数据集列表 - 桌面端表格 -->
      <v-card class="d-none d-md-block">
        <v-data-table
          :headers="headers"
          :items="datasets"
          :loading="loading"
          :items-per-page="20"
          class="dataset-table"
        >
          <!-- 文件名列 -->
          <template v-slot:item.name="{ item }">
            <div class="d-flex align-center py-2">
              <v-icon class="mr-2" color="primary">mdi-file-delimited</v-icon>
              <div>
                <div class="font-weight-medium">{{ item.logical_name || item.name }}</div>
                <div class="text-caption text-medium-emphasis">{{ item.name }}</div>
              </div>
            </div>
          </template>

          <!-- 数据规模列 -->
          <template v-slot:item.size="{ item }">
            <div v-if="item.parse_status === 'parsed'">
              <div class="font-weight-medium">{{ item.row_count?.toLocaleString() }} 行</div>
              <div class="text-caption text-medium-emphasis">{{ item.column_count }} 列</div>
            </div>
            <div v-else class="text-medium-emphasis">-</div>
          </template>

          <!-- 状态列 -->
          <template v-slot:item.status="{ item }">
            <div class="status-container">
              <!-- 解析状态 -->
              <v-chip
                size="small"
                :color="getStatusColor(item.parse_status)"
                variant="flat"
                class="mb-1"
              >
                <v-icon size="16" class="mr-1">{{ getStatusIcon(item.parse_status) }}</v-icon>
                解析: {{ getStatusText(item.parse_status) }}
              </v-chip>

              <!-- 分片状态 -->
              <v-chip
                v-if="item.parse_status === 'parsed'"
                size="small"
                :color="getStatusColor(item.chunk_status)"
                variant="flat"
                class="mb-1"
              >
                <v-icon size="16" class="mr-1">{{ getStatusIcon(item.chunk_status) }}</v-icon>
                分片: {{ getStatusText(item.chunk_status) }}
              </v-chip>

              <!-- 向量化状态 -->
              <v-chip
                v-if="item.chunk_status === 'completed'"
                size="small"
                :color="getStatusColor(item.vectorize_status)"
                variant="flat"
              >
                <v-icon size="16" class="mr-1">{{ getStatusIcon(item.vectorize_status) }}</v-icon>
                向量化: {{ getStatusText(item.vectorize_status) }}
              </v-chip>
            </div>
          </template>

          <!-- 进度列 -->
          <template v-slot:item.progress="{ item }">
            <div class="progress-container">
              <v-progress-linear
                v-if="item.parse_status === 'parsing'"
                :model-value="item.parse_progress || 0"
                color="primary"
                height="6"
                rounded
              />
              <v-progress-linear
                v-else-if="item.chunk_status === 'chunking'"
                :model-value="item.chunk_progress || 0"
                color="primary"
                height="6"
                rounded
              />
              <v-progress-linear
                v-else-if="item.vectorize_status === 'vectorizing'"
                :model-value="item.vectorize_progress || 0"
                color="secondary"
                height="6"
                rounded
              />
              <div v-else class="text-caption text-medium-emphasis text-center">
                {{ getOverallStatus(item) }}
              </div>
            </div>
          </template>

          <!-- 操作列 -->
          <template v-slot:item.actions="{ item }">
            <div class="d-flex gap-1 justify-center">
              <!-- 查看详情 -->
              <v-tooltip text="查看详情" location="top">
                <template v-slot:activator="{ props }">
                  <v-btn
                    icon="mdi-eye"
                    size="small"
                    variant="text"
                    color="primary"
                    @click="viewDetails(item)"
                    v-bind="props"
                  />
                </template>
              </v-tooltip>

              <!-- 查看原文件 -->
              <v-tooltip text="查看原文件" location="top">
                <template v-slot:activator="{ props }">
                  <v-btn
                    icon="mdi-file-document-outline"
                    size="small"
                    variant="text"
                    color="secondary"
                    @click="showOriginalFilePreview(item)"
                    v-bind="props"
                  />
                </template>
              </v-tooltip>

              <!-- 重试按钮 -->
              <v-tooltip v-if="canRetry(item)" text="重试" location="top">
                <template v-slot:activator="{ props }">
                  <v-btn
                    icon="mdi-refresh"
                    size="small"
                    variant="text"
                    color="warning"
                    @click="retryTask(item)"
                    v-bind="props"
                  />
                </template>
              </v-tooltip>

              <!-- 删除按钮 -->
              <v-tooltip text="删除" location="top">
                <template v-slot:activator="{ props }">
                  <v-btn
                    icon="mdi-delete"
                    size="small"
                    variant="text"
                    color="error"
                    @click="confirmDelete(item)"
                    v-bind="props"
                  />
                </template>
              </v-tooltip>
            </div>
          </template>
        </v-data-table>
      </v-card>

      <!-- 数据集列表 - 移动端卡片 -->
      <div class="d-md-none mobile-cards-container">
        <v-card
          v-for="item in datasets"
          :key="item.id"
          class="mb-3 dataset-mobile-card"
          @click="openPreviewDialog(item)"
        >
          <v-card-text>
            <!-- 文件名和图标 -->
            <div class="d-flex align-center mb-3">
              <v-icon color="primary" size="32" class="mr-3">mdi-file-delimited</v-icon>
              <div class="flex-grow-1">
                <div class="font-weight-bold text-body-1">{{ item.logical_name || item.name }}</div>
                <div class="text-caption text-medium-emphasis">{{ item.name }}</div>
              </div>
            </div>

            <!-- 数据规模 -->
            <div v-if="item.parse_status === 'parsed'" class="mb-3">
              <v-chip size="small" variant="tonal" color="primary">
                <v-icon size="16" start>mdi-table</v-icon>
                {{ item.row_count?.toLocaleString() }} 行 × {{ item.column_count }} 列
              </v-chip>
            </div>

            <!-- 处理状态 -->
            <div class="mb-3">
              <div class="text-caption text-medium-emphasis mb-1">处理状态</div>
              <div class="d-flex flex-column gap-1">
                <!-- 解析状态 -->
                <v-chip
                  size="small"
                  :color="getStatusColor(item.parse_status)"
                  variant="flat"
                >
                  <v-icon size="16" class="mr-1">{{ getStatusIcon(item.parse_status) }}</v-icon>
                  解析: {{ getStatusText(item.parse_status) }}
                </v-chip>

                <!-- 分片状态 -->
                <v-chip
                  v-if="item.parse_status === 'parsed'"
                  size="small"
                  :color="getStatusColor(item.chunk_status)"
                  variant="flat"
                >
                  <v-icon size="16" class="mr-1">{{ getStatusIcon(item.chunk_status) }}</v-icon>
                  分片: {{ getStatusText(item.chunk_status) }}
                </v-chip>

                <!-- 向量化状态 -->
                <v-chip
                  v-if="item.chunk_status === 'completed'"
                  size="small"
                  :color="getStatusColor(item.vectorize_status)"
                  variant="flat"
                >
                  <v-icon size="16" class="mr-1">{{ getStatusIcon(item.vectorize_status) }}</v-icon>
                  向量化: {{ getStatusText(item.vectorize_status) }}
                </v-chip>
              </div>
            </div>

            <!-- 进度 -->
            <div v-if="item.parse_status === 'parsing' || item.chunk_status === 'chunking' || item.vectorize_status === 'vectorizing'" class="mb-3">
              <div class="text-caption text-medium-emphasis mb-1">进度</div>
              <v-progress-linear
                v-if="item.parse_status === 'parsing'"
                :model-value="item.parse_progress || 0"
                color="primary"
                height="6"
                rounded
              />
              <v-progress-linear
                v-else-if="item.chunk_status === 'chunking'"
                :model-value="item.chunk_progress || 0"
                color="primary"
                height="6"
                rounded
              />
              <v-progress-linear
                v-else-if="item.vectorize_status === 'vectorizing'"
                :model-value="item.vectorize_progress || 0"
                color="secondary"
                height="6"
                rounded
              />
            </div>
            <div v-else class="mb-3">
              <v-chip size="small" variant="tonal">
                {{ getOverallStatus(item) }}
              </v-chip>
            </div>

            <!-- 操作按钮 -->
            <div class="d-flex gap-2">
              <v-btn
                size="small"
                variant="tonal"
                color="primary"
                prepend-icon="mdi-eye"
                @click.stop="viewDetails(item)"
                block
              >
                查看详情
              </v-btn>
              <v-btn
                size="small"
                variant="tonal"
                color="secondary"
                prepend-icon="mdi-file-document-outline"
                @click.stop="showOriginalFilePreview(item)"
                block
              >
                查看原文件
              </v-btn>
              <v-btn
                v-if="canRetry(item)"
                size="small"
                variant="tonal"
                color="warning"
                icon="mdi-refresh"
                @click.stop="retryTask(item)"
              />
              <v-btn
                size="small"
                variant="tonal"
                color="error"
                icon="mdi-delete"
                @click.stop="confirmDelete(item)"
              />
            </div>
          </v-card-text>
        </v-card>

        <!-- 加载中 -->
        <div v-if="loading" class="text-center py-8">
          <v-progress-circular indeterminate color="primary" />
          <div class="text-caption text-medium-emphasis mt-2">加载中...</div>
        </div>

        <!-- 空状态 -->
        <div v-if="!loading && datasets.length === 0" class="text-center py-8">
          <v-icon size="64" color="grey">mdi-database-off</v-icon>
          <div class="text-body-1 text-medium-emphasis mt-2">暂无数据集</div>
        </div>
      </div>
    </v-container>

    <!-- 详情对话框 - 引用 DatasetList 组件的逻辑 -->
    <v-dialog v-model="detailsDialog" max-width="700">
      <v-card v-if="selectedDataset">
        <v-card-title>
          <div class="d-flex align-center">
            <v-icon class="mr-2">mdi-file-delimited</v-icon>
            {{ selectedDataset.logical_name || selectedDataset.name }}
          </div>
        </v-card-title>

        <v-divider />

        <v-card-text class="pt-4">
          <!-- 基本信息 -->
          <div class="mb-4">
            <div class="text-subtitle-2 mb-2">基本信息</div>
            <v-list density="compact">
              <v-list-item>
                <template v-slot:prepend>
                  <v-icon size="20">mdi-file</v-icon>
                </template>
                <v-list-item-title>文件名</v-list-item-title>
                <v-list-item-subtitle>{{ selectedDataset.name }}</v-list-item-subtitle>
              </v-list-item>
              <v-list-item v-if="selectedDataset.parse_status === 'parsed'">
                <template v-slot:prepend>
                  <v-icon size="20">mdi-table</v-icon>
                </template>
                <v-list-item-title>数据规模</v-list-item-title>
                <v-list-item-subtitle>
                  {{ selectedDataset.row_count?.toLocaleString() }} 行 × {{ selectedDataset.column_count }} 列
                </v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </div>

          <!-- 处理流程 -->
          <div class="mb-4">
            <div class="text-subtitle-2 mb-2">处理流程</div>
            <v-timeline density="compact" side="end" align="start">
              <!-- 文件解析 -->
              <v-timeline-item
                :dot-color="getStatusColor(selectedDataset.parse_status)"
                size="small"
              >
                <template v-slot:opposite>
                  <span class="text-caption">步骤 1</span>
                </template>
                <div>
                  <div class="font-weight-medium mb-1">文件解析</div>
                  <v-chip size="x-small" :color="getStatusColor(selectedDataset.parse_status)">
                    {{ getStatusText(selectedDataset.parse_status) }}
                  </v-chip>
                  <div v-if="selectedDataset.error_message" class="text-caption text-error mt-1">
                    {{ selectedDataset.error_message }}
                  </div>
                </div>
              </v-timeline-item>

              <!-- 数据分片 -->
              <v-timeline-item
                :dot-color="getStatusColor(selectedDataset.chunk_status)"
                size="small"
              >
                <template v-slot:opposite>
                  <span class="text-caption">步骤 2</span>
                </template>
                <div>
                  <div class="font-weight-medium mb-1">数据分片</div>
                  <v-chip size="x-small" :color="getStatusColor(selectedDataset.chunk_status)">
                    {{ getStatusText(selectedDataset.chunk_status) }}
                  </v-chip>
                  <div v-if="selectedDataset.chunk_error" class="text-caption text-error mt-1">
                    {{ selectedDataset.chunk_error }}
                  </div>
                </div>
              </v-timeline-item>

              <!-- 向量化 -->
              <v-timeline-item
                :dot-color="getStatusColor(selectedDataset.vectorize_status)"
                size="small"
              >
                <template v-slot:opposite>
                  <span class="text-caption">步骤 3</span>
                </template>
                <div>
                  <div class="font-weight-medium mb-1">向量化生成</div>
                  <v-chip size="x-small" :color="getStatusColor(selectedDataset.vectorize_status)">
                    {{ getStatusText(selectedDataset.vectorize_status) }}
                  </v-chip>
                  <v-progress-linear
                    v-if="selectedDataset.vectorize_status === 'vectorizing'"
                    :model-value="selectedDataset.vectorize_progress || 0"
                    color="secondary"
                    height="4"
                    class="mt-2"
                  />
                  <div v-if="selectedDataset.vectorize_error" class="text-caption text-error mt-1">
                    {{ selectedDataset.vectorize_error }}
                  </div>
                </div>
              </v-timeline-item>
            </v-timeline>
          </div>
        </v-card-text>

        <v-divider />

        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="detailsDialog = false">关闭</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 删除确认对话框 -->
    <v-dialog v-model="deleteDialog" max-width="500">
      <v-card>
        <v-card-title>确认删除</v-card-title>
        <v-card-text>
          确定要删除数据集 <strong>{{ datasetToDelete?.name }}</strong> 吗？
          <br />
          此操作将删除所有相关文件和向量数据，且不可撤销。
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="deleteDialog = false">取消</v-btn>
          <v-btn color="error" variant="tonal" @click="deleteDataset" :loading="deleting">删除</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snackbar -->
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="3000">
      {{ snackbar.text }}
    </v-snackbar>

    <!-- 数据集预览对话框 -->
    <DatasetPreviewDialog
      v-model="previewDialog"
      :dataset="previewDataset"
    />

    <!-- 原文件预览对话框 -->
    <OriginalFilePreviewDialog
      v-model="originalFilePreviewVisible"
      :dataset="originalFilePreviewDataset"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, onUnmounted } from 'vue'
import axios from 'axios'
import { useDatasetStore, type Dataset } from '@/stores/dataset'
import DatasetPreviewDialog from './DatasetPreviewDialog.vue'
import OriginalFilePreviewDialog from './OriginalFilePreviewDialog.vue'
import StatCard from './StatCard.vue'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL

// 使用数据集store
const datasetStore = useDatasetStore()

// 本地状态
const deleting = ref(false)
const detailsDialog = ref(false)
const deleteDialog = ref(false)
const selectedDataset = ref<Dataset | null>(null)
const datasetToDelete = ref<Dataset | null>(null)

// 数据集预览对话框状态
const previewDialog = ref(false)
const previewDataset = ref<Dataset | null>(null)

// 原文件预览对话框状态
const originalFilePreviewVisible = ref(false)
const originalFilePreviewDataset = ref<Dataset | null>(null)

// 定时刷新器
let refreshInterval: number | null = null

const snackbar = ref({
  show: false,
  text: '',
  color: 'success'
})

const headers = [
  { title: '数据集名称', key: 'name', sortable: true },
  { title: '数据规模', key: 'size', sortable: false },
  { title: '处理状态', key: 'status', sortable: false },
  { title: '进度', key: 'progress', sortable: false },
  { title: '操作', key: 'actions', sortable: false, align: 'center' as const }
]

// 从store获取数据
const datasets = computed(() => datasetStore.datasets)
const loading = computed(() => datasetStore.loading)

// 统计数量
const completedCount = computed(() => {
  return datasets.value.filter(d =>
    d.parse_status === 'parsed' &&
    d.chunk_status === 'completed' &&
    d.vectorize_status === 'completed'
  ).length
})

const processingCount = computed(() => {
  return datasets.value.filter(d =>
    d.parse_status === 'parsing' ||
    d.chunk_status === 'chunking' ||
    d.vectorize_status === 'vectorizing'
  ).length
})

const failedCount = computed(() => {
  return datasets.value.filter(d =>
    d.parse_status === 'failed' ||
    d.chunk_status === 'failed' ||
    d.vectorize_status === 'failed'
  ).length
})

// 加载数据集
const loadDatasets = async () => {
  try {
    await datasetStore.fetchDatasets()
  } catch (error) {
    console.error('加载数据集失败:', error)
    showSnackbar('加载数据集列表失败', 'error')
  }
}

const viewDetails = (dataset: Dataset) => {
  selectedDataset.value = dataset
  detailsDialog.value = true
}

// 打开数据集预览对话框
const openPreviewDialog = (dataset: Dataset) => {
  previewDataset.value = dataset
  previewDialog.value = true
}

// 显示原文件预览
const showOriginalFilePreview = (dataset: Dataset) => {
  originalFilePreviewDataset.value = dataset
  originalFilePreviewVisible.value = true
}

const canRetry = (dataset: Dataset) => {
  return dataset.parse_status === 'failed' ||
         dataset.chunk_status === 'failed' ||
         dataset.vectorize_status === 'failed'
}

const retryTask = async (dataset: Dataset) => {
  try {
    let endpoint = ''
    if (dataset.parse_status === 'failed') {
      endpoint = `/api/dataset/${dataset.id}/retry_parse`
    } else if (dataset.chunk_status === 'failed') {
      endpoint = `/api/dataset/${dataset.id}/retry_chunk`
    } else if (dataset.vectorize_status === 'failed') {
      endpoint = `/api/dataset/${dataset.id}/retry_vectorize`
    }

    await axios.post(`${API_BASE_URL}${endpoint}`)
    showSnackbar('已开始重试，请稍后刷新查看结果', 'success')

    setTimeout(() => {
      loadDatasets()
    }, 2000)
  } catch (error: any) {
    showSnackbar('重试失败: ' + (error.response?.data?.detail || error.message), 'error')
  }
}

const confirmDelete = (dataset: Dataset) => {
  datasetToDelete.value = dataset
  deleteDialog.value = true
}

const deleteDataset = async () => {
  if (!datasetToDelete.value) return

  deleting.value = true
  try {
    await axios.delete(`${API_BASE_URL}/api/dataset/${datasetToDelete.value.id}`)
    showSnackbar('数据集已删除', 'success')
    deleteDialog.value = false
    datasetToDelete.value = null
    await loadDatasets()
  } catch (error: any) {
    showSnackbar('删除失败: ' + (error.response?.data?.detail || error.message), 'error')
  } finally {
    deleting.value = false
  }
}

const getStatusColor = (status?: string) => {
  switch (status) {
    case 'parsing':
    case 'chunking':
    case 'vectorizing':
      return 'primary'
    case 'parsed':
    case 'completed':
      return 'success'
    case 'failed':
      return 'error'
    case 'pending':
      return 'grey'
    default:
      return 'grey'
  }
}

const getStatusIcon = (status?: string) => {
  switch (status) {
    case 'parsing':
    case 'chunking':
    case 'vectorizing':
      return 'mdi-loading mdi-spin'
    case 'parsed':
    case 'completed':
      return 'mdi-check'
    case 'failed':
      return 'mdi-alert'
    case 'pending':
      return 'mdi-clock-outline'
    default:
      return 'mdi-help'
  }
}

const getStatusText = (status?: string) => {
  switch (status) {
    case 'parsing':
      return '解析中'
    case 'chunking':
      return '分片中'
    case 'vectorizing':
      return '向量化中'
    case 'parsed':
    case 'completed':
      return '已完成'
    case 'failed':
      return '失败'
    case 'pending':
      return '等待中'
    default:
      return '未知'
  }
}

const getOverallStatus = (dataset: Dataset) => {
  if (dataset.vectorize_status === 'completed') return '全部完成'
  if (dataset.chunk_status === 'completed') return '等待向量化'
  if (dataset.parse_status === 'parsed') return '等待分片'
  return '-'
}

const showSnackbar = (text: string, color: string = 'success') => {
  snackbar.value = { show: true, text, color }
}

onMounted(() => {
  loadDatasets()
  
  // 设置智能定时刷新（仅在有数据处理中的数据集时）
  refreshInterval = setInterval(() => {
    const hasProcessingDatasets = datasets.value.some(dataset => 
      dataset.parse_status === 'parsing' ||
      dataset.chunk_status === 'chunking' ||
      dataset.vectorize_status === 'vectorizing' ||
      dataset.embedding_status === 'embedding'
    )
    
    if (hasProcessingDatasets) {
      datasetStore.refreshDatasets()
    }
  }, 10000) // 10秒刷新一次，仅在有处理中的数据集时
})

// 组件卸载时清理
onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
    refreshInterval = null
  }
})
</script>

<style scoped>
.dataset-management-wrapper {
  height: 100vh;
  width: 100%;
  overflow-y: auto;
}

.dataset-management {
  min-height: 100%;
}

.gap-1 {
  gap: 0.25rem;
}

.gap-2 {
  gap: 0.5rem;
}

/* 状态容器 */
.status-container {
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: flex-start;
}

/* 进度容器 */
.progress-container {
  min-width: 150px;
}

/* 表格样式 */
.dataset-table {
  height: auto;
}

/* 移动端卡片容器 */
.mobile-cards-container {
  display: flex;
  flex-direction: column;
}

/* 移动端数据集卡片 */
.dataset-mobile-card {
  border-radius: 12px;
  transition: all 0.2s ease;
}

.dataset-mobile-card:active {
  transform: scale(0.98);
  opacity: 0.9;
}

/* 移动端优化标题 */
@media (max-width: 960px) {
  .dataset-management h2 {
    font-size: 1.5rem;
  }

  .dataset-management .pa-6 {
    padding: 1rem !important;
  }
}
</style>
