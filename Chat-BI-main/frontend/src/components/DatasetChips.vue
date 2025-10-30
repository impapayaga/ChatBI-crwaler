<template>
  <div v-if="datasets.length > 0" class="dataset-chips-container">
    <div class="chips-wrapper">
      <v-chip
        v-for="dataset in datasets"
        :key="dataset.id"
        closable
        size="small"
        variant="tonal"
        color="primary"
        class="dataset-chip"
        @click="openPreview(dataset)"
        @click:close="removeDataset(dataset.id)"
      >
        <v-icon start size="16">mdi-table</v-icon>
        <span class="chip-text">{{ dataset.logical_name || dataset.name }}</span>
        <v-tooltip activator="parent" location="top">
          <div class="tooltip-content">
            <div class="tooltip-title">{{ dataset.logical_name || dataset.name }}</div>
            <div class="tooltip-row">
              <v-icon size="12">mdi-file</v-icon>
              <span>{{ dataset.name }}</span>
            </div>
            <div class="tooltip-row">
              <v-icon size="12">mdi-database</v-icon>
              <span>{{ dataset.row_count }} 行 × {{ dataset.column_count }} 列</span>
            </div>
            <div class="tooltip-hint">
              点击 × 移除
            </div>
          </div>
        </v-tooltip>
      </v-chip>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Dataset {
  id: string
  name: string
  logical_name?: string
  row_count: number
  column_count: number
}

interface Props {
  datasets: Dataset[]
}

interface Emits {
  (e: 'remove', datasetId: string): void
  (e: 'preview', dataset: Dataset): void
}

defineProps<Props>()
const emit = defineEmits<Emits>()

const removeDataset = (datasetId: string) => {
  emit('remove', datasetId)
}

const openPreview = (dataset: Dataset) => {
  emit('preview', dataset)
}
</script>

<style scoped>
.dataset-chips-container {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  padding-bottom: 0.5rem;
  background-color: transparent;
  border: 1px solid currentColor;
  border-bottom: none;
  border-radius: 1.5rem 1.5rem 0 0;
}

.chips-wrapper {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  overflow-x: auto;
  overflow-y: hidden;
  flex: 1;
  /* 隐藏滚动条但保持可滚动 */
  scrollbar-width: thin;
  scrollbar-color: rgba(var(--v-theme-on-surface), 0.2) transparent;
}

.chips-wrapper::-webkit-scrollbar {
  height: 4px;
}

.chips-wrapper::-webkit-scrollbar-track {
  background: transparent;
}

.chips-wrapper::-webkit-scrollbar-thumb {
  background-color: rgba(var(--v-theme-on-surface), 0.2);
  border-radius: 2px;
}

.chips-wrapper::-webkit-scrollbar-thumb:hover {
  background-color: rgba(var(--v-theme-on-surface), 0.3);
}

.dataset-chip {
  flex-shrink: 0;
  cursor: default;
}

.chip-text {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tooltip-content {
  padding: 0.5rem;
  line-height: 1.5;
}

.tooltip-title {
  font-weight: 600;
  font-size: 0.875rem;
  margin-bottom: 0.5rem;
  color: white;
}

.tooltip-row {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.75rem;
  margin-bottom: 0.25rem;
  color: rgba(255, 255, 255, 0.9);
}

.tooltip-hint {
  font-size: 0.75rem;
  margin-top: 0.5rem;
  padding-top: 0.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.2);
  color: rgba(255, 255, 255, 0.7);
  font-style: italic;
}

/* 深色模式优化 - 移除背景色 */
:global(.v-theme--dark) .dataset-chips-container {
  background-color: transparent;
}
</style>
