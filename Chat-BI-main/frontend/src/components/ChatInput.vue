<template>
  <div class="chat-input-container">
    <!-- 数据集标签区域 -->
    <DatasetChips
      v-if="selectedDatasets.length > 0"
      :datasets="selectedDatasets"
      @remove="handleRemoveDataset"
      @preview="handlePreviewDataset"
    />

    <!-- 输入框 -->
    <div
      class="chat-input-wrapper"
      :class="{ 'focused': isFocused, 'has-datasets': selectedDatasets.length > 0 }"
      @focusin="isFocused = true"
      @focusout="isFocused = false">

      <!-- 输入区域 -->
      <div class="input-section">
      <textarea
        ref="textareaRef"
        v-model="localValue"
        :placeholder="placeholder"
        :disabled="disabled"
        :rows="rows"
        class="input-area"
        @keydown.enter.exact.prevent="handleSend"
        @keydown.enter.shift.exact="handleNewLine"
        @input="autoResize"
      ></textarea>
    </div>

    <!-- 功能按钮区域 -->
    <div class="action-bar">
      <v-btn
        icon
        size="small"
        variant="plain"
        class="action-btn"
        @click="emit('uploadClick')">
        <v-icon>mdi-paperclip</v-icon>
      </v-btn>

      <ToolMenu
        :position="toolMenuPosition"
        @select="handleToolSelect"
      />

      <div class="spacer"></div>

      <v-icon
        v-if="localValue"
        class="clear-icon"
        @click="handleClear">
        mdi-close-circle
      </v-icon>

      <v-btn
        icon
        size="small"
        color="primary"
        :disabled="disabled || !localValue"
        class="send-btn circular-btn"
        rounded="xl"
        @click="handleSend">
        <v-icon>mdi-arrow-up</v-icon>
      </v-btn>
    </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import ToolMenu from './ToolMenu.vue'
import DatasetChips from './DatasetChips.vue'

interface Dataset {
  id: string
  name: string
  logical_name?: string
  row_count: number
  column_count: number
}

interface Props {
  modelValue: string
  disabled?: boolean
  rows?: number
  placeholder?: string
  maxRows?: number
  toolMenuPosition?: 'top' | 'bottom'
  selectedDatasets?: Dataset[]
}

interface Emits {
  (e: 'update:modelValue', value: string): void
  (e: 'send'): void
  (e: 'toolSelect', action: string): void
  (e: 'uploadClick'): void
  (e: 'removeDataset', datasetId: string): void
  (e: 'previewDataset', dataset: Dataset): void
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
  rows: 1,
  placeholder: '请输入问题',
  maxRows: 6,
  toolMenuPosition: 'bottom',
  selectedDatasets: () => []
})

const emit = defineEmits<Emits>()

const isFocused = ref(false)
const textareaRef = ref<HTMLTextAreaElement>()

const localValue = computed({
  get: () => props.modelValue,
  set: (value: string) => emit('update:modelValue', value)
})

const handleSend = () => {
  if (!props.disabled && localValue.value) {
    emit('send')
  }
}

const handleClear = () => {
  localValue.value = ''
  nextTick(() => {
    autoResize()
    textareaRef.value?.focus()
  })
}

const handleNewLine = () => {
  const textarea = textareaRef.value
  if (!textarea) return

  const start = textarea.selectionStart
  const end = textarea.selectionEnd
  const value = localValue.value

  localValue.value = value.substring(0, start) + '\n' + value.substring(end)

  nextTick(() => {
    textarea.selectionStart = textarea.selectionEnd = start + 1
    autoResize()
  })
}

const handleToolSelect = (action: string) => {
  emit('toolSelect', action)
}

const handleRemoveDataset = (datasetId: string) => {
  emit('removeDataset', datasetId)
}

const handlePreviewDataset = (dataset: Dataset) => {
  emit('previewDataset', dataset)
}

const autoResize = () => {
  const textarea = textareaRef.value
  if (!textarea) return

  // 重置高度以获取正确的 scrollHeight
  textarea.style.height = 'auto'

  // 计算最大高度
  const lineHeight = parseInt(getComputedStyle(textarea).lineHeight)
  const maxHeight = lineHeight * props.maxRows

  // 设置新高度
  const newHeight = Math.min(textarea.scrollHeight, maxHeight)
  textarea.style.height = `${newHeight}px`
}

watch(() => props.modelValue, () => {
  nextTick(autoResize)
})

onMounted(() => {
  autoResize()
})
</script>

<style scoped>
.chat-input-container {
  width: 100%;
}

.chat-input-wrapper {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1rem 1.25rem;
  border: 1px solid currentColor;
  border-radius: 1.5rem;
  opacity: 0.5;
  transition: all 0.2s;
}

/* 有数据集时,移除顶部边框,顶部圆角改为0 */
.chat-input-wrapper.has-datasets {
  border-top: none;
  border-top-left-radius: 0;
  border-top-right-radius: 0;
}

.chat-input-wrapper.focused {
  opacity: 1;
}

.input-section {
  width: 100%;
}

.input-area {
  width: 100%;
  min-height: 2rem;
  padding: 0;
  border: none;
  outline: none;
  background: transparent;
  resize: none;
  font-family: inherit;
  font-size: 1rem;
  line-height: 1.5rem;
  overflow-y: auto;
}

.input-area:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.action-bar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.action-btn {
  flex-shrink: 0;
}

.spacer {
  flex: 1;
}

.clear-icon {
  flex-shrink: 0;
  cursor: pointer;
  opacity: 0.6;
  transition: opacity 0.2s;
}

.clear-icon:hover {
  opacity: 1;
}

.send-btn {
  flex-shrink: 0;
}

/* 强制发送按钮保持圆形，不受全局圆角设置影响 */
.circular-btn {
  border-radius: 50% !important;
}
</style>
