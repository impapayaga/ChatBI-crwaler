<template>
  <div class="home-container">
    <!-- 初始状态 - 欢迎页面 -->
    <div v-if="!hasData && !isLoading && !hasStartedChat" class="initial-view">
      <!-- 顶部工具栏 - 透明区域 (初始状态) -->
      <div class="top-toolbar">
        <div class="toolbar-left">
          <ConversationHistory ref="conversationHistoryRef" @select-conversation="handleSelectConversation"
            @new-conversation="handleNewChat" />
          <v-btn icon size="small" variant="text" class="new-chat-btn" @click="handleNewChat">
            <v-icon>mdi-plus</v-icon>
          </v-btn>
          <ModelSelector />
        </div>
        <div class="toolbar-right">
          <DatasetList ref="datasetListRef" @select-dataset="handleDatasetSelect" />
        </div>
      </div>

      <!-- 居中内容容器 -->
      <div class="center-content">
        <!-- 欢迎卡片 -->
        <div class="welcome-section">
          <v-card title="欢迎使用北京市教育考试院智能问数系统" subtitle="这是一个实验环境，回答可能有误，请注意甄别!">
            <template v-slot:prepend>
              <v-icon color="primary" size="large">mdi-message-text</v-icon>
            </template>
          </v-card>
        </div>

        <!-- 输入框 -->
        <div class="input-center-section">
          <div class="input-center-wrapper">
            <ChatInput v-model="inputValue" :disabled="isLoading" :rows="2" tool-menu-position="bottom"
              :selected-datasets="selectedDatasets" @send="sendRequest" @tool-select="handleToolSelect"
              @upload-click="uploadDialogVisible = true" @remove-dataset="handleRemoveDataset" @preview-dataset="handlePreviewDataset" />
          </div>
        </div>
      </div>

    </div>

    <!-- 对话状态 - 内容区域可滚动 + 输入框固定底部 -->
    <div v-else class="conversation-view">
      <!-- 顶部工具栏 - 透明区域 -->
      <div class="top-toolbar-conversation">
        <div class="toolbar-left">
          <ConversationHistory @select-conversation="handleSelectConversation" @new-conversation="handleNewChat" />
          <v-btn icon size="small" variant="text" class="new-chat-btn" @click="handleNewChat">
            <v-icon>mdi-plus</v-icon>
          </v-btn>
          <ModelSelector />
        </div>
        <div class="toolbar-right">
          <DatasetList ref="datasetListRef" @select-dataset="handleDatasetSelect" />
        </div>
      </div>

      <!-- 内容区域 - 可滚动 -->
      <div class="content-area" ref="contentArea">
        <div class="content-wrapper">
          <!-- 统一消息显示区域 -->
          <div v-if="hasStartedChat || hasData" class="messages-list">
            <!-- 显示所有消息（历史+临时） -->
            <template v-if="displayMessages.length > 0">
              <template v-for="(message, index) in displayMessages" :key="message.id || `temp-${index}`">
                <!-- 用户消息 -->
                <div v-if="message.role === 'user'" class="message-item user-message">
                  <div class="user-bubble">
                    <p class="text-sm">{{ message.content }}</p>
                  </div>
                </div>

                <!-- AI助手消息 -->
                <div v-else-if="message.role === 'assistant'" class="message-item ai-message">
                  <!-- 处理步骤指示器(仅在加载中显示) -->
                  <ProcessingSteps v-if="isLoading && showProcessingSteps" :current-step="currentProcessingStep"
                    :error="processingError" class="mb-4" />

                  <!-- 图表展示 -->
                  <v-card v-if="message.chart_data" class="mb-4">
                    <!-- 图表类型切换按钮 -->
                    <v-card-title class="d-flex justify-space-between align-center">
                      <span>数据可视化</span>
                      <div class="chart-controls">
                        <v-btn-toggle v-model="message.chart_data.display_mode" mandatory 
                          variant="flat" density="compact" class="chart-toggle-group">
                          <v-btn value="chart" size="small" class="chart-toggle-btn">
                            <v-icon size="16">mdi-chart-bar</v-icon>
                            <span class="ml-1">图表</span>
                          </v-btn>
                          <v-btn value="table" size="small" class="chart-toggle-btn">
                            <v-icon size="16">mdi-table</v-icon>
                            <span class="ml-1">表格</span>
                          </v-btn>
                        </v-btn-toggle>
                      </div>
                    </v-card-title>
                    <v-card-text>
                      <!-- 图表视图 -->
                      <div v-if="message.chart_data.display_mode === 'chart' || !message.chart_data.display_mode">
                        <!-- 检查是否有有效的图表配置 -->
                        <div v-if="Object.keys(buildChartOptions(message.chart_data)).length > 0">
                          <EChart :options="buildChartOptions(message.chart_data)" :loading="false"
                            v-model="message.chart_data.chart_type" class="chart"
                            @update:modelValue="handleChartTypeChange(message, $event)" />
                        </div>
                        <!-- 如果无法生成图表配置，显示提示信息 -->
                        <div v-else class="text-center py-8 text-gray-500">
                          <v-icon size="48" class="mb-2">mdi-chart-bar</v-icon>
                          <p>此数据暂不支持图表展示，请切换到表格视图</p>
                        </div>
                      </div>
                      <!-- 表格视图 -->
                      <div v-else-if="message.chart_data.display_mode === 'table'">
                        <DataTable :data="message.chart_data.data || []" :items-per-page="10" />
                      </div>
                    </v-card-text>
                  </v-card>

                  <!-- 洞察分析卡片 - 加载中即显示（骨架屏/流式内容） -->
                  <v-card v-if="message.chart_data && isAnalysisLoading" class="mb-4 insight-analysis-card">
                    <v-card-title class="d-flex align-center">
                      <v-icon color="primary" class="mr-2">mdi-lightbulb-on</v-icon>
                      <span>数据洞察分析</span>
                    </v-card-title>
                    <v-card-text>
                      <!-- 骨架屏加载状态 -->
                      <div v-if="isAnalysisLoading && !streamingAnalysis" class="insight-skeleton">
                        <v-skeleton-loader type="paragraph" class="mb-3"></v-skeleton-loader>
                        <v-skeleton-loader type="sentences" class="mb-3"></v-skeleton-loader>
                        <v-skeleton-loader type="paragraph"></v-skeleton-loader>
                      </div>

                      <!-- 流式输出内容 - 打字机效果 -->
                      <div v-else-if="streamingAnalysis" class="streaming-content">
                        <div class="prose dark:prose-invert max-w-none">
                          <MarkdownRenderer :content="streamingAnalysis" />
                        </div>
                        <!-- 打字机光标效果 -->
                        <span v-if="!isAnalysisComplete" class="typing-cursor">|</span>
                      </div>
                    </v-card-text>
                  </v-card>

                  <!-- 历史对话中的洞察分析内容 - 仅在非流式状态时显示 -->
                  <v-card v-else-if="message.role === 'assistant' && message.content && message.content.includes('## 📊 数据洞察分析') && !isAnalysisLoading" class="mb-4 insight-analysis-card">
                    <v-card-title class="d-flex align-center">
                      <v-icon color="primary" class="mr-2">mdi-lightbulb-on</v-icon>
                      <span>数据洞察分析</span>
                    </v-card-title>
                    <v-card-text>
                      <div class="prose dark:prose-invert max-w-none">
                        <MarkdownRenderer :content="message.content" />
                      </div>
                    </v-card-text>
                  </v-card>

                  <!-- AI回复内容 - 排除洞察分析内容 -->
                  <v-card v-if="message.content && !message.content.includes('## 📊 数据洞察分析')" class="mb-4">
                    <v-card-text>
                      <div class="prose dark:prose-invert max-w-none">
                        <MarkdownRenderer :content="message.content" />
                      </div>
                    </v-card-text>
                  </v-card>

                  <!-- 操作按钮和时间信息 -->
                  <div class="action-bar">
                    <div class="action-buttons">
                      <v-btn icon size="small" variant="text" class="action-icon-btn">
                        <v-icon size="18">mdi-refresh</v-icon>
                      </v-btn>
                      <v-btn icon size="small" variant="text" class="action-icon-btn">
                        <v-icon size="18">mdi-content-copy</v-icon>
                      </v-btn>
                      <v-btn icon size="small" variant="text" class="action-icon-btn">
                        <v-icon size="18">mdi-thumb-up-outline</v-icon>
                      </v-btn>
                      <v-btn icon size="small" variant="text" class="action-icon-btn">
                        <v-icon size="18">mdi-thumb-down-outline</v-icon>
                      </v-btn>
                    </div>
                    <!-- 右侧时间信息区域 -->
                    <div class="time-info">
                      <!-- AI回复时间 -->
                      <div class="message-time">
                        <v-icon size="16">mdi-calendar-clock</v-icon>
                        <span>{{ formatMessageTime(message.created_at) }}</span>
                      </div>
                      <!-- 响应时间 -->
                      <div v-if="message.response_time" class="response-time">
                        <v-icon size="16">mdi-clock-outline</v-icon>
                        <span>{{ (message.response_time / 1000).toFixed(1) }}s</span>
                      </div>
                    </div>
                  </div>
                </div>
              </template>
            </template>
          </div>
        </div>
      </div>

      <!-- 滚动到底部按钮 - 固定在输入框上方 -->
      <Transition name="fade">
        <div v-if="showScrollToBottom" class="scroll-to-bottom-container">
          <v-btn color="primary" size="small" elevation="2" class="scroll-to-bottom-btn" @click="scrollToBottom(true)">
            <v-icon size="18">mdi-arrow-down</v-icon>
            <span class="ml-1">滚动到最新</span>
          </v-btn>
        </div>
      </Transition>

      <!-- 输入区域 - 固定在底部 -->
      <div class="input-bar">
        <div class="input-wrapper">
          <ChatInput v-model="inputValue" :disabled="isLoading" :rows="1" tool-menu-position="top"
            :selected-datasets="selectedDatasets" @send="sendRequest" @tool-select="handleToolSelect"
            @upload-click="uploadDialogVisible = true" @remove-dataset="handleRemoveDataset" @preview-dataset="handlePreviewDataset" />
        </div>
      </div>

      <!-- 底部免责声明 - 透明 -->
      <div class="disclaimer-footer">
        <span class="disclaimer-text">AI 生成内容可能不准确，请仔细核实。</span>
      </div>
    </div>

    <!-- 文件上传对话框 -->
    <FileUploadDialog v-model="uploadDialogVisible" @upload-success="handleUploadSuccess" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, onUnmounted, watch } from 'vue'
