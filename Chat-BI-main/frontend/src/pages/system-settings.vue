<template>
  <div class="settings-container">
    <div class="settings-wrapper">
      <!-- 页面标题 -->
      <div class="page-header">
        <h1 class="text-h4 font-weight-bold">系统设置</h1>
        <p class="text-body-2 text-medium-emphasis mt-2">自定义您的系统偏好设置</p>
      </div>

      <!-- 设置内容 -->
      <v-card class="mt-6">
        <v-card-title class="text-h6">外观设置</v-card-title>
        <v-card-text>
          <!-- 圆角设置 -->
          <div class="setting-item">
            <div class="setting-info">
              <div class="setting-label">圆角大小</div>
              <div class="setting-description">调整界面元素的圆角程度</div>
            </div>

            <div class="setting-control">
              <v-btn-toggle
                v-model="selectedRounded"
                mandatory
                color="primary"
                variant="outlined"
                class="rounded-toggle">
                <v-btn value="0" size="small">
                  <span>直角</span>
                </v-btn>
                <v-btn value="sm" size="small">
                  <span>小</span>
                </v-btn>
                <v-btn value="md" size="small">
                  <span>中</span>
                </v-btn>
                <v-btn value="lg" size="small">
                  <span>大</span>
                </v-btn>
                <v-btn value="xl" size="small">
                  <span>超大</span>
                </v-btn>
              </v-btn-toggle>
            </div>
          </div>

          <v-divider class="my-6"></v-divider>

          <!-- 预览示例 -->
          <div class="preview-section">
            <div class="text-subtitle-2 mb-4">预览效果</div>
            <div class="preview-grid">
              <v-btn color="primary" :rounded="selectedRounded">按钮示例</v-btn>
              <v-card class="pa-4" elevation="2" :rounded="selectedRounded">
                <div class="text-body-2">卡片示例</div>
              </v-card>
              <v-chip color="secondary" :rounded="selectedRounded">标签示例</v-chip>
              <v-text-field
                label="输入框示例"
                variant="outlined"
                density="compact"
                hide-details
                :rounded="selectedRounded"
              ></v-text-field>
            </div>
          </div>

          <!-- 提示信息 -->
          <v-alert
            v-if="hasChanges"
            type="info"
            variant="tonal"
            class="mt-4"
            density="compact">
            <template v-slot:prepend>
              <v-icon>mdi-information</v-icon>
            </template>
            <div class="text-body-2">预览效果仅供参考，点击"保存设置"后将应用到整个系统</div>
          </v-alert>
        </v-card-text>
      </v-card>

      <!-- Embedding 模型配置 -->
      <v-card class="mt-6">
        <v-card-title class="d-flex justify-space-between align-center">
          <span class="text-h6">数据处理设置</span>
          <v-btn
            variant="text"
            color="primary"
            size="small"
            @click="goToAiModelConfig"
          >
            <v-icon start size="20">mdi-cog</v-icon>
            管理 AI 模型
          </v-btn>
        </v-card-title>
        <v-card-text>
          <!-- Embedding 模型配置状态 -->
          <div class="setting-item">
            <div class="setting-info">
              <div class="setting-label">Embedding 模型配置</div>
              <div class="setting-description">用于数据集列名向量化，影响智能检索准确度</div>
            </div>

            <div class="setting-control">
              <v-chip
                v-if="embeddingConfigStatus.configured"
                color="success"
                variant="tonal"
                prepend-icon="mdi-check-circle"
              >
                已配置
              </v-chip>
              <v-chip
                v-else
                color="error"
                variant="tonal"
                prepend-icon="mdi-alert-circle"
              >
                未配置
              </v-chip>
            </div>
          </div>

          <!-- 配置详情 -->
          <v-alert
            v-if="embeddingConfigStatus.configured"
            type="success"
            variant="tonal"
            class="mt-4"
            density="compact"
          >
            <template v-slot:prepend>
              <v-icon>mdi-check-circle</v-icon>
            </template>
            <div class="text-body-2">
              <div><strong>模型名称：</strong>{{ embeddingConfigStatus.modelName }}</div>
              <div><strong>配置名称：</strong>{{ embeddingConfigStatus.configName }}</div>
              <div><strong>提供商：</strong>{{ embeddingConfigStatus.provider }}</div>
              <div class="text-caption text-medium-emphasis mt-2">
                <v-icon size="14" class="mr-1">mdi-information-outline</v-icon>
                如需切换模型，请前往 AI 模型管理中心，将目标 Embedding 模型设为"默认配置"
              </div>
            </div>
          </v-alert>

          <!-- 未配置提示 -->
          <v-alert
            v-else
            type="error"
            variant="tonal"
            class="mt-4"
            density="compact"
          >
            <template v-slot:prepend>
              <v-icon>mdi-alert-circle</v-icon>
            </template>
            <div class="text-body-2">
              <strong>未检测到 Embedding 模型配置</strong>
              <br>
              数据集上传后将无法生成向量索引，影响智能检索功能。
              <br>
              <v-btn
                variant="text"
                color="error"
                size="small"
                class="mt-2 px-0"
                @click="goToAiModelConfig('embedding')"
              >
                <v-icon start size="18">mdi-plus-circle</v-icon>
                立即配置
              </v-btn>
            </div>
          </v-alert>
        </v-card-text>
      </v-card>

      <!-- 操作按钮 -->
      <div class="mt-6 action-buttons">
        <v-btn
          color="primary"
          size="large"
          :disabled="!hasChanges"
          @click="handleSave">
          <v-icon start>mdi-content-save</v-icon>
          保存设置
        </v-btn>

        <v-btn
          variant="outlined"
          color="error"
          size="large"
          @click="handleReset">
          <v-icon start>mdi-restore</v-icon>
          恢复默认
        </v-btn>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useSettingsStore, type RoundedSize } from '@/stores/settings'
