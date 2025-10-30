<template>
  <div class="model-selector">
    <v-menu location="bottom">
      <template v-slot:activator="{ props }">
        <v-btn
          variant="text"
          class="model-btn"
          :disabled="loading || models.length === 0"
          v-bind="props">
          <v-icon start size="20">mdi-brain</v-icon>
          <span class="model-name">{{ selectedModelName }}</span>
          <v-icon end size="20">mdi-chevron-down</v-icon>
        </v-btn>
      </template>

      <v-list class="model-list">
        <v-list-subheader>选择 AI 模型</v-list-subheader>

        <div v-if="loading" class="loading-state">
          <v-progress-circular indeterminate size="24"></v-progress-circular>
          <span class="ml-2">加载中...</span>
        </div>

        <div v-else-if="models.length === 0" class="empty-state">
          <v-icon size="32" color="grey">mdi-alert-circle-outline</v-icon>
          <p class="text-body-2 mt-2">暂无可用模型</p>
        </div>

        <v-list-item
          v-else
          v-for="model in models"
          :key="model.id"
          :value="model.id"
          :active="selectedModelId === model.id"
          @click="handleSelectModel(model)">
          <template v-slot:prepend>
            <v-icon>{{ getModelIcon(model.modelType) }}</v-icon>
          </template>
          <v-list-item-title>{{ model.configName }}</v-list-item-title>
          <v-list-item-subtitle>{{ model.modelName }}</v-list-item-subtitle>
          <template v-slot:append v-if="selectedModelId === model.id">
            <v-icon color="primary">mdi-check</v-icon>
          </template>
        </v-list-item>
      </v-list>
    </v-menu>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { useModelStore } from '@/stores/model'

interface ModelConfig {
  id: number
  configName: string
  modelName: string
  modelType: string
  apiUrl: string
  description?: string
  isDefault: boolean
  isActive: boolean
}

const models = ref<ModelConfig[]>([])
const loading = ref(false)

// 使用Pinia store管理模型选择
const modelStore = useModelStore()

// 临时使用固定的 user_id = 1
const USER_ID = 1

// 从store获取选中的模型ID
const selectedModelId = computed(() => modelStore.selectedModelId)

const selectedModelName = computed(() => {
  console.log('=== selectedModelName computed ===')
  console.log('loading:', loading.value)
  console.log('models.length:', models.value.length)
  console.log('selectedModelId:', selectedModelId.value)

  if (loading.value) return '加载中...'
  if (models.value.length === 0) return '无可用模型'
  if (!selectedModelId.value) return '选择模型'

  const model = models.value.find(m => m.id === selectedModelId.value)
  console.log('found model:', model)
  const result = model ? model.modelName : '选择模型'
  console.log('selectedModelName result:', result)
  return result
})

const getModelIcon = (modelType: string): string => {
  const iconMap: Record<string, string> = {
    'openai': 'mdi-star',
    'claude': 'mdi-file-document',
    'gemini': 'mdi-google',
    'qwen': 'mdi-brain',
    'default': 'mdi-robot'
  }
  return iconMap[modelType.toLowerCase()] || iconMap['default']
}

const fetchModels = async () => {
  loading.value = true
  try {
    console.log('正在获取模型列表...')
    const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/ai-model-configs`, {
      params: {
        user_id: USER_ID,
        limit: 100
      }
    })

    console.log('API原始响应:', response.data)

    // API返回的字段可能是驼峰或下划线格式,需要统一处理
    const items = response.data.items || []
    console.log('总模型数:', items.length)

    models.value = items
      // 只显示激活的且模型类型为 chat 的模型
      .filter((m: any) => {
        const isActive = m.isActive === true || m.is_active === true
        const modelType = (m.modelType || m.model_type || '').toLowerCase()
        const isChatModel = modelType === 'chat'
        if (!isChatModel) {
          console.log(`过滤掉非chat模型: ${m.configName || m.config_name} (类型: ${modelType})`)
        }
        return isActive && isChatModel
      })
      .map((m: any) => ({
        id: m.id,
        configName: m.configName || m.config_name || '未命名配置',
        modelName: m.modelName || m.model_name || '',
        modelType: m.modelType || m.model_type || 'default',
        apiUrl: m.apiUrl || m.api_url || '',
        description: m.description || '',
        isDefault: m.isDefault === true || m.is_default === true,
        isActive: m.isActive === true || m.is_active === true,
      }))

    console.log('过滤后的 Chat 模型数量:', models.value.length)
    console.log('Chat 模型列表:', models.value)

    // 从后端获取当前选择的模型(存储在Redis中)
    await modelStore.fetchCurrentModel()

    // 如果store中没有选择的模型,自动选择默认模型
    if (!modelStore.hasSelectedModel) {
      const defaultModel = models.value.find(m => m.isDefault)
      if (defaultModel) {
        await handleSelectModel(defaultModel)
        console.log('自动选择默认模型:', defaultModel.configName)
      } else if (models.value.length > 0) {
        await handleSelectModel(models.value[0])
        console.log('自动选择第一个模型:', models.value[0].configName)
      } else {
        console.warn('没有可用的模型')
      }
    }
  } catch (error: any) {
    console.error('获取模型列表失败:', error)
    console.error('错误详情:', error.response?.data || error.message)
  } finally {
    loading.value = false
  }
}

const emit = defineEmits(['update:modelId', 'modelSelected'])

const handleSelectModel = async (model: ModelConfig) => {
  console.log('选择模型:', model)

  // 调用store方法,保存到Redis
  const success = await modelStore.selectModel({
    id: model.id,
    config_name: model.configName,
    model_name: model.modelName,
    model_type: model.modelType,
    api_url: model.apiUrl,
    is_default: model.isDefault
  })

  if (success) {
    // 发送事件通知父组件
    emit('update:modelId', model.id)
    emit('modelSelected', model)
  }
}

onMounted(() => {
  fetchModels()
})
</script>

<style scoped>
.model-selector {
  display: inline-block;
}

.model-btn {
  min-width: 140px;
  height: 40px;
  border-radius: 20px;
  text-transform: none;
  font-weight: 500;
  padding: 0 1rem;
  transition: all 0.2s ease;
}

.model-name {
  flex: 1;
  text-align: center;
  font-size: 0.875rem;
  color: inherit;
  opacity: 1;
  visibility: visible;
}

.model-list {
  min-width: 280px;
  max-width: 320px;
}

.model-list :deep(.v-list-item) {
  padding: 0.75rem 1rem;
}

.model-list :deep(.v-list-item-title) {
  font-size: 0.9375rem;
  font-weight: 500;
  margin-bottom: 0.25rem;
}

.model-list :deep(.v-list-item-subtitle) {
  font-size: 0.8125rem;
  opacity: 0.7;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem 1rem;
  text-align: center;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.loading-state {
  flex-direction: row;
}
</style>
