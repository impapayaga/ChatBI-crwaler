<template>
  <v-container fluid class="ai-model-config-container">
    <v-row justify="center">
      <v-col cols="12" md="10" lg="8">
        <v-card>
          <v-card-title class="text-h5">
            <v-icon left>mdi-robot</v-icon>
            大模型配置
          </v-card-title>
          <v-card-subtitle>
            配置您的AI大模型接口信息
          </v-card-subtitle>

          <v-card-text>
            <v-form ref="form" v-model="valid">
              <v-text-field
                v-model="config.configName"
                label="配置名称"
                prepend-icon="mdi-tag"
                :rules="nameRules"
                required
                class="mb-4"
              ></v-text-field>

              <v-select
                v-model="config.modelType"
                :items="modelTypeOptions"
                item-title="name"
                item-value="value"
                label="模型类型"
                prepend-icon="mdi-format-list-bulleted-type"
                required
                class="mb-4"
              ></v-select>

              <v-select
                v-model="selectedProvider"
                :items="providerOptions"
                item-title="name"
                item-value="value"
                label="选择模型提供商"
                prepend-icon="mdi-cloud"
                @update:model-value="onProviderChange"
                required
                class="mb-4"
              ></v-select>

              <v-text-field
                v-model="config.apiKey"
                label="API Key"
                prepend-icon="mdi-key"
                :type="showApiKey ? 'text' : 'password'"
                :append-inner-icon="showApiKey ? 'mdi-eye' : 'mdi-eye-off'"
                @click:append-inner="showApiKey = !showApiKey"
                :rules="apiKeyRules"
                class="mb-4"
              ></v-text-field>

              <v-text-field
                v-model="config.apiUrl"
                label="API 地址"
                prepend-icon="mdi-web"
                :rules="urlRules"
                required
                class="mb-4"
              ></v-text-field>

              <v-text-field
                v-model="config.modelName"
                label="模型名称"
                prepend-icon="mdi-brain"
                :rules="modelRules"
                required
                class="mb-4"
              ></v-text-field>

              <v-slider
                v-model="temperature"
                label="Temperature"
                min="0"
                max="2"
                step="0.1"
                thumb-label
                prepend-icon="mdi-thermometer"
                class="mb-4"
                @update:model-value="config.temperature = temperature.toFixed(1)"
              ></v-slider>

              <v-text-field
                v-model.number="config.maxTokens"
                label="Max Tokens"
                type="number"
                min="100"
                max="8000"
                prepend-icon="mdi-text-long"
                class="mb-4"
              ></v-text-field>

              <v-textarea
                v-model="config.description"
                label="配置描述"
                prepend-icon="mdi-text"
                rows="2"
                class="mb-4"
              ></v-textarea>

              <v-switch
                v-model="config.isDefault"
                label="设为默认配置"
                color="primary"
                class="mb-2"
              ></v-switch>

              <v-switch
                v-model="config.isActive"
                label="启用此配置"
                color="primary"
                class="mb-4"
              ></v-switch>

              <v-card class="mb-4" outlined>
                <v-card-title class="text-subtitle-1">
                  <v-icon left>mdi-test-tube</v-icon>
                  测试配置
                </v-card-title>
                <v-card-text>
                  <v-textarea
                    v-model="testMessage"
                    label="测试消息"
                    rows="3"
                    placeholder="输入一条测试消息来验证配置是否正确"
                    class="mb-2"
                  ></v-textarea>
                  <v-btn
                    @click="testConnection"
                    :loading="testing"
                    :disabled="!valid || !testMessage"
                    color="info"
                    variant="outlined"
                  >
                    <v-icon left>mdi-lightning-bolt</v-icon>
                    测试连接
                  </v-btn>
                </v-card-text>
              </v-card>

              <v-alert
                v-if="testResult"
                :type="testResult.success ? 'success' : 'error'"
                class="mb-4"
              >
                <div class="font-weight-bold">{{ testResult.success ? '✓ 连接成功' : '✗ 连接失败' }}</div>
                <div class="text-caption">{{ testResult.message }}</div>
                <div v-if="testResult.response" class="text-caption mt-2">
                  <strong>响应:</strong> {{ testResult.response }}
                </div>
              </v-alert>
            </v-form>
          </v-card-text>

          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn
              color="grey"
              variant="text"
              @click="resetForm"
            >
              重置
            </v-btn>
            <v-btn
              color="primary"
              :disabled="!valid"
              :loading="saving"
              @click="saveConfig"
            >
              <v-icon left>mdi-content-save</v-icon>
              保存配置
            </v-btn>
          </v-card-actions>
        </v-card>

        <!-- 已保存的配置列表 -->
        <v-card class="mt-4" v-if="savedConfigs.length > 0">
          <v-card-title class="text-h6">
            <v-icon left>mdi-history</v-icon>
            已保存的配置
          </v-card-title>
          <v-list>
            <v-list-item
              v-for="item in savedConfigs"
              :key="item.id"
              :class="{ 'bg-primary-lighten-5': item.isDefault }"
            >
              <template v-slot:prepend>
                <v-icon :color="item.isActive ? 'success' : 'grey'">
                  {{ item.isDefault ? 'mdi-star' : 'mdi-cog' }}
                </v-icon>
              </template>

              <v-list-item-title>
                {{ item.configName }}
                <v-chip v-if="item.isDefault" size="x-small" color="primary" class="ml-2">默认</v-chip>
                <v-chip v-if="!item.isActive" size="x-small" color="grey" class="ml-2">已禁用</v-chip>
              </v-list-item-title>
              <v-list-item-subtitle>
                {{ item.modelName }} | {{ item.modelType }}
              </v-list-item-subtitle>

              <template v-slot:append>
                <v-btn
                  icon="mdi-pencil"
                  size="small"
                  variant="text"
                  @click="editConfig(item)"
                ></v-btn>
                <v-btn
                  v-if="item.id"
                  icon="mdi-delete"
                  size="small"
                  variant="text"
                  color="error"
                  @click="deleteConfig(item.id)"
                ></v-btn>
              </template>
            </v-list-item>
          </v-list>
        </v-card>
      </v-col>
    </v-row>

    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      :timeout="3000"
    >
      {{ snackbar.message }}
      <template #actions>
        <v-btn
          color="white"
          variant="text"
          @click="snackbar.show = false"
        >
          关闭
        </v-btn>
      </template>
    </v-snackbar>
  </v-container>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import axios from 'axios'

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