import { useRouter } from 'vue-router'

const settingsStore = useSettingsStore()
const router = useRouter()

// 当前选择的圆角大小
const selectedRounded = ref<RoundedSize>(settingsStore.roundedSize)

// 原始值（用于检测是否有变化）
const originalRounded = ref<RoundedSize>(settingsStore.roundedSize)

// Embedding 配置状态 - 使用全局 store
const embeddingConfigStatus = computed(() => settingsStore.embeddingConfigStatus)

// 检测是否有变化
const hasChanges = computed(() => {
  return selectedRounded.value !== originalRounded.value
})

// 跳转到 AI 模型配置页面
const goToAiModelConfig = (addType?: string) => {
  if (addType) {
    // 如果指定了类型，跳转时带上查询参数
    router.push({ path: '/ai-model-config', query: { addType } })
  } else {
    router.push('/ai-model-config')
  }
}

// 保存设置
const handleSave = () => {
  if (!hasChanges.value) return

  settingsStore.setRoundedSize(selectedRounded.value)
  originalRounded.value = selectedRounded.value

  // 显示保存成功提示并刷新页面
  alert('设置已保存，页面即将刷新以应用新设置')
  window.location.reload()
}

// 重置设置
const handleReset = () => {
  if (confirm('确定要恢复默认设置吗？这将刷新页面。')) {
    selectedRounded.value = 'lg'
    settingsStore.setRoundedSize('lg')
    window.location.reload()
  }
}

// 页面离开前提示未保存的更改
const handleBeforeUnload = (e: BeforeUnloadEvent) => {
  if (hasChanges.value) {
    e.preventDefault()
    e.returnValue = ''
  }
}

onMounted(() => {
  settingsStore.initSettings()
  // 监听页面离开事件
  window.addEventListener('beforeunload', handleBeforeUnload)
})

// 清理监听器
import { onUnmounted } from 'vue'
onUnmounted(() => {
  window.removeEventListener('beforeunload', handleBeforeUnload)
})
</script>

<style scoped>
.settings-container {
  width: 100%;
  height: 100%;
  overflow-y: auto;
}

.settings-wrapper {
  width: 100%;
  max-width: 900px;
  margin: 0 auto;
  padding: 2rem 1rem;
}

.page-header {
  margin-bottom: 1rem;
}

.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 2rem;
  padding: 1rem 0;
}

.setting-info {
  flex: 1;
}

.setting-label {
  font-size: 1rem;
  font-weight: 500;
  margin-bottom: 0.25rem;
}

.setting-description {
  font-size: 0.875rem;
  opacity: 0.7;
}

.setting-control {
  flex-shrink: 0;
}

.preview-section {
  margin-top: 1rem;
}

.preview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
  align-items: center;
}

.action-buttons {
  display: flex;
  gap: 1rem;
  align-items: center;
}

/* 圆角切换按钮样式 */
.rounded-toggle {
  gap: 0.5rem;
}

.rounded-toggle :deep(.v-btn) {
  min-width: 60px;
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity)) !important;
}

.rounded-toggle :deep(.v-btn--active) {
  border-color: rgb(var(--v-theme-primary)) !important;
}

/* 响应式 */
@media (max-width: 768px) {
  .setting-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }

  .setting-control {
    width: 100%;
  }

  .setting-control :deep(.v-btn-toggle) {
    width: 100%;
  }

  .preview-grid {
    grid-template-columns: 1fr;
  }

  .action-buttons {
    flex-direction: column;
    width: 100%;
  }

  .action-buttons :deep(.v-btn) {
    width: 100%;
  }
}
</style>
