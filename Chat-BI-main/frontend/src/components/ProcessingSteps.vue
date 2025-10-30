<template>
  <v-card class="processing-steps" elevation="2">
    <v-card-text>
      <div class="steps-container">
        <div
          v-for="(step, index) in steps"
          :key="index"
          class="step-item"
          :class="{
            'step-completed': step.status === 'completed',
            'step-active': step.status === 'active',
            'step-error': step.status === 'error'
          }">
          <div class="step-icon">
            <v-icon v-if="step.status === 'completed'" color="success" size="small">
              mdi-check-circle
            </v-icon>
            <v-icon v-else-if="step.status === 'error'" color="error" size="small">
              mdi-alert-circle
            </v-icon>
            <v-progress-circular
              v-else-if="step.status === 'active'"
              indeterminate
              color="primary"
              size="20"
              width="2"
            />
            <v-icon v-else color="grey" size="small">
              mdi-circle-outline
            </v-icon>
          </div>
          <div class="step-content">
            <div class="step-title">{{ step.title }}</div>
            <div v-if="step.description" class="step-description">{{ step.description }}</div>
            <div v-if="step.error" class="step-error-message">{{ step.error }}</div>
          </div>
        </div>
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

interface Step {
  title: string
  description?: string
  status: 'pending' | 'active' | 'completed' | 'error'
  error?: string
}

interface Props {
  currentStep?: string
  error?: string
}

const props = defineProps<Props>()

// 定义处理步骤
const steps = ref<Step[]>([
  {
    title: '意图识别',
    description: '分析用户问题类型...',
    status: 'pending'
  },
  {
    title: '数据检索',
    description: '从向量数据库检索相关数据集...',
    status: 'pending'
  },
  {
    title: 'SQL生成',
    description: '生成数据查询语句...',
    status: 'pending'
  },
  {
    title: '查询执行',
    description: '执行数据查询...',
    status: 'pending'
  },
  {
    title: '结果分析',
    description: '生成图表和洞察分析...',
    status: 'pending'
  }
])

// 监听当前步骤变化
watch(() => props.currentStep, (newStep) => {
  if (!newStep) return

  const stepMap: { [key: string]: number } = {
    'intent': 0,
    'retrieval': 1,
    'sql_generation': 2,
    'query_execution': 3,
    'analysis': 4
  }

  const currentIndex = stepMap[newStep]
  if (currentIndex !== undefined) {
    // 更新步骤状态
    steps.value.forEach((step, index) => {
      if (index < currentIndex) {
        step.status = 'completed'
      } else if (index === currentIndex) {
        step.status = 'active'
      } else {
        step.status = 'pending'
      }
    })
  }
}, { immediate: true })

// 监听错误
watch(() => props.error, (error) => {
  if (error && props.currentStep) {
    const stepMap: { [key: string]: number } = {
      'intent': 0,
      'retrieval': 1,
      'sql_generation': 2,
      'query_execution': 3,
      'analysis': 4
    }

    const currentIndex = stepMap[props.currentStep]
    if (currentIndex !== undefined) {
      steps.value[currentIndex].status = 'error'
      steps.value[currentIndex].error = error
    }
  }
})
</script>

<style scoped>
.processing-steps {
  margin-bottom: 1rem;
}

.steps-container {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.step-item {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 0.5rem;
  border-radius: 0.5rem;
  transition: background-color 0.2s ease;
}

.step-item.step-active {
  background-color: rgba(var(--v-theme-primary), 0.05);
}

.step-item.step-completed {
  opacity: 0.7;
}

.step-item.step-error {
  background-color: rgba(var(--v-theme-error), 0.05);
}

.step-icon {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.step-content {
  flex: 1;
  min-width: 0;
}

.step-title {
  font-weight: 600;
  font-size: 0.875rem;
  color: rgb(var(--v-theme-on-surface));
}

.step-description {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin-top: 0.125rem;
}

.step-error-message {
  font-size: 0.75rem;
  color: rgb(var(--v-theme-error));
  margin-top: 0.25rem;
}
</style>
