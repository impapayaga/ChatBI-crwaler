<template>
  <div class="ai-config-page">
    <v-container fluid class="py-6">
      <v-row>
        <v-col cols="12">
          <!-- 页面标题和新增按钮 -->
          <div class="d-flex justify-space-between align-center mb-6">
            <div>
              <h1 class="text-h4 font-weight-bold">
                <v-icon size="large" class="mr-2">mdi-robot</v-icon>
                AI 模型配置
              </h1>
              <p class="text-body-2 text-medium-emphasis mt-2">管理和配置您的 AI 大模型接口</p>
            </div>
            <v-btn
              color="primary"
              size="large"
              prepend-icon="mdi-plus"
              @click="openAddDialog"
            >
              新增配置
            </v-btn>
          </div>

          <!-- 配置卡片列表 -->
          <v-row v-if="savedConfigs.length > 0">
            <v-col
              v-for="config in savedConfigs"
              :key="config.id"
              cols="12"
              sm="6"
              md="4"
              lg="3"
            >
              <v-card
                :class="{ 'border-primary': config.isDefault }"
                :variant="config.isDefault ? 'outlined' : 'elevated'"
                hover
                class="config-card"
              >
                <!-- 卡片头部 -->
                <v-card-title class="py-3 px-4 d-flex align-center">
                  <v-icon
                    :color="config.isActive ? 'success' : 'grey'"
                    size="20"
                    class="mr-2"
                  >
                    {{ config.isDefault ? 'mdi-star' : 'mdi-cog' }}
                  </v-icon>
                  <span class="text-h6 text-truncate flex-grow-1">{{ config.configName }}</span>
                  <v-chip
                    v-if="config.isDefault"
                    size="x-small"
                    color="primary"
                    variant="flat"
                    class="ml-2"
                  >
                    默认
                  </v-chip>
                </v-card-title>

                <v-divider></v-divider>

                <!-- 卡片内容 -->
                <v-card-text class="py-3 px-4">
                  <div class="config-info-compact">
                    <div class="info-item">
                      <v-icon size="16" class="mr-1 text-medium-emphasis">mdi-brain</v-icon>
                      <span class="text-body-2 font-weight-medium">{{ config.modelName }}</span>
                    </div>
                    <div class="info-item mt-1">
                      <v-icon size="16" class="mr-1 text-medium-emphasis">mdi-format-list-bulleted-type</v-icon>
                      <span class="text-caption">{{ getModelTypeLabel(config.modelType) }}</span>
                    </div>
                    <div v-if="config.description" class="info-item mt-2">
                      <p class="text-caption text-medium-emphasis description-text">{{ config.description }}</p>
                    </div>
                  </div>
                </v-card-text>

                <v-divider></v-divider>

                <!-- 卡片底部 -->
                <v-card-actions class="py-2 px-4 d-flex align-center">
                  <v-chip
                    :color="config.isActive ? 'success' : 'grey'"
                    size="x-small"
                    variant="flat"
                  >
                    {{ config.isActive ? '已启用' : '已禁用' }}
                  </v-chip>
                  <v-spacer></v-spacer>
                  <v-btn
                    size="small"
                    variant="text"
                    color="primary"
                    icon="mdi-pencil"
                    @click="openEditDialog(config)"
                  ></v-btn>
                  <v-btn
                    size="small"
                    variant="text"
                    color="error"
                    icon="mdi-delete"
                    @click="deleteConfig(config.id!)"
                  ></v-btn>
                </v-card-actions>
              </v-card>
            </v-col>
          </v-row>

          <!-- 空状态 -->
          <v-card v-else class="text-center py-12">
            <v-card-text>
              <v-icon size="64" color="grey-lighten-1">mdi-robot-outline</v-icon>
              <h3 class="text-h6 mt-4 mb-2">暂无 AI 模型配置</h3>
              <p class="text-body-2 text-medium-emphasis mb-4">
                点击上方"新增配置"按钮创建您的第一个 AI 模型配置
              </p>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </v-container>

    <!-- 配置对话框 -->
    <AIModelConfigDialog
      v-model="dialogVisible"
      :config="editingConfig"
      :is-edit="isEditMode"
      @saved="handleConfigSaved"
    />
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import AIModelConfigDialog from '@/components/AIModelConfigDialog.vue'
import { useSettingsStore } from '@/stores/settings'