interface TestResult {
  success: boolean
  message: string
  response?: string
}

interface SnackbarState {
  show: boolean
  message: string
  color: string
}

const valid = ref(false)
const showApiKey = ref(false)
const selectedProvider = ref('')
const testing = ref(false)
const saving = ref(false)
const testMessage = ref('你好，请介绍一下你自己。')
const currentEditId = ref<number | null>(null)
const temperature = ref(0.7)

// 暂时使用默认用户ID (admin用户)
const currentUserId = ref(1)

const config = reactive<Omit<AIModelConfig, 'id'>>({
  userId: currentUserId.value,
  configName: '',
  modelName: '',
  modelType: 'chat',
  apiUrl: '',
  apiKey: '',
  temperature: '0.7',
  maxTokens: 2000,
  description: '',
  isDefault: false,
  isActive: true
})

const savedConfigs = ref<AIModelConfig[]>([])
const testResult = ref<TestResult | null>(null)

const snackbar = reactive<SnackbarState>({
  show: false,
  message: '',
  color: 'success'
})

const modelTypeOptions = [
  { name: '对话模型 (Chat)', value: 'chat' },
  { name: '生成模型 (Generate)', value: 'generate' },
  { name: '嵌入模型 (Embedding)', value: 'embedding' }
]

const providerOptions = [
  {
    name: '硅基流动 (SiliconFlow)',
    value: 'siliconflow',
    defaultConfig: {
      apiUrl: 'https://api.siliconflow.cn/v1/chat/completions',
      modelName: 'Qwen/Qwen2.5-72B-Instruct'
    }
  },
  {
    name: 'OpenAI GPT',
    value: 'openai',
    defaultConfig: {
      apiUrl: 'https://api.openai.com/v1/chat/completions',
      modelName: 'gpt-3.5-turbo'
    }
  },
  {
    name: 'Deepseek',
    value: 'deepseek',
    defaultConfig: {
      apiUrl: 'https://api.deepseek.com/v1/chat/completions',
      modelName: 'deepseek-chat'
    }
  },
  {
    name: '自定义',
    value: 'custom',
    defaultConfig: {
      apiUrl: '',
      modelName: ''
    }
  }
]

const nameRules = [
  (v: string) => !!v || '配置名称是必填项',
  (v: string) => v.length >= 2 || '配置名称至少2个字符'
]

const apiKeyRules = [
  (v: string) => v.length === 0 || v.length >= 10 || 'API Key 长度至少10位'
]

const urlRules = [
  (v: string) => !!v || 'API 地址是必填项',
  (v: string) => /^https?:\/\/.+/.test(v) || '请输入有效的URL地址'
]