import axios from 'axios'
import EChart from './EChart.vue'
import MarkdownRenderer from './MarkdownRenderer.vue'
import ChatInput from './ChatInput.vue'
import ConversationHistory from './ConversationHistory.vue'
import ModelSelector from './ModelSelector.vue'
import DatasetList from './DatasetList.vue'
import FileUploadDialog from './FileUploadDialog.vue'
import ProcessingSteps from './ProcessingSteps.vue'
import DataTable from './DataTable.vue'

const inputValue = ref('')
const lastUserMessage = ref('')  // 保存最后一条用户消息
const hasData = ref(false)
const isLoading = ref(false)
const hasStartedChat = ref(false)
const hasChartData = ref(false)  // 新增: 是否有图表数据
const chartOptions = ref({})
const chartType = ref<'bar' | 'line' | 'pie' | 'doughnut'>('bar')
const responseTime = ref<number | null>(null)
const insightAnalysis = ref<string | null>(null)
const streamingAnalysis = ref<string>('')
const isAnalysisLoading = ref(false)
const isAnalysisComplete = ref(false)
const uploadDialogVisible = ref(false)
const datasetListRef = ref()
const conversationHistoryRef = ref()
const selectedDatasets = ref<Dataset[]>([])

// 处理步骤相关
const currentProcessingStep = ref<string>('')
const processingError = ref<string>('')
const showProcessingSteps = ref(false)

// 消息列表相关
interface Message {
  id: number
  role: 'user' | 'assistant'
  content: string
  chart_data?: any
  chart_type?: string
  response_time?: number
  created_at: string
  insight_task_id?: string  // 洞察分析任务ID
}

const messageList = ref<Message[]>([])  // 存储完整的消息列表
const currentConversationId = ref<number | null>(null)  // 当前会话ID
const isStreaming = ref(false)  // 是否正在流式输出
const tempUserMessage = ref<Message | null>(null)  // 临时用户消息
const tempAiMessage = ref<Message | null>(null)  // 临时AI消息（用于流式更新）

// 合并历史消息和临时消息用于显示
const displayMessages = computed(() => {
  const messages = [...messageList.value]

  // 如果有临时消息，添加到末尾
  if (tempUserMessage.value) {
    messages.push(tempUserMessage.value)
  }
  if (tempAiMessage.value) {
    messages.push(tempAiMessage.value)
  }

  return messages
})

// 滚动相关
const contentArea = ref<HTMLElement>()
const showScrollToBottom = ref(false)  // 是否显示滚动到底部按钮

interface Dataset {
  id: string
  name: string
  logical_name?: string
  row_count: number
  column_count: number
}

interface RefinedData {
  x_axis: string
  y_axes: string[]
  scale: string
  unit: string
}

