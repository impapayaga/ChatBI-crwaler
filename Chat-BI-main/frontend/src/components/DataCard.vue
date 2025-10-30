<template>
  <v-card class="data-card" elevation="2">
    <v-card-text class="pa-4">
      <!-- 如果只有一条数据，展示为字段列表 -->
      <template v-if="data.length === 1">
        <div v-for="(value, key) in data[0]" :key="key" class="field-item mb-4">
          <div class="field-label text-caption text-medium-emphasis mb-1">
            {{ key }}
          </div>
          <div class="field-value text-body-1" v-html="formatValue(value)"></div>
        </div>
      </template>

      <!-- 如果有多条数据（但不多），展示为卡片列表 -->
      <template v-else-if="data.length <= 5">
        <v-card
          v-for="(record, index) in data"
          :key="index"
          class="mb-3"
          variant="outlined"
        >
          <v-card-text>
            <div v-for="(value, key) in record" :key="key" class="field-item mb-2">
              <span class="field-label text-caption text-medium-emphasis">{{ key }}:</span>
              <span class="field-value text-body-2 ml-2" v-html="formatValue(value)"></span>
            </div>
          </v-card-text>
        </v-card>
      </template>

      <!-- 数据太多，降级到简单列表 -->
      <template v-else>
        <v-alert type="info" variant="tonal" class="mb-3">
          共 {{ data.length }} 条数据，建议使用表格查看
        </v-alert>
        <v-list>
          <v-list-item v-for="(record, index) in data.slice(0, 10)" :key="index">
            <v-list-item-title>{{ getRecordTitle(record) }}</v-list-item-title>
            <v-list-item-subtitle>{{ getRecordSubtitle(record) }}</v-list-item-subtitle>
          </v-list-item>
        </v-list>
        <div v-if="data.length > 10" class="text-center text-caption text-medium-emphasis mt-2">
          还有 {{ data.length - 10 }} 条数据未显示
        </div>
      </template>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  data: Record<string, any>[]
}

const props = defineProps<Props>()

/**
 * 格式化字段值，处理长文本和换行
 */
const formatValue = (value: any): string => {
  if (value === null || value === undefined) {
    return '<span class="text-medium-emphasis">-</span>'
  }

  const str = String(value)

  // 处理换行符
  return str.replace(/\n/g, '<br>')
}

/**
 * 获取记录的标题（第一个字段）
 */
const getRecordTitle = (record: Record<string, any>): string => {
  const firstKey = Object.keys(record)[0]
  return String(record[firstKey])
}

/**
 * 获取记录的副标题（第二个字段）
 */
const getRecordSubtitle = (record: Record<string, any>): string => {
  const keys = Object.keys(record)
  if (keys.length < 2) return ''
  const secondKey = keys[1]
  const value = String(record[secondKey])
  return value.length > 100 ? value.substring(0, 100) + '...' : value
}
</script>

<style scoped lang="scss">
.data-card {
  border-radius: 12px;
}

.field-item {
  .field-label {
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .field-value {
    line-height: 1.6;
    white-space: pre-wrap;
    word-wrap: break-word;

    :deep(br) {
      display: block;
      content: "";
      margin-top: 0.5em;
    }
  }
}

/* 暗色主题适配 */
:global(.v-theme--dark) .data-card {
  background-color: rgb(var(--v-theme-surface-variant));
}
</style>
