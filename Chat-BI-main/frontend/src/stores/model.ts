/**
 * AI模型选择状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

interface ModelConfig {
  id: number
  config_name: string
  model_name: string
  model_type: string
  api_url: string
  api_key?: string
  temperature?: number
  max_tokens?: number
  is_default?: boolean
}

export const useModelStore = defineStore('model', () => {
  // 状态
  const selectedModel = ref<ModelConfig | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // 临时使用固定的 user_id = 1
  const USER_ID = 1

  // 计算属性
  const selectedModelId = computed(() => selectedModel.value?.id || null)
  const selectedModelName = computed(() => selectedModel.value?.model_name || '选择模型')
  const hasSelectedModel = computed(() => selectedModel.value !== null)

  /**
   * 从后端获取当前选择的模型
   */
  const fetchCurrentModel = async (): Promise<void> => {
    isLoading.value = true
    error.value = null

    try {
      const response = await axios.get(
        `${import.meta.env.VITE_API_BASE_URL}/api/current-model/${USER_ID}`
      )

      if (response.data.success && response.data.model_config) {
        selectedModel.value = response.data.model_config
        console.log('从后端获取当前模型:', selectedModel.value)
      }
    } catch (err: any) {
      console.error('获取当前模型失败:', err)
      error.value = err.response?.data?.detail || '获取模型失败'
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 选择新的AI模型
   */
  const selectModel = async (model: ModelConfig): Promise<boolean> => {
    isLoading.value = true
    error.value = null

    try {
      console.log('选择新模型:', model)

      // 调用后端API保存到Redis
      const response = await axios.post(
        `${import.meta.env.VITE_API_BASE_URL}/api/select-model`,
        {
          user_id: USER_ID,
          model_id: model.id
        }
      )

      if (response.data.success) {
        // 更新本地状态
        selectedModel.value = response.data.model_data
        console.log('模型选择成功:', selectedModel.value)
        return true
      } else {
        error.value = response.data.message || '选择模型失败'
        return false
      }
    } catch (err: any) {
      console.error('选择模型失败:', err)
      error.value = err.response?.data?.detail || '选择模型失败'
      return false
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 清除选择的模型
   */
  const clearModel = () => {
    selectedModel.value = null
    error.value = null
  }

  return {
    // 状态
    selectedModel,
    isLoading,
    error,

    // 计算属性
    selectedModelId,
    selectedModelName,
    hasSelectedModel,

    // 方法
    fetchCurrentModel,
    selectModel,
    clearModel
  }
})