const sendRequest = async () => {
  if (!inputValue.value) {
    alert('请输入问题')
    return
  }

  // 保存用户输入(发送前)
  const userQuestion = inputValue.value
  lastUserMessage.value = userQuestion  // 保存到lastUserMessage用于显示

  // 清空输入框 - 使用多次确保清除
  inputValue.value = ''

  // 使用 nextTick 确保 DOM 更新后再次清空
  await nextTick()
  inputValue.value = ''

  // 如果当前没有会话ID，先创建新会话（只在第一次发送消息时创建）
  if (!currentConversationId.value) {
    const newConvId = await createNewConversation()
    if (!newConvId) {
      alert('创建会话失败，请重试')
      return
    }
    console.log('首次发送消息，已创建新会话:', newConvId)
  } else {
    console.log('使用现有会话:', currentConversationId.value)
  }

  // 创建临时用户消息立即显示
  tempUserMessage.value = {
    id: Date.now(),  // 临时ID
    role: 'user',
    content: userQuestion,
    created_at: new Date().toISOString()
  }

  // 创建临时AI消息（初始为空）
  tempAiMessage.value = {
    id: Date.now() + 1,  // 临时ID
    role: 'assistant',
    content: '',
    created_at: new Date().toISOString()
  }

  // 标记对话已开始
  hasStartedChat.value = true
  isStreaming.value = true

  // 重置当前消息的显示状态（但不清空 currentConversationId）
  isLoading.value = true
  hasData.value = false
  hasChartData.value = false  // 重置图表数据标志
  responseTime.value = null
  insightAnalysis.value = null
  streamingAnalysis.value = ''
  isAnalysisLoading.value = false
  isAnalysisComplete.value = false
  const startTime = performance.now()

  // 重置处理步骤
  currentProcessingStep.value = ''
  processingError.value = ''
  showProcessingSteps.value = false

  // 判断是否进入智慧问数模式
  const isSmartQueryMode = selectedDatasets.value.length > 0

  console.log(`模式: ${isSmartQueryMode ? '智慧问数' : '普通对话'}`)
  console.log('已选择数据集:', selectedDatasets.value)

  try {
    // 如果是普通对话模式(未选择数据集),直接调用流式AI对话
    if (!isSmartQueryMode) {
      console.log('普通对话模式 - 调用流式AI对话')
      hasData.value = true
      hasChartData.value = false  // 普通对话模式不显示图表
      await fetchStreamingChatResponse(userQuestion)
      const endTime = performance.now()
      responseTime.value = Math.round(endTime - startTime)
      isLoading.value = false
      return
    }

    // 智慧问数模式 - 显示处理步骤并调用图表生成API
    console.log('智慧问数模式 - 调用图表生成API')
    showProcessingSteps.value = true

    // 初始化进度状态
    currentProcessingStep.value = 'intent'
    processingError.value = ''

    const response = await axios.post(`${import.meta.env.VITE_API_BASE_URL}/api/generate_chart`, {
      user_input: userQuestion,
      user_id: 1,  // 临时使用固定用户ID
      dataset_ids: selectedDatasets.value.map((d: any) => d.id)  // 传递用户选中的数据集ID列表
    })

    console.log('Response:', response.data)
    const responseData = response.data

    // 获取任务ID并订阅进度更新
    const taskId = responseData.task_id
    if (taskId) {
      subscribeToProgress(taskId)
    }

    // 检查是否有错误标识
    if (responseData.is_error || responseData.error) {
      throw new Error(responseData.message || responseData.error || '未知错误')
    }

    // 检查响应类型
    if (responseData.type === 'text') {
      // 处理文本响应(闲聊等)
      console.log('收到文本响应:', responseData.message)
      hasData.value = true
      streamingAnalysis.value = responseData.message
      showProcessingSteps.value = false
      return
    }

    const { data, refined_data, chart_type, visualization_type, insight_task_id } = responseData

    if (data && data.length > 0) {
      hasData.value = true
      showProcessingSteps.value = false  // 隐藏处理步骤，显示结果

      // 根据可视化类型进行不同处理
      if (visualization_type === 'table') {
        // 表格类型：不显示图表，只显示数据
        hasChartData.value = false
        console.log('数据类型为table，跳过图表渲染')
        
        // 将表格数据添加到临时AI消息
        if (tempAiMessage.value) {
          tempAiMessage.value.chart_data = {
            data: data,
            refined_data: null,
            chart_type: null,
            display_mode: 'table'  // 表格显示模式
          }

          // 保存洞察分析任务ID
          if (insight_task_id) {
            tempAiMessage.value.insight_task_id = insight_task_id
            console.log('保存洞察分析任务ID:', insight_task_id)
          }
        }
      } else {
        // 图表类型：显示图表
        hasChartData.value = true
        
        // 检查refined_data是否存在
        if (!refined_data || !refined_data.x_axis || !refined_data.y_axes) {
          console.warn('refined_data不完整，使用自动推断构建图表')
          // 使用buildChartOptions的自动推断逻辑
          chartOptions.value = buildChartOptions({
            data: data,
            refined_data: null,
            chart_type: chart_type || 'bar',
            visualization_type: 'chart'
          })
          chartType.value = chart_type || 'bar'
        } else {
          // 使用refined_data构建图表
          const refinedData = refined_data as RefinedData
          console.log('Refined Data:', refinedData)

          const xAxisData = data.map((item: any) => item[refinedData.x_axis])
          console.log('xAxisData:', xAxisData)

          const seriesData = refined_data.y_axes.map((yAxis: string) => {
            return {
              name: yAxis,
              type: chart_type || 'bar',
              data: data.map((item: any) => item[yAxis]),
              stack: chart_type === 'bar' ? 'x' : undefined,
              areaStyle: chart_type === 'line' ? {} : undefined
            }
          })
          console.log('Series Data:', seriesData)

          chartOptions.value = {
            xAxis: {
              type: 'category',
              data: xAxisData,
            },
            yAxis: {
              type: 'value',
            },
            series: seriesData,
            legend: {
              data: refined_data.y_axes
            },
            tooltip: {
              trigger: 'axis'
            }
          }
          chartType.value = chart_type || 'bar'
        }
        
        console.log('Chart Options:', chartOptions.value)
        console.log('Chart Type:', chartType.value)

        // 将图表数据添加到临时AI消息
        if (tempAiMessage.value) {
          tempAiMessage.value.chart_data = {
            data: data,
            refined_data: refined_data,
            chart_type: chart_type,
            display_mode: 'chart'  // 图表显示模式
          }

          // 保存洞察分析任务ID
          if (insight_task_id) {
            tempAiMessage.value.insight_task_id = insight_task_id
            console.log('保存洞察分析任务ID:', insight_task_id)
          }
        }
      }

      // 如果有任务ID，使用轮询方式获取洞察分析；否则使用流式方式
      if (insight_task_id) {
        console.log('使用任务ID轮询方式获取洞察分析:', insight_task_id)
        pollInsightAnalysisTask(insight_task_id)
      } else {
        // 开始流式洞察分析（兼容旧版本）
        console.log('使用流式方式获取洞察分析...')
        fetchStreamingInsightAnalysis()
      }
    } else {
      hasData.value = false
      console.warn('未获取到图表数据')
    }
  } catch (error: any) {
    console.error('请求失败', error)
    hasData.value = false

    // 提取详细错误信息
    let errorTitle = '生成图表失败'
    let errorDetail = ''
    let errorSuggestions: string[] = []

    if (error.response?.data) {
      const errorData = error.response.data

      // 使用后端返回的结构化错误信息
      if (errorData.title) {
        errorTitle = errorData.title
      } else {
        errorTitle = errorData.error || errorTitle
      }

      errorDetail = errorData.message || errorData.detail || ''

      // 获取后端返回的建议
      if (errorData.suggestions && Array.isArray(errorData.suggestions)) {
        errorSuggestions = errorData.suggestions
      }

      // 处理后端返回的具体错误类型
      if (errorData.error_type) {
        switch (errorData.error_type) {
          case 'column_not_found':
            if (!errorData.title) errorTitle = '数据列未找到'
            break
          case 'connection_error':
            if (!errorData.title) errorTitle = '网络连接错误'
            break
          case 'sql_error':
            if (!errorData.title) errorTitle = '数据查询错误'
            break
          case 'ai_model_error':
            if (!errorData.title) errorTitle = 'AI服务错误'
            break
          case 'dataset_error':
            if (!errorData.title) errorTitle = '数据集处理错误'
            break
          case 'permission_error':
            if (!errorData.title) errorTitle = '权限不足'
            break
        }
      }

      // 兼容旧的错误类型处理
      if (errorData.type === 'validation_error') {
        errorTitle = '数据验证错误'
      } else if (errorData.type === 'database_error') {
        errorTitle = '数据库查询错误'
      } else if (errorData.type === 'ai_model_error') {
        errorTitle = 'AI模型调用错误'
      }
    } else if (error.message) {
      errorDetail = error.message
    } else {
      errorDetail = '网络连接失败，请检查您的网络设置'
    }

    // 标记处理步骤错误
    processingError.value = errorDetail
    showProcessingSteps.value = true

    // 在对话区域显示友好的错误消息
    let friendlyErrorMessage = `### ❌ ${errorTitle}\n\n`

    if (errorDetail) {
      friendlyErrorMessage += `${errorDetail}\n\n`
    }

    // 显示建议操作
    if (errorSuggestions.length > 0) {
      friendlyErrorMessage += '**建议操作：**\n'
      errorSuggestions.forEach((suggestion, index) => {
        friendlyErrorMessage += `${index + 1}. ${suggestion}\n`
      })
    } else {
      // 如果没有后端建议，使用默认建议
      if (errorDetail.includes('Referenced column') && errorDetail.includes('not found')) {
        friendlyErrorMessage += '**建议操作：**\n'
        friendlyErrorMessage += '1. 请稍后重试您的查询\n'
        friendlyErrorMessage += '2. 或者尝试重新上传数据文件\n'
        friendlyErrorMessage += '3. 确保数据文件中的列名不包含特殊符号'
      } else if (errorDetail.includes('网络') || errorDetail.includes('连接')) {
        friendlyErrorMessage += '网络连接出现问题，请检查您的网络连接后重试。'
      } else if (errorDetail.includes('模型') || errorDetail.includes('AI')) {
        friendlyErrorMessage += 'AI服务暂时不可用，请稍后重试。'
      } else {
        friendlyErrorMessage += '**建议操作：**\n'
        friendlyErrorMessage += '1. 检查您的输入是否正确\n'
        friendlyErrorMessage += '2. 稍后重试\n'
        friendlyErrorMessage += '3. 如果问题持续存在，请联系管理员'
      }
    }

    streamingAnalysis.value = friendlyErrorMessage
    hasData.value = true  // 显示错误消息区域

    // 更新临时AI消息以显示错误
    if (tempAiMessage.value) {
      tempAiMessage.value.content = friendlyErrorMessage
    }

  } finally {
    const endTime = performance.now()
    responseTime.value = Math.round(endTime - startTime)
    isLoading.value = false
  }
}