interface AIModelConfig {
  id?: number
  userId: number
  configName: string
  modelName: string
  modelType: string
  apiUrl: string
  apiKey: string
  temperature: string
  maxTokens: number | null
  description: string
  isDefault: boolean
  isActive: boolean
}

const savedConfigs = ref<AIModelConfig[]>([])
const dialogVisible = ref(false)
const editingConfig = ref<AIModelConfig | null>(null)
const isEditMode = ref(false)

const route = useRoute()
const router = useRouter()
const settingsStore = useSettingsStore()
const currentUserId = ref(1) // 暂时使用默认用户ID

const getModelTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    chat: '对话模型',
    generate: '生成模型',
    embedding: '嵌入模型'
  }
  return labels[type] || type
}

const loadConfigs = async () => {
  try {
    const response = await axios.get(
      `${import.meta.env.VITE_API_BASE_URL}/api/ai-model-configs`,
      {
        params: {
          user_id: currentUserId.value
        }
      }
    )

    if (response.data && response.data.items) {
      savedConfigs.value = response.data.items
    }
  } catch (error) {
    console.error('加载配置列表失败:', error)
  }
}

const openAddDialog = (modelType?: string) => {
  editingConfig.value = null
  isEditMode.value = false

  // 如果指定了模型类型，创建一个预填充了 modelType 的配置对象
  if (modelType) {
    editingConfig.value = {
      userId: currentUserId.value,
      configName: '',
      modelName: '',
      modelType: modelType,
      apiUrl: '',
      apiKey: '',
      temperature: '0.7',
      maxTokens: 2000,
      description: '',
      isDefault: false,
      isActive: true
    }
  }

  dialogVisible.value = true
}

const openEditDialog = (config: AIModelConfig) => {
  editingConfig.value = { ...config }
  isEditMode.value = true
  dialogVisible.value = true
}

const deleteConfig = async (id: number) => {
  if (!confirm('确定要删除此配置吗？')) {
    return
  }

  try {
    await axios.delete(`${import.meta.env.VITE_API_BASE_URL}/api/ai-model-configs/${id}`)
    await loadConfigs()
    // 刷新 embedding 配置状态（删除的可能是 embedding 类型）
    await settingsStore.loadEmbeddingConfig()
  } catch (error: any) {
    alert('删除失败: ' + (error.response?.data?.detail || error.message))
  }
}

const clearUrlParams = () => {
  // 清除 URL 中的查询参数
  if (route.query.addType) {
    router.replace({ path: route.path })
  }
}

const handleConfigSaved = async () => {
  dialogVisible.value = false
  await loadConfigs()
  // 刷新 embedding 配置状态（如果保存的是 embedding 类型）
  await settingsStore.loadEmbeddingConfig()
  // 清除 URL 参数
  clearUrlParams()
}

// 监听对话框关闭，清除 URL 参数
watch(dialogVisible, (newValue) => {
  if (!newValue) {
    clearUrlParams()
  }
})

onMounted(() => {
  loadConfigs()

  // 检查路由参数，如果有 addType 参数，自动打开新增对话框
  const addType = route.query.addType as string
  if (addType) {
    openAddDialog(addType)
  }
})
</script>

<style scoped>
.ai-config-page {
  height: 100%;
}

.border-primary {
  border: 2px solid rgb(var(--v-theme-primary)) !important;
}

.config-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.config-info-compact {
  min-height: 60px;
}

.info-item {
  display: flex;
  align-items: flex-start;
}

.description-text {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.4;
  max-height: 2.8em;
}

.text-truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>

<route lang="yaml">
meta:
  layout: default
</route>
