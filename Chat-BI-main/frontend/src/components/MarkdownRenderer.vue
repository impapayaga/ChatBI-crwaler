<template>
  <div class="markdown-content">
    <div v-html="renderedMarkdown" class="markdown-body"></div>
    <div v-if="streaming && showCursor" class="streaming-cursor">▊</div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { marked } from 'marked'

const props = defineProps<{
  content: string
  streaming?: boolean
}>()

const showCursor = ref(true)

// 配置marked选项
marked.setOptions({
  breaks: true,
  gfm: true,
})

const renderedMarkdown = computed(() => {
  if (!props.content) return ''
  
  try {
    return marked(props.content)
  } catch (error) {
    console.error('Markdown rendering error:', error)
    return `<p>${props.content}</p>`
  }
})

// 流式模式下的光标闪烁
watch(() => props.streaming, (newVal) => {
  if (newVal) {
    const interval = setInterval(() => {
      showCursor.value = !showCursor.value
    }, 500)
    
    watch(() => props.streaming, (streaming) => {
      if (!streaming) {
        clearInterval(interval)
        showCursor.value = false
      }
    })
  }
})
</script>

<style scoped>
.markdown-content {
  position: relative;
}

.markdown-body {
  line-height: 1.6;
  font-size: 14px;
}

.streaming-cursor {
  display: inline-block;
  color: rgb(var(--v-theme-primary));
  font-weight: bold;
  animation: pulse 1s infinite;
  margin-left: 2px;
}

@keyframes pulse {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

/* Markdown样式 - 最小化，依赖继承 */
.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3) {
  font-weight: 600;
  margin: 1rem 0 0.5rem 0;
}

.markdown-body :deep(h1) { font-size: 1.8rem; }
.markdown-body :deep(h2) { font-size: 1.5rem; }
.markdown-body :deep(h3) { font-size: 1.25rem; }

.markdown-body :deep(p) {
  margin: 0.75rem 0;
  line-height: 1.7;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  margin: 0.75rem 0;
  padding-left: 1.5rem;
}

.markdown-body :deep(li) {
  margin: 0.25rem 0;
  line-height: 1.6;
}

.markdown-body :deep(strong) {
  font-weight: 600;
}

.markdown-body :deep(code) {
  padding: 0.125rem 0.25rem;
  border-radius: 3px;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 0.9em;
  opacity: 0.9;
}

.markdown-body :deep(pre) {
  border-radius: 6px;
  padding: 1rem;
  margin: 1rem 0;
  overflow-x: auto;
  opacity: 0.9;
}

.markdown-body :deep(pre code) {
  padding: 0;
}

.markdown-body :deep(table) {
  border-collapse: collapse;
  margin: 1rem 0;
  width: 100%;
}

.markdown-body :deep(th),
.markdown-body :deep(td) {
  border: 1px solid currentColor;
  padding: 0.75rem;
  text-align: left;
  opacity: 0.5;
}

.markdown-body :deep(th) {
  font-weight: 600;
  opacity: 0.7;
}

.markdown-body :deep(blockquote) {
  margin: 1rem 0;
  padding: 0.75rem 1rem;
  border-left: 4px solid currentColor;
  border-radius: 4px;
  font-style: italic;
  opacity: 0.8;
}

.markdown-body :deep(blockquote p) {
  margin: 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .markdown-body {
    font-size: 13px;
  }

  .markdown-body :deep(h1) { font-size: 1.5rem; }
  .markdown-body :deep(h2) { font-size: 1.3rem; }
  .markdown-body :deep(h3) { font-size: 1.1rem; }
}
</style>