const fetchInsightAnalysis = async () => {
  try {
    const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/insight_analysis`, {
      params: { user_input: inputValue.value }
    })
    insightAnalysis.value = response.data.insight_analysis
  } catch (error) {
    console.error('获取洞察分析失败', error)
  }
}

// 轮询洞察分析任务状态
const pollInsightAnalysisTask = async (taskId: string) => {
  console.log('开始轮询洞察分析任务:', taskId)
  isAnalysisLoading.value = true
  isAnalysisComplete.value = false

  const maxAttempts = 60 // 最多轮询60次 (5分钟)
  const pollInterval = 5000 // 每5秒轮询一次
  let attempts = 0

  const poll = async () => {
    try {
      attempts++
      console.log(`轮询洞察分析任务状态 (${attempts}/${maxAttempts}):`, taskId)

      const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/insight_task/${taskId}`)
      const { status, result, error } = response.data

      console.log('任务状态:', status, '结果:', result ? '已获取' : '无', '错误:', error)

      if (status === 'completed' && result) {
        // 任务完成，重新加载对话消息以获取保存到数据库的洞察分析
        isAnalysisLoading.value = false
        isAnalysisComplete.value = true
        console.log('洞察分析完成:', result)
        
        // 重新加载对话消息以获取保存到数据库的洞察分析
        if (currentConversationId.value) {
          console.log('重新加载对话消息以获取洞察分析...')
          await reloadConversationMessages()
          // 清空流式分析内容，确保历史洞察分析能正确显示
          streamingAnalysis.value = ''
        }
        return
      } else if (status === 'failed') {
        // 任务失败
        console.error('洞察分析任务失败:', error)
        isAnalysisLoading.value = false
        isAnalysisComplete.value = false
        return
      } else if (status === 'running' && attempts < maxAttempts) {
        // 任务仍在运行，继续轮询
        setTimeout(poll, pollInterval)
      } else if (attempts >= maxAttempts) {
        // 超时
        console.error('洞察分析任务轮询超时')
        isAnalysisLoading.value = false
        isAnalysisComplete.value = false
      }
    } catch (error) {
      console.error('轮询洞察分析任务失败:', error)
      if (attempts < maxAttempts) {
        // 出错时继续重试
        setTimeout(poll, pollInterval)
      } else {
        isAnalysisLoading.value = false
        isAnalysisComplete.value = false
      }
    }
  }

  // 开始轮询
  poll()
}

const fetchStreamingChatResponse = async (userQuestion: string) => {
  if (!userQuestion) return

  console.log('开始流式对话，当前conversation_id:', currentConversationId.value)
  streamingAnalysis.value = ''
  insightAnalysis.value = null
  isAnalysisLoading.value = true
  isAnalysisComplete.value = false

  try {
    // 调用普通对话API (使用现有的流式分析端点,但不传数据)
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/insight_analysis_stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_input: userQuestion,
        data: JSON.stringify({
          userQuestion: userQuestion,
          mode: 'chat',  // 标记为纯聊天模式
          conversation_id: currentConversationId.value || null,  // 传递当前对话ID，确保为null而不是undefined
          timestamp: new Date().toISOString()
        })
      })
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    if (!response.body) {
      throw new Error('Response body is null')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()

      if (done) {
        isAnalysisComplete.value = true
        isAnalysisLoading.value = false
        break
      }

      const chunk = decoder.decode(value, { stream: true })
      const lines = chunk.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))

            if (data.content) {
              streamingAnalysis.value += data.content
              // 实时更新临时AI消息
              if (tempAiMessage.value) {
                tempAiMessage.value.content += data.content
              }
            } else if (data.done) {
              isAnalysisComplete.value = true
              isAnalysisLoading.value = false
            } else if (data.error) {
              console.error('流式对话错误:', data.error)
              isAnalysisComplete.value = true
              isAnalysisLoading.value = false
              streamingAnalysis.value += '\n\n出现错误，请稍后重试'
              if (tempAiMessage.value) {
                tempAiMessage.value.content += '\n\n出现错误，请稍后重试'
              }
              break
            }
          } catch (e) {
            console.debug('解析流数据出错:', e)
          }
        }
      }
    }

    // 流式输出完成后，重新加载对话消息列表
    if (currentConversationId.value) {
      await reloadConversationMessages()
      // 清空流式分析内容，确保历史洞察分析能正确显示
      streamingAnalysis.value = ''
    }

  } catch (error) {
    console.error('流式对话失败:', error)
    isAnalysisComplete.value = true
    isAnalysisLoading.value = false
    streamingAnalysis.value = '抱歉，对话服务暂时不可用，请稍后重试。'
  }
}

