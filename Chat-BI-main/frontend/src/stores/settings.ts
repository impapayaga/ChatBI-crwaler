import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

export type RoundedSize = 0 | 'sm' | 'md' | 'lg' | 'xl'

export interface EmbeddingConfigStatus {
  configured: boolean
  modelName: string
  configName: string
  provider: string
}

export const useSettingsStore = defineStore('settings', () => {
  // 圆角设置
  const roundedSize = ref<RoundedSize>('lg')

  // Embedding 配置状态
  const embeddingConfigStatus = ref<EmbeddingConfigStatus>({
    configured: false,
    modelName: '',
    configName: '',
    provider: ''
  })

  // 从 localStorage 加载设置
  const loadSettings = () => {
    const savedRounded = localStorage.getItem('roundedSize')
    if (savedRounded) {
      roundedSize.value = savedRounded as RoundedSize
    }
  }

  // 设置圆角大小
  const setRoundedSize = (size: RoundedSize) => {
    roundedSize.value = size
    localStorage.setItem('roundedSize', size.toString())

    // 动态更新 CSS 变量
    updateCSSVariables()
  }

  // 更新 CSS 变量
  const updateCSSVariables = () => {
    const root = document.documentElement

    // 根据选择的圆角大小设置 CSS 变量
    const roundedMap: Record<RoundedSize, string> = {
      0: '0px',
      'sm': '4px',
      'md': '8px',
      'lg': '12px',
      'xl': '16px',
    }

    root.style.setProperty('--v-border-radius', roundedMap[roundedSize.value])
  }

  // 加载 Embedding 配置状态
  const loadEmbeddingConfig = async () => {
    try {
      const response = await axios.get(
        `${import.meta.env.VITE_API_BASE_URL}/api/ai-model-configs`,
        { params: { user_id: 1, limit: 100 } }
      )

      // 后端返回格式: { total: number, items: [...] }
      if (response.data && response.data.items && response.data.items.length > 0) {
        // 优先查找默认的 embedding 配置
        let embeddingConfig = response.data.items.find(
          (config: any) => config.modelType === 'embedding' && config.isActive && config.isDefault
        )

        // 如果没有默认配置，则查找第一个启用的 embedding 配置
        if (!embeddingConfig) {
          embeddingConfig = response.data.items.find(
            (config: any) => config.modelType === 'embedding' && config.isActive
          )
        }

        if (embeddingConfig) {
          embeddingConfigStatus.value = {
            configured: true,
            modelName: embeddingConfig.modelName,
            configName: embeddingConfig.configName,
            provider: embeddingConfig.provider || '未指定'
          }
        } else {
          embeddingConfigStatus.value.configured = false
        }
      } else {
        embeddingConfigStatus.value.configured = false
      }
    } catch (error) {
      console.error('加载 Embedding 配置失败:', error)
      embeddingConfigStatus.value.configured = false
    }
  }

  // 初始化设置
  const initSettings = () => {
    loadSettings()
    updateCSSVariables()
    loadEmbeddingConfig()
  }

  return {
    roundedSize,
    setRoundedSize,
    initSettings,
    embeddingConfigStatus,
    loadEmbeddingConfig,
  }
})