const modelRules = [
  (v: string) => !!v || '模型名称是必填项'
]

const onProviderChange = (value: string) => {
  const option = providerOptions.find(opt => opt.value === value)
  if (option && option.defaultConfig) {
    config.apiUrl = option.defaultConfig.apiUrl
    config.modelName = option.defaultConfig.modelName
  }
  testResult.value = null
}

const testConnection = async () => {
  if (!testMessage.value.trim()) {
    showSnackbar('请输入测试消息', 'warning')
    return
  }

  testing.value = true
  testResult.value = null

  try {
    const response = await axios.post(
      `${import.meta.env.VITE_API_BASE_URL}/api/ai-model-configs/test`,
      null,
      {
        params: {
          api_url: config.apiUrl,
          api_key: config.apiKey,
          model_name: config.modelName,
          temperature: parseFloat(config.temperature),
          max_tokens: config.maxTokens || 2000,
          test_message: testMessage.value
        }
      }
    )

    testResult.value = response.data
  } catch (error: any) {
    testResult.value = {
      success: false,
      message: error.response?.data?.detail || error.message || '连接测试失败'
    }
  } finally {
    testing.value = false
  }
}

const saveConfig = async () => {
  saving.value = true

  try {
    const payload = {
      ...config,
      temperature: config.temperature
    }

    if (currentEditId.value) {
      // 更新现有配置
      await axios.put(
        `${import.meta.env.VITE_API_BASE_URL}/api/ai-model-configs/${currentEditId.value}`,
        payload
      )
      showSnackbar('配置更新成功', 'success')
    } else {
      // 创建新配置
      await axios.post(
        `${import.meta.env.VITE_API_BASE_URL}/api/ai-model-configs`,
        payload
      )
      showSnackbar('配置保存成功', 'success')
    }

    resetForm()
    await loadConfigs()
  } catch (error: any) {
    console.error('保存配置失败:', error)
    const errorDetail = error.response?.data?.detail
    let errorMsg = '保存失败'
    if (Array.isArray(errorDetail)) {
      // Pydantic 验证错误
      errorMsg += ': ' + errorDetail.map((e: any) => `${e.loc.join('.')}: ${e.msg}`).join('; ')
    } else if (typeof errorDetail === 'string') {
      errorMsg += ': ' + errorDetail
    } else if (error.message) {
      errorMsg += ': ' + error.message
    }
    showSnackbar(errorMsg, 'error')
  } finally {
    saving.value = false
  }
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

const editConfig = (item: AIModelConfig) => {
  currentEditId.value = item.id || null
  Object.assign(config, {
    userId: item.userId,
    configName: item.configName,
    modelName: item.modelName,
    modelType: item.modelType,
    apiUrl: item.apiUrl,
    apiKey: item.apiKey || '',
    temperature: item.temperature,
    maxTokens: item.maxTokens,
    description: item.description || '',
    isDefault: item.isDefault,
    isActive: item.isActive
  })
  temperature.value = parseFloat(item.temperature)
  testResult.value = null

  // 滚动到顶部
  window.scrollTo({ top: 0, behavior: 'smooth' })
  showSnackbar('正在编辑配置', 'info')
}

const deleteConfig = async (id: number) => {
  if (!confirm('确定要删除此配置吗？')) {
    return
  }

  try {
    await axios.delete(`${import.meta.env.VITE_API_BASE_URL}/api/ai-model-configs/${id}`)
    showSnackbar('配置删除成功', 'success')
    await loadConfigs()
  } catch (error: any) {
    showSnackbar('删除失败: ' + (error.response?.data?.detail || error.message), 'error')
  }
}

const resetForm = () => {
  currentEditId.value = null
  selectedProvider.value = ''
  Object.assign(config, {
    userId: currentUserId.value,
    configName: '',
    modelName: '',
    modelType: 'chat',
    apiUrl: '',
    apiKey: '',
    temperature: '0.7',
    maxTokens: 2000,
    description: '',
    isDefault: false,
    isActive: true
  })
  temperature.value = 0.7
  testResult.value = null
}

const showSnackbar = (message: string, color: string = 'success') => {
  snackbar.message = message
  snackbar.color = color
  snackbar.show = true
}

onMounted(() => {
  loadConfigs()
})
</script>

<style scoped>
.ai-model-config-container {
  padding: 24px 16px;
  padding-bottom: 48px; /* 额外底部空间 */
}

.v-card {
  margin-bottom: 24px;
}

.v-card:last-child {
  margin-bottom: 0;
}

.bg-primary-lighten-5 {
  background-color: rgba(var(--v-theme-primary), 0.05);
}
</style>