const fetchStreamingInsightAnalysis = async () => {
  console.log('=== 开始洞察分析流程 ===')
  console.log('当前状态检查:')
  console.log('- inputValue:', inputValue.value)
  console.log('- chartOptions:', chartOptions.value)
  console.log('- hasData:', hasData.value)
  console.log('- tempAiMessage:', tempAiMessage.value)

  if (!inputValue.value) {
    console.log('❌ inputValue为空，退出函数')
    return
  }

  console.log('✅ 开始设置状态变量...')
  streamingAnalysis.value = ''
  insightAnalysis.value = null
  isAnalysisLoading.value = true
  isAnalysisComplete.value = false

  console.log('✅ 状态变量设置完成:', {
    streamingAnalysis: streamingAnalysis.value,
    insightAnalysis: insightAnalysis.value,
    isAnalysisLoading: isAnalysisLoading.value,
    isAnalysisComplete: isAnalysisComplete.value
  })

  try {
    const requestUrl = `${import.meta.env.VITE_API_BASE_URL}/api/insight_analysis_stream`
    const requestBody = {
      user_input: inputValue.value,
      data: JSON.stringify({
        chartData: chartOptions.value,
        userQuestion: inputValue.value,
        timestamp: new Date().toISOString(),
        mode: 'analysis',  // 标记为洞察分析模式
        conversation_id: currentConversationId.value  // 传递当前对话ID
      })
    }

    console.log('📡 准备发送请求:')
    console.log('- URL:', requestUrl)
    console.log('- Body:', requestBody)

    const response = await fetch(requestUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody)
    })

    console.log('📥 收到响应:', {
      status: response.status,
      ok: response.ok,
      headers: Object.fromEntries(response.headers.entries())
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    if (!response.body) {
      throw new Error('Response body is null')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    console.log('🔄 开始读取流式数据...')
    let chunkCount = 0
    while (true) {
      const { done, value } = await reader.read()

      if (done) {
        console.log('✅ 流式数据读取完成，总共处理了', chunkCount, '个数据块')
        isAnalysisComplete.value = true
        isAnalysisLoading.value = false
        break
      }

      chunkCount++
      const chunk = decoder.decode(value, { stream: true })
      console.log(`📦 收到第${chunkCount}个数据块:`, chunk)
      const lines = chunk.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const dataStr = line.slice(6)
            console.log('🔍 解析数据字符串:', dataStr)
            const data = JSON.parse(dataStr)
            console.log('✅ 解析成功的数据:', data)

            // 处理后端返回的不同数据格式
            if (data.content) {
              // 处理流式内容
              const oldLength = streamingAnalysis.value.length
              streamingAnalysis.value += data.content
              console.log(`📝 更新streamingAnalysis: ${oldLength} -> ${streamingAnalysis.value.length} 字符`)
              console.log('📝 新增内容:', data.content)

              // 实时更新临时AI消息
              if (tempAiMessage.value) {
                tempAiMessage.value.content += data.content
                console.log('📝 同步更新tempAiMessage')
              }
            } else if (data.delta && data.delta.content) {
              // 处理OpenAI格式的delta内容
              const oldLength = streamingAnalysis.value.length
              streamingAnalysis.value += data.delta.content
              console.log(`📝 更新streamingAnalysis (delta): ${oldLength} -> ${streamingAnalysis.value.length} 字符`)
              if (tempAiMessage.value) {
                tempAiMessage.value.content += data.delta.content
              }
            } else if (data.choices && data.choices[0] && data.choices[0].delta && data.choices[0].delta.content) {
              // 处理OpenAI API格式的choices.delta.content
              const content = data.choices[0].delta.content
              const oldLength = streamingAnalysis.value.length
              streamingAnalysis.value += content
              console.log(`📝 更新streamingAnalysis (choices): ${oldLength} -> ${streamingAnalysis.value.length} 字符`)
              if (tempAiMessage.value) {
                tempAiMessage.value.content += content
              }
            } else if (data.done || (data.choices && data.choices[0] && data.choices[0].finish_reason)) {
              console.log('🏁 收到完成信号')
              isAnalysisComplete.value = true
              isAnalysisLoading.value = false
            } else if (data.error) {
              console.error('❌ 流式分析错误:', data.error)
              isAnalysisComplete.value = true
              isAnalysisLoading.value = false
              streamingAnalysis.value += '\n\n出现错误，正在尝试获取缓存的分析结果...'
              if (tempAiMessage.value) {
                tempAiMessage.value.content += '\n\n出现错误，正在尝试获取缓存的分析结果...'
              }
              setTimeout(fetchInsightAnalysis, 1000)
              break
            } else {
              // 处理其他可能的数据格式
              console.log('⚠️ 收到未处理的数据格式:', data)
            }
          } catch (e) {
            console.debug('⚠️ 解析流数据出错:', e, '原始数据:', line)
          }
        }
      }
    }

    // 流式输出完成后，重新加载对话消息列表
    if (currentConversationId.value) {
      console.log('🔄 重新加载对话消息列表...')
      await reloadConversationMessages()
      // 清空流式分析内容，确保历史洞察分析能正确显示
      streamingAnalysis.value = ''
      // 如果是新会话的第一条消息，自动生成标题
      await generateConversationTitleIfNeeded()
    }

  } catch (error) {
    console.error('❌ 流式洞察分析失败:', error)
    isAnalysisComplete.value = true
    isAnalysisLoading.value = false
    streamingAnalysis.value = ''
    fetchInsightAnalysis()
  }

  console.log('=== 洞察分析流程结束 ===')
}

const handleToolSelect = (action: string) => {
  console.log('工具选择:', action)
  // 这里可以处理不同工具的逻辑
  switch (action) {
    case 'upload':
      console.log('上传文件')
      break
    case 'create-image':
      console.log('创建图片')
      break
    case 'think-longer':
      console.log('思考时间更长')
      break
    case 'deep-research':
      console.log('深度研究')
      break
    case 'study':
      console.log('研究与学习')
      break
    case 'more':
      console.log('更多选项')
      break
    default:
      console.log('未知操作:', action)
  }
}

// 创建新会话
const createNewConversation = async () => {
  try {
    const response = await axios.post(
      `${import.meta.env.VITE_API_BASE_URL}/api/conversation/create`,
      {
        user_id: 1,
        title: '新对话'
      }
    )

    if (response.data.success) {
      currentConversationId.value = response.data.conversation_id
      console.log('新会话已创建:', currentConversationId.value)
      return currentConversationId.value
    }
  } catch (error) {
    console.error('创建新会话失败:', error)
  }
  return null
}

