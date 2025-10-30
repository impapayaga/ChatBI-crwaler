<template>
  <v-card class="data-table-card" elevation="2">
    <v-card-text class="pa-0">
      <v-data-table
        :headers="headers"
        :items="data"
        :items-per-page="itemsPerPage"
        :items-per-page-options="[10, 25, 50, 100]"
        class="data-table"
        density="comfortable"
      >
        <!-- 自定义单元格渲染 -->
        <template v-for="header in headers" :key="header.key" v-slot:[`item.${header.key}`]="{ value }">
          <div class="cell-content">{{ formatCellValue(value) }}</div>
        </template>

        <!-- 空状态 -->
        <template v-slot:no-data>
          <div class="text-center pa-6 text-medium-emphasis">
            <v-icon size="48" color="grey-lighten-1">mdi-table-off</v-icon>
            <div class="text-body-2 mt-2">暂无数据</div>
          </div>
        </template>
      </v-data-table>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  data: Record<string, any>[]
  itemsPerPage?: number
}

const props = withDefaults(defineProps<Props>(), {
  itemsPerPage: 10
})

/**
 * 根据数据自动生成表头
 */
const headers = computed(() => {
  if (props.data.length === 0) return []

  const firstRow = props.data[0]
  return Object.keys(firstRow).map(key => ({
    title: key,
    key: key,
    sortable: true,
    align: 'start' as const,
    width: undefined
  }))
})

/**
 * 格式化单元格值
 */
const formatCellValue = (value: any): string => {
  if (value === null || value === undefined) {
    return '-'
  }

  // 处理长文本，截断显示
  const str = String(value)
  if (str.length > 100) {
    return str.substring(0, 100) + '...'
  }

  return str
}
</script>

<style scoped lang="scss">
.data-table-card {
  border-radius: 12px;
  overflow: hidden;
}

.data-table {
  :deep(.v-data-table__th) {
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-size: 0.75rem;
  }

  :deep(.v-data-table__td) {
    font-size: 0.875rem;
  }
}

.cell-content {
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 暗色主题适配 */
:global(.v-theme--dark) .data-table-card {
  background-color: rgb(var(--v-theme-surface-variant));
}
</style>
