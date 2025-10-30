import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export interface Dataset {
  id: string
  name: string
  logical_name?: string
  description?: string
  parse_status: 'pending' | 'parsing' | 'parsed' | 'failed'
  parse_progress?: number
  error_message?: string
  chunk_status?: 'pending' | 'chunking' | 'completed' | 'failed'
  chunk_progress?: number
  chunk_error?: string
  vectorize_status?: 'pending' | 'vectorizing' | 'completed' | 'failed'
  vectorize_progress?: number
  vectorize_error?: string
  embedding_status?: 'pending' | 'embedding' | 'completed' | 'failed'
  embedding_progress?: number
  embedding_error?: string
  row_count: number
  column_count: number
  file_size?: number
  created_at: string
  updated_at?: string
}

export const useDatasetStore = defineStore('dataset', () => {
  // 状态
  const datasets = ref<Dataset[]>([])
  const loading = ref(false)
  const lastFetchTime = ref<number>(0)
  const error = ref<string | null>(null)

  // 缓存时间：5分钟
  const CACHE_DURATION = 5 * 60 * 1000

  // 请求去重：存储正在进行的请求Promise
  let fetchPromise: Promise<Dataset[]> | null = null
  
  // 计算属性
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

  // 检查缓存是否有效
  const isCacheValid = () => {
    return Date.now() - lastFetchTime.value < CACHE_DURATION
  }

  // 获取数据集列表（带缓存 + 请求去重）
  const fetchDatasets = async (forceRefresh = false) => {
    // 如果缓存有效且不是强制刷新，直接返回缓存数据
    if (!forceRefresh && isCacheValid() && datasets.value.length > 0) {
      console.log('使用缓存的数据集列表')
      return datasets.value
    }

    // 如果已有正在进行的请求，返回该请求的Promise（请求去重）
    if (fetchPromise) {
      console.log('复用正在进行的数据集请求')
      return fetchPromise
    }

    loading.value = true
    error.value = null

    // 创建新的请求Promise
    fetchPromise = (async () => {
      try {
        console.log('从服务器获取数据集列表')
        const response = await axios.get(
          `${import.meta.env.VITE_API_BASE_URL}/api/datasets`
        )

        datasets.value = response.data.datasets || []
        lastFetchTime.value = Date.now()

        console.log('数据集列表已更新:', datasets.value.length, '个数据集')
        return datasets.value
      } catch (err: any) {
        error.value = err.response?.data?.message || '获取数据集列表失败'
        console.error('获取数据集列表失败:', err)
        throw err
      } finally {
        loading.value = false
        // 请求完成后清除Promise，允许后续新请求
        fetchPromise = null
      }
    })()

    return fetchPromise
  }

  // 刷新数据集列表
  const refreshDatasets = () => {
    return fetchDatasets(true)
  }

  // 添加数据集到列表（用于上传成功后）
  const addDataset = (dataset: Dataset) => {
    const existingIndex = datasets.value.findIndex(d => d.id === dataset.id)
    if (existingIndex >= 0) {
      datasets.value[existingIndex] = dataset
    } else {
      datasets.value.unshift(dataset) // 添加到开头
    }
  }

  // 更新数据集状态
  const updateDataset = (id: string, updates: Partial<Dataset>) => {
    const index = datasets.value.findIndex(d => d.id === id)
    if (index >= 0) {
      datasets.value[index] = { ...datasets.value[index], ...updates }
    }
  }

  // 删除数据集
  const removeDataset = (id: string) => {
    const index = datasets.value.findIndex(d => d.id === id)
    if (index >= 0) {
      datasets.value.splice(index, 1)
    }
  }

  // 根据ID获取数据集
  const getDatasetById = (id: string) => {
    return datasets.value.find(d => d.id === id)
  }

  // 清除缓存
  const clearCache = () => {
    datasets.value = []
    lastFetchTime.value = 0
    error.value = null
  }

  // 检查是否有正在处理的数据集
  const hasProcessingDatasets = computed(() => {
    return processingCount.value > 0
  })

  return {
    // 状态
    datasets,
    loading,
    error,
    lastFetchTime,
    
    // 计算属性
    completedCount,
    processingCount,
    failedCount,
    hasProcessingDatasets,
    
    // 方法
    fetchDatasets,
    refreshDatasets,
    addDataset,
    updateDataset,
    removeDataset,
    getDatasetById,
    clearCache,
    isCacheValid
  }
})