// 新增会话
const handleNewChat = () => {
  // 重置所有状态回到初始页面
  inputValue.value = ''
  lastUserMessage.value = ''
  hasData.value = false
  hasChartData.value = false
  isLoading.value = false
  hasStartedChat.value = false
  chartOptions.value = {}
  chartType.value = 'bar'
  responseTime.value = null
  insightAnalysis.value = null
  streamingAnalysis.value = ''
  isAnalysisLoading.value = false
  isAnalysisComplete.value = false
  selectedDatasets.value = []
  // 清空消息列表
  messageList.value = []
  // 清空临时消息
  tempUserMessage.value = null
  tempAiMessage.value = null
  isStreaming.value = false
  // 重置当前会话ID（下次发送消息时会自动创建新会话）
  currentConversationId.value = null
  // 重置处理步骤
  currentProcessingStep.value = ''
  processingError.value = ''
  showProcessingSteps.value = false

  console.log('已重置到初始状态，下次发送消息时将创建新会话')
}

// 组件挂载时的初始化
onMounted(async () => {
  if (contentArea.value) {
    contentArea.value.addEventListener('scroll', handleScroll)
  }

  // 刷新页面不创建会话，保持初始状态
  console.log('页面加载完成，等待用户操作')
})

// 处理文件上传成功
const handleUploadSuccess = async (datasetId: string) => {
  console.log('文件上传成功，数据集ID:', datasetId)

  // 刷新数据集列表
  if (datasetListRef.value) {
    datasetListRef.value.refreshDatasets()
  }

  // 获取上传的数据集详情并自动添加到选中列表
  try {
    const response = await axios.get(
      `${import.meta.env.VITE_API_BASE_URL}/api/dataset/${datasetId}/status`
    )
    const dataset = response.data
    handleDatasetSelect({
      id: dataset.dataset_id,
      name: dataset.name,
      logical_name: dataset.logical_name,
      row_count: dataset.row_count || 0,
      column_count: dataset.column_count || 0
    })
  } catch (error) {
    console.error('获取数据集详情失败:', error)
  }
}

// 处理数据集选择 - 支持多选
const handleDatasetSelect = (dataset: Dataset) => {
  console.log('选择数据集:', dataset)

  // 检查是否已选中
  const index = selectedDatasets.value.findIndex(d => d.id === dataset.id)
  if (index === -1) {
    // 未选中,添加到列表
    selectedDatasets.value.push(dataset)
  } else {
    // 已选中,不重复添加
    console.log('数据集已在选中列表中')
  }
}

// 处理移除数据集
const handleRemoveDataset = (datasetId: string) => {
  selectedDatasets.value = selectedDatasets.value.filter(d => d.id !== datasetId)
}

// 处理预览数据集
const handlePreviewDataset = (dataset: Dataset) => {
  // 打开数据集预览对话框
  if (datasetListRef.value && datasetListRef.value.openPreviewDialog) {
    datasetListRef.value.openPreviewDialog(dataset)
  }
}

// 滚动到底部
const scrollToBottom = (smooth = true) => {
  nextTick(() => {
    if (contentArea.value) {
      contentArea.value.scrollTo({
        top: contentArea.value.scrollHeight,
        behavior: smooth ? 'smooth' : 'auto'
      })
    }
  })
}

// 监听滚动事件，判断是否显示"滚动到底部"按钮
const handleScroll = () => {
  if (!contentArea.value) return

  const { scrollTop, scrollHeight, clientHeight } = contentArea.value
  const distanceFromBottom = scrollHeight - scrollTop - clientHeight

  console.log('Scroll event:', { scrollTop, scrollHeight, clientHeight, distanceFromBottom })

  // 如果距离底部超过200px，显示按钮
  showScrollToBottom.value = distanceFromBottom > 200
  console.log('Show scroll button:', showScrollToBottom.value)
}

// 监听内容变化，自动滚动到底部
watch([streamingAnalysis, messageList, hasData], () => {
  // 如果用户没有向上滚动（按钮未显示），则自动滚动
  if (!showScrollToBottom.value) {
    scrollToBottom(true)
  }
}, { flush: 'post' })

// 组件卸载时移除滚动监听
onUnmounted(() => {
  if (contentArea.value) {
    contentArea.value.removeEventListener('scroll', handleScroll)
  }
})

// 辅助函数：格式化消息时间（年月日 时:分）
const formatMessageTime = (isoString: string) => {
  if (!isoString) return ''

  const date = new Date(isoString)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')

  return `${year}/${month}/${day} ${hours}:${minutes}`
}

