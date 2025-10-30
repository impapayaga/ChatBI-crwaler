<template>
  <v-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    max-width="900px"
    persistent
    scrollable
  >
    <v-card>
      <v-card-title class="d-flex align-center bg-primary">
        <v-icon class="mr-2">mdi-robot</v-icon>
        <span>{{ isEdit ? '编辑 AI 模型配置' : '新增 AI 模型配置' }}</span>
        <v-spacer></v-spacer>
        <v-btn
          icon="mdi-close"
          variant="text"
          @click="closeDialog"
        ></v-btn>
      </v-card-title>

      <v-card-text class="pa-6">
        <v-form ref="formRef" v-model="valid">
          <v-text-field
            v-model="formData.configName"
            label="配置名称"
            prepend-icon="mdi-tag"
            :rules="nameRules"
            required
            class="mb-4"
          ></v-text-field>

          <v-select
            v-model="formData.modelType"
            :items="modelTypeOptions"
            item-title="name"
            item-value="value"
            label="模型类型"
            prepend-icon="mdi-format-list-bulleted-type"
            required
            class="mb-2"
          ></v-select>

          <v-alert
            v-if="formData.modelType === 'embedding'"
            type="info"
            density="compact"
            class="mb-4 text-caption"
          >
            Embedding 模型用于将文本转换为向量表示，常用于语义搜索、文本相似度计算等场景。
          </v-alert>

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
            v-model="formData.apiKey"
            label="API Key"
            prepend-icon="mdi-key"
            :type="showApiKey ? 'text' : 'password'"
            :append-inner-icon="showApiKey ? 'mdi-eye' : 'mdi-eye-off'"
            @click:append-inner="showApiKey = !showApiKey"
            :rules="apiKeyRules"
            class="mb-4"
          ></v-text-field>

          <v-text-field
            v-model="formData.apiUrl"
            label="API 地址"
            prepend-icon="mdi-web"
            :rules="urlRules"
            required
            class="mb-4"
          ></v-text-field>

          <v-text-field
            v-model="formData.modelName"
            label="模型名称"
            prepend-icon="mdi-brain"
            :rules="modelRules"
            :hint="formData.modelType === 'embedding' ? '例如: BAAI/bge-large-zh-v1.5, text-embedding-3-small' : '例如: Qwen/Qwen2.5-72B-Instruct, gpt-3.5-turbo'"
            persistent-hint
            required
            class="mb-4"
          ></v-text-field>

          <v-slider
            v-if="formData.modelType !== 'embedding'"
            v-model="temperature"
            label="Temperature"
            min="0"
            max="2"
            step="0.1"
            thumb-label
            prepend-icon="mdi-thermometer"
            class="mb-4"
          ></v-slider>

          <v-text-field
            v-if="formData.modelType !== 'embedding'"
            v-model.number="formData.maxTokens"
            label="Max Tokens"
            type="number"
            min="100"
            max="8000"
            prepend-icon="mdi-text-long"
            class="mb-4"
          ></v-text-field>

          <v-textarea
            v-model="formData.description"
            label="配置描述"
            prepend-icon="mdi-text"
            rows="2"
            class="mb-4"
          ></v-textarea>

          <v-switch
            v-model="formData.isDefault"
            label="设为默认配置"
            color="primary"
            class="mb-2"
          ></v-switch>

          <v-switch
            v-model="formData.isActive"
            label="启用此配置"
            color="primary"
            class="mb-4"
          ></v-switch>

          <v-expansion-panels>
            <v-expansion-panel>
              <v-expansion-panel-title>
                <v-icon class="mr-2">mdi-test-tube</v-icon>
                测试配置
                <v-chip
                  v-if="testResult?.success"
                  color="success"
                  size="x-small"
                  class="ml-2"
                >
                  已通过
                </v-chip>
                <v-chip
                  v-else
                  color="warning"
                  size="x-small"
                  class="ml-2"
                >
                  待测试
                </v-chip>
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <v-alert
                  type="warning"
                  density="compact"
                  class="mb-3 text-caption"
                >
                  保存前必须先测试连接并确保通过
                </v-alert>

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
                  <v-icon start>mdi-lightning-bolt</v-icon>
                  测试连接
                </v-btn>

                <v-alert
                  v-if="testResult"
                  :type="testResult.success ? 'success' : 'error'"
                  class="mt-4"
                >
                  <div class="font-weight-bold">{{ testResult.success ? '✓ 连接成功' : '✗ 连接失败' }}</div>
                  <div class="text-caption">{{ testResult.message }}</div>
                  <div v-if="testResult.response" class="text-caption mt-2">
                    <strong>响应:</strong> {{ testResult.response }}
                  </div>
                  <div v-if="testResult.responseTime" class="text-caption mt-1">
                    <strong>响应时间:</strong> {{ testResult.responseTime }} ms
                  </div>
                </v-alert>
              </v-expansion-panel-text>
            </v-expansion-panel>
          </v-expansion-panels>
        </v-form>
      </v-card-text>

      <v-card-actions class="px-6 pb-4">
        <v-spacer></v-spacer>
        <v-btn
          color="grey"
          variant="text"
          @click="closeDialog"
        >
          取消
        </v-btn>
        <v-btn
          color="primary"
          :disabled="!valid || !testResult?.success"
          :loading="saving"
          @click="saveConfig"
        >
          <v-icon start>mdi-content-save</v-icon>
          保存配置
        </v-btn>
      </v-card-actions>
    </v-card>

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
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed, nextTick } from 'vue'
import axios from 'axios'

interface AIModelConfig {
  id?: number
  userId: number
  configName: string
  provider?: string
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
  responseTime?: number
}

interface SnackbarState {
  show: boolean
  message: string
  color: string
}