// 辅助函数：根据图表数据构建ECharts配置
const buildChartOptions = (chartData: any) => {
  if (!chartData) return {}

  const refinedData = chartData.refined_data
  const data = chartData.data
  const chartType = chartData.chart_type || 'bar'
  const visualizationType = chartData.visualization_type

  console.log('构建图表选项 - 原始数据:', data)
  console.log('构建图表选项 - refined_data:', refinedData)
  console.log('构建图表选项 - chartType:', chartType)
  console.log('构建图表选项 - visualizationType:', visualizationType)

  if (!data || data.length === 0) {
    console.warn('图表数据为空')
    return {}
  }

  // 对于table类型或没有refined_data的情况，尝试自动构建图表配置
  if (!refinedData || visualizationType === 'table') {
    console.log('没有refined_data或为table类型，自动推断数据结构')

    const columns = Object.keys(data[0])
    if (columns.length === 0) return {}

    // 找到数值列和非数值列 - 多行采样(前10行)，避免仅首行为空导致误判
    const sampleSize = Math.min(10, data.length)
    const isNumericValue = (v: any) => {
      if (v === null || v === undefined || v === '') return false
      if (typeof v === 'number') return !isNaN(v) && isFinite(v)
      if (typeof v === 'string') {
        const num = parseFloat(v)
        return !isNaN(num) && isFinite(num)
      }
      return false
    }
    const blacklistSubstrings = ['dataset', 'dataset_id', 'source', 'source_id']
    const isBlacklisted = (name: string) => {
      const n = String(name || '').toLowerCase()
      return blacklistSubstrings.some(sub => n.includes(sub))
    }

    const numericColumns = columns.filter(col => {
      let numericCount = 0
      for (let i = 0; i < sampleSize; i++) {
        if (isNumericValue(data[i][col])) numericCount++
      }
      // 至少一半样本为数值则判为数值列
      return numericCount >= Math.ceil(sampleSize / 2)
    })

    const categoryColumns = columns.filter(col => !numericColumns.includes(col))

    console.log('数值列:', numericColumns)
    console.log('分类列:', categoryColumns)

    // 如果没有数值列，无法生成图表
    if (numericColumns.length === 0) {
      console.warn('没有找到数值列，无法生成图表')
      return {}
    }

    // 选择第一个分类列作为x轴，如果没有分类列则使用索引
    const xAxisColumn = categoryColumns.length > 0 ? categoryColumns[0] : 'index'
    const xAxisData = xAxisColumn === 'index'
      ? data.map((_: any, index: number) => `项目${index + 1}`)
      : data.map((item: any) => String(item[xAxisColumn] || ''))

    // 过滤黑名单列后，使用最多前10个数值列作为y轴
    const candidateNumericColumns = numericColumns.filter(col => !isBlacklisted(col))
    const yAxisColumns = candidateNumericColumns.slice(0, 10)
    const seriesData = yAxisColumns.map((col: string) => {
      const seriesValues = data.map((item: any) => {
        const value = item[col]
        if (value === null || value === undefined || value === '') return 0
        const numValue = Number(value)
        return isNaN(numValue) ? 0 : numValue
      })

      return {
        name: col,
        type: chartType,
        data: seriesValues,
        stack: chartType === 'bar' ? 'x' : undefined,
        areaStyle: chartType === 'line' ? {} : undefined
      }
    })

    console.log('自动构建的x轴数据:', xAxisData)
    console.log('自动构建的系列数据:', seriesData)

    return {
      xAxis: {
        type: 'category' as const,
        data: xAxisData,
      },
      yAxis: {
        type: 'value' as const,
      },
      series: seriesData,
      legend: {
        data: yAxisColumns
      },
      tooltip: {
        trigger: 'axis' as const
      }
    }
  }

  // 验证refined_data的有效性
  if (!data.some((item: any) => item.hasOwnProperty(refinedData.x_axis))) {
    console.warn(`x轴字段 ${refinedData.x_axis} 在数据中不存在，回退到自动推断`)
    return buildChartOptions({ data, refined_data: null, chart_type: chartType, visualization_type: 'chart' })
  }

  const invalidYAxes = refinedData.y_axes.filter((yAxis: string) =>
    !data.some((item: any) => item.hasOwnProperty(yAxis))
  )

  if (invalidYAxes.length > 0) {
    console.warn(`y轴字段 ${invalidYAxes.join(', ')} 在数据中不存在，回退到自动推断`)
    return buildChartOptions({ data, refined_data: null, chart_type: chartType, visualization_type: 'chart' })
  }

  // 原有的refined_data处理逻辑
  const xAxisData = data.map((item: any) => String(item[refinedData.x_axis] || ''))
  const seriesData = refinedData.y_axes.map((yAxis: string) => {
    const seriesValues = data.map((item: any) => {
      const value = item[yAxis]
      if (value === null || value === undefined || value === '') return 0
      const numValue = Number(value)
      return isNaN(numValue) ? 0 : numValue
    })

    return {
      name: yAxis,
      type: chartType,
      data: seriesValues,
      stack: chartType === 'bar' ? 'x' : undefined,
      areaStyle: chartType === 'line' ? {} : undefined
    }
  })

  console.log('使用refined_data构建的x轴数据:', xAxisData)
  console.log('使用refined_data构建的系列数据:', seriesData)

  return {
    xAxis: {
      type: 'category' as const,
      data: xAxisData,
    },
    yAxis: {
      type: 'value' as const,
    },
    series: seriesData,
    legend: {
      data: refinedData.y_axes
    },
    tooltip: {
      trigger: 'axis' as const
    }
  }
}

// 处理图表类型变更
const handleChartTypeChange = (message: Message, newType: string) => {
  console.log('图表类型变更:', newType)
  if (message.chart_data) {
    message.chart_data.chart_type = newType
  }
}

// 重新加载当前对话的所有消息（流式输出完成后调用）
const reloadConversationMessages = async () => {
  if (!currentConversationId.value) return

  try {
    console.log('重新加载对话消息:', currentConversationId.value)
    const response = await axios.get(
      `${import.meta.env.VITE_API_BASE_URL}/api/conversation/${currentConversationId.value}/messages`
    )

    if (response.data.success) {
      const messages = response.data.messages
      messageList.value = messages
      console.log('对话消息已更新，共', messages.length, '条')

      // 清除临时消息（已经从数据库加载了真实消息）
      tempUserMessage.value = null
      tempAiMessage.value = null
      isStreaming.value = false
      
      // 重置洞察分析状态，确保历史洞察分析能正确显示
      isAnalysisLoading.value = false
      isAnalysisComplete.value = true

      // 滚动到底部
      nextTick(() => {
        scrollToBottom(true)
      })
    }
  } catch (error) {
    console.error('重新加载对话消息失败:', error)
  }
}

// 生成对话标题（如果需要）
const generateConversationTitleIfNeeded = async () => {
  try {
    if (!currentConversationId.value || !lastUserMessage.value) {
      return
    }

    // 调用后端API生成标题
    const response = await axios.post(
      `${import.meta.env.VITE_API_BASE_URL}/api/conversation/generate_title`,
      {
        conversation_id: currentConversationId.value,
        user_question: lastUserMessage.value
      }
    )

    if (response.data.success && response.data.updated) {
      console.log('对话标题已自动生成:', response.data.title)
      // 触发会话列表刷新
      conversationHistoryRef.value?.refreshConversations()
    }
  } catch (error) {
    console.error('生成对话标题失败:', error)
    // 失败不影响主流程，静默处理
  }
}

// 订阅进度更新
const subscribeToProgress = (taskId: string) => {
  console.log('订阅进度更新:', taskId)

  const eventSource = new EventSource(`${import.meta.env.VITE_API_BASE_URL}/api/progress/${taskId}`)

  eventSource.onmessage = (event) => {
    try {
      const progressData = JSON.parse(event.data)
      console.log('收到进度更新:', progressData)

      // 更新当前步骤
      if (progressData.step) {
        currentProcessingStep.value = progressData.step
      }

      // 更新错误状态
      if (progressData.error) {
        processingError.value = progressData.message || '处理过程中发生错误'
      } else {
        processingError.value = ''
      }

      // 如果进度完成，关闭连接
      if (progressData.progress === 100 || progressData.error) {
        eventSource.close()
      }
    } catch (error) {
      console.error('解析进度数据失败:', error)
    }
  }

  eventSource.onerror = (error) => {
    console.error('进度订阅连接错误:', error)
    eventSource.close()
  }

  // 30秒后自动关闭连接
  setTimeout(() => {
    if (eventSource.readyState !== EventSource.CLOSED) {
      eventSource.close()
    }
  }, 30000)
}

// 处理选择历史对话
const handleSelectConversation = async (conversationId: number) => {
  console.log('选中历史对话:', conversationId)

  // 立即清空页面状态
  currentConversationId.value = conversationId
  isLoading.value = true
  hasStartedChat.value = false
  messageList.value = []
  hasData.value = false
  hasChartData.value = false
  streamingAnalysis.value = ''
  insightAnalysis.value = null
  responseTime.value = null
  lastUserMessage.value = ''
  tempUserMessage.value = null
  tempAiMessage.value = null
  isStreaming.value = false

  try {
    // 从后端加载对话的所有消息
    const response = await axios.get(
      `${import.meta.env.VITE_API_BASE_URL}/api/conversation/${conversationId}/messages`
    )

    if (response.data.success) {
      const messages = response.data.messages
      console.log('加载历史消息:', messages)

      // 如果消息列表为空，显示初始状态
      if (messages.length === 0) {
        console.log('会话消息列表为空，显示初始状态')
      } else {
        // 有消息，切换到对话视图，显示消息列表
        hasStartedChat.value = true
        messageList.value = messages
        hasData.value = true

        // 加载完成后滚动到底部
        nextTick(() => {
          scrollToBottom(false) // 立即滚动，不使用动画
        })
      }
    }
  } catch (error) {
    console.error('加载历史对话失败:', error)
    // 显示错误消息
    messageList.value = []
    hasData.value = false
    hasStartedChat.value = false
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
/* 主容器 - 占满父元素 */
.home-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* 初始状态视图 - 上下布局 */
.initial-view {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

/* 居中内容容器 */
.center-content {
  flex: 1;
  width: 100%;
  max-width: 48rem;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2rem;
  padding: 1rem;
}

/* 欢迎卡片区域 */
.welcome-section {
  width: 100%;
}

/* 输入框居中区域 */
.input-center-section {
  width: 100%;
}

.input-center-wrapper {
  width: 100%;
}

/* 初始状态底部免责声明 */
.disclaimer-footer-initial {
  position: absolute;
  bottom: 1rem;
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  text-align: center;
  background: transparent;
  padding: 0.5rem 1rem;
}

/* 初始状态 - 顶部工具栏 */
.top-toolbar {
  flex-shrink: 0;
  padding: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
  background: white;
  border: none;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

/* 对话状态视图容器 */
.conversation-view {
  flex: 1;
  position: relative;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 对话状态 - 顶部工具栏 */
.top-toolbar-conversation {
  flex-shrink: 0;
  padding: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
  background: white;
  border: none;
}

.new-chat-btn {
  flex-shrink: 0;
}

/* 对话视图 - 内容区 + 输入框 */
.content-area {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
}

.content-wrapper {
  width: 100%;
  max-width: 64rem;
  margin: 0 auto;
  padding: 2rem 1rem 6rem 1rem;
}

.messages-list {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.message-item {
  width: 100%;
}

/* 用户消息 - 右对齐 */
.user-message {
  display: flex;
  justify-content: flex-end;
}

.user-bubble {
  max-width: 80%;
  padding: 0.75rem 1.25rem;
  background-color: rgb(var(--v-theme-primary));
  color: rgb(var(--v-theme-on-primary));
  border-radius: 1rem;
  border-top-right-radius: 0.125rem;
  word-wrap: break-word;
  word-break: break-word;
  overflow-wrap: break-word;
  box-sizing: border-box;
}

.user-bubble p {
  margin: 0;
  word-wrap: break-word;
  word-break: break-word;
  overflow-wrap: break-word;
}

/* AI消息 - 左对齐 */
.ai-message {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.chart {
  width: 100%;
  height: 24rem;
}

.loading-state {
  text-align: center;
  padding: 2rem 0;
}

.action-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.25rem;
}

.action-buttons {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.action-icon-btn {
  opacity: 0.4;
  transition: opacity 0.2s ease;
}

.action-icon-btn:hover {
  opacity: 0.7;
}

.time-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-left: auto;
}

.message-time {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  white-space: nowrap;
}

.response-time {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  white-space: nowrap;
}

/* 滚动到底部按钮容器 */
.scroll-to-bottom-container {
  position: fixed;
  bottom: 160px;
  /* 输入框上方，适应更小的输入框 */
  right: 2rem;
  /* 改为右侧对齐，更明显 */
  z-index: 2001;
  /* 提高z-index确保在所有内容上方 */
  pointer-events: none;
  /* 让容器本身不阻挡点击 */
}

.scroll-to-bottom-btn {
  pointer-events: auto;
  /* 恢复按钮的点击 */
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  border-radius: 24px;
}

/* 按钮淡入淡出动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 输入框区域 - 固定底部 */
.input-bar {
  flex-shrink: 0;
  background-color: rgb(var(--v-theme-background));
  padding: 0.75rem 1rem;
  padding-bottom: 0;
  /* 为免责声明腾出空间 */
}

/* 对话状态下输入框更紧凑 */
.input-bar :deep(.chat-input-wrapper) {
  padding: 0.5rem 1rem;
}

.input-bar :deep(.input-area) {
  font-size: 0.875rem;
  min-height: 1.5rem;
}

.input-wrapper {
  width: 100%;
  max-width: 64rem;
  margin: 0 auto;
}

/* 底部免责声明 - 透明 */
.disclaimer-footer {
  flex-shrink: 0;
  background: transparent;
  text-align: center;
  padding: 0.5rem 1rem;
}

/* 图表切换按钮组样式 */
.chart-toggle-group {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.chart-toggle-btn {
  border-radius: 0 !important;
  transition: all 0.2s ease;
  font-weight: 500;
}

.chart-toggle-group :deep(.v-btn--active) {
  background-color: rgba(var(--v-theme-primary), 0.1) !important;
  color: rgb(var(--v-theme-primary)) !important;
}

.chart-toggle-group :deep(.v-btn:not(.v-btn--active)) {
  background-color: rgba(var(--v-theme-surface), 1) !important;
  color: rgba(var(--v-theme-on-surface), 0.8) !important;
  border: 1px solid rgba(var(--v-theme-outline), 0.2) !important;
}

.chart-toggle-group :deep(.v-btn:hover:not(.v-btn--active)) {
  background-color: rgba(var(--v-theme-primary), 0.05) !important;
  color: rgba(var(--v-theme-on-surface), 0.9) !important;
  border-color: rgba(var(--v-theme-primary), 0.3) !important;
}

/* 洞察分析卡片样式 */
.insight-analysis-card {
  border: 1px solid rgba(var(--v-theme-primary), 0.2);
  background: linear-gradient(135deg, rgba(var(--v-theme-primary), 0.05) 0%, rgba(var(--v-theme-surface), 1) 100%);
}

.insight-analysis-card .v-card-title {
  background: rgba(var(--v-theme-primary), 0.1);
  font-weight: 600;
}

/* 骨架屏样式 */
.insight-skeleton {
  animation: pulse 1.5s ease-in-out infinite;
}

/* 流式内容样式 */
.streaming-content {
  position: relative;
}

/* 打字机光标效果 */
.typing-cursor {
  display: inline-block;
  background-color: rgb(var(--v-theme-primary));
  width: 2px;
  height: 1.2em;
  margin-left: 2px;
  animation: blink 1s infinite;
}

@keyframes blink {

  0%,
  50% {
    opacity: 1;
  }

  51%,
  100% {
    opacity: 0;
  }
}

@keyframes pulse {

  0%,
  100% {
    opacity: 1;
  }

  50% {
    opacity: 0.7;
  }
}

/* 静态内容样式 */
.static-content {
  opacity: 1;
  transition: opacity 0.3s ease;
}

.disclaimer-text {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  opacity: 0.8;
}

/* 响应式 */
@media (min-width: 640px) {
  .center-content {
    padding: 2rem;
  }
}

/* 移动端优化滚动按钮 */
@media (max-width: 768px) {
  .scroll-to-bottom-container {
    right: 1rem;
    bottom: 140px;
  }

  .scroll-to-bottom-btn {
    font-size: 0.875rem;
  }
}
</style>