interface Props {
  modelValue: boolean
  config: AIModelConfig | null
  isEdit: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'saved'): void
}>()

const formRef = ref()
const valid = ref(false)
const showApiKey = ref(false)
const selectedProvider = ref('')
const testing = ref(false)
const saving = ref(false)
const testMessage = ref('你好，请介绍一下你自己。')
const temperature = ref(0.7)
const currentUserId = ref(1)

const formData = reactive<Omit<AIModelConfig, 'id'>>({
  userId: currentUserId.value,
  configName: '',
  provider: '',
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

const providerOptions = computed(() => {
  const modelType = formData.modelType

  if (modelType === 'embedding') {
    return [
      {
        name: '硅基流动 (SiliconFlow)',
        value: 'siliconflow',
        defaultConfig: {
          apiUrl: 'https://api.siliconflow.cn/v1/embeddings'
        }
      },
      {
        name: 'OpenAI',
        value: 'openai',
        defaultConfig: {
          apiUrl: 'https://api.openai.com/v1/embeddings'
        }
      },
      {
        name: 'Deepseek',
        value: 'deepseek',
        defaultConfig: {
          apiUrl: 'https://api.deepseek.com/v1/embeddings'
        }
      },
      {
        name: '自定义',
        value: 'custom',
        defaultConfig: {
          apiUrl: ''
        }
      }
    ]
  } else {
    // Chat/Generate 模型
    return [
      {
        name: '硅基流动 (SiliconFlow)',
        value: 'siliconflow',
        defaultConfig: {
          apiUrl: 'https://api.siliconflow.cn/v1/chat/completions'
        }
      },
      {
        name: 'OpenAI GPT',
        value: 'openai',
        defaultConfig: {
          apiUrl: 'https://api.openai.com/v1/chat/completions'
        }
      },
      {
        name: 'Deepseek',
        value: 'deepseek',
        defaultConfig: {
          apiUrl: 'https://api.deepseek.com/v1/chat/completions'
        }
      },
      {
        name: '自定义',
        value: 'custom',
        defaultConfig: {
          apiUrl: ''
        }
      }
    ]
  }
})

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

// 监听 temperature 变化
watch(temperature, (val) => {
  formData.temperature = val.toFixed(1)
})

// 监听模型类型变化，更新测试消息和重置 provider
watch(() => formData.modelType, (newType) => {
  if (newType === 'embedding') {
    testMessage.value = '测试 Embedding 向量生成'
  } else {
    testMessage.value = '你好，请介绍一下你自己。'
  }
  // 重置 provider 以触发新的默认配置
  selectedProvider.value = ''
  formData.provider = ''
  testResult.value = null
})

// 监听对话框打开，填充数据
watch(() => props.modelValue, async (newVal) => {
  if (newVal) {
    if (props.config) {
      // 编辑模式，填充数据
      // 先设置 modelType，这样 providerOptions 会立即更新
      formData.modelType = props.config.modelType

      // 等待下一个 tick，确保 providerOptions 已经根据新的 modelType 更新
      await nextTick()

      // 然后再填充其他数据
      Object.assign(formData, {
        userId: props.config.userId,
        configName: props.config.configName,
        provider: props.config.provider || '',
        modelName: props.config.modelName,
        apiUrl: props.config.apiUrl,
        apiKey: props.config.apiKey || '',
        temperature: props.config.temperature,
        maxTokens: props.config.maxTokens,
        description: props.config.description || '',
        isDefault: props.config.isDefault,
        isActive: props.config.isActive
      })
      // 同步 selectedProvider 以便在下拉框中显示
      selectedProvider.value = props.config.provider || ''
      temperature.value = parseFloat(props.config.temperature)
    } else {
      // 新增模式，重置表单
      resetForm()
    }
    testResult.value = null
  }
})

const onProviderChange = (value: string) => {
  const option = providerOptions.value.find(opt => opt.value === value)
  if (option && option.defaultConfig) {
    formData.provider = value
    formData.apiUrl = option.defaultConfig.apiUrl
    // 不自动填充模型名称，让用户自己输入
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
          api_url: formData.apiUrl,
          api_key: formData.apiKey,
          model_name: formData.modelName,
          model_type: formData.modelType,
          temperature: parseFloat(formData.temperature),
          max_tokens: formData.maxTokens || 2000,
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
  if (!formRef.value) return

  const { valid: isValid } = await formRef.value.validate()
  if (!isValid) return

  // 检查是否已经通过测试
  if (!testResult.value || !testResult.value.success) {
    showSnackbar('请先测试连接并确保通过后再保存', 'warning')
    return
  }

  saving.value = true

  try {
    const payload = {
      ...formData,
      temperature: formData.temperature
    }

    if (props.isEdit && props.config?.id) {
      // 更新现有配置
      await axios.put(
        `${import.meta.env.VITE_API_BASE_URL}/api/ai-model-configs/${props.config.id}`,
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

    emit('saved')
  } catch (error: any) {
    console.error('保存配置失败:', error)
    const errorDetail = error.response?.data?.detail
    let errorMsg = '保存失败'
    if (Array.isArray(errorDetail)) {
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

const resetForm = () => {
  selectedProvider.value = ''
  Object.assign(formData, {
    userId: currentUserId.value,
    configName: '',
    provider: '',
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
  formRef.value?.resetValidation()
}

const closeDialog = () => {
  emit('update:modelValue', false)
}

const showSnackbar = (message: string, color: string = 'success') => {
  snackbar.message = message
  snackbar.color = color
  snackbar.show = true
}
</script>

<style scoped>
.bg-primary {
  background-color: rgb(var(--v-theme-primary));
  color: rgb(var(--v-theme-on-primary));
}
</style>
