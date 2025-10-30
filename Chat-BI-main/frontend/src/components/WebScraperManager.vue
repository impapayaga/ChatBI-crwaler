<template>
  <div class="scraper-manager-wrapper">
    <v-container fluid class="scraper-manager pa-6">
      <!-- 标题栏 -->
      <div class="d-flex align-center justify-space-between mb-4">
        <h2 class="text-h4 font-weight-bold">数据爬取管理</h2>
        <div class="d-flex gap-2">
          <v-btn
            color="success"
            prepend-icon="mdi-play"
            @click="showManualCrawlDialog = true"
          >
            手动触发爬取
          </v-btn>
          <v-btn
            color="grey"
            prepend-icon="mdi-plus"
            disabled
            title="此功能正在开发中，敬请期待"
          >
            添加爬取源
          </v-btn>
          <v-btn
            icon="mdi-refresh"
            variant="text"
            @click="loadScrapeSources"
            :loading="loading"
          />
        </div>
      </div>

      <!-- 统计卡片 -->
      <v-row class="mb-4">
        <v-col cols="12" md="3">
          <StatCard
            icon="mdi-web"
            :value="scrapeSources.length"
            label="爬取源总数"
            color="primary"
          />
        </v-col>

        <v-col cols="12" md="3">
          <StatCard
            icon="mdi-check-circle"
            :value="activeSourcesCount"
            label="活跃爬取源"
            color="success"
          />
        </v-col>

        <v-col cols="12" md="3">
          <StatCard
            icon="mdi-clock-outline"
            :value="scheduledTasksCount"
            label="定时任务"
            color="info"
          />
        </v-col>

        <v-col cols="12" md="3">
          <StatCard
            icon="mdi-database"
            :value="totalRecordsCount.toLocaleString()"
            label="爬取记录数"
            color="warning"
          />
        </v-col>
      </v-row>

      <!-- Tab切换 -->
      <v-tabs v-model="currentTab" class="mb-4" color="primary">
        <v-tab value="sources">
          <v-icon start>mdi-web</v-icon>
          爬取源管理
        </v-tab>
        <v-tab value="schedules">
          <v-icon start>mdi-calendar-clock</v-icon>
          定时任务
        </v-tab>
        <v-tab value="results">
          <v-icon start>mdi-table-eye</v-icon>
          爬取结果
        </v-tab>
      </v-tabs>

      <!-- Tab内容 -->
      <v-window v-model="currentTab">
        <!-- 爬取源管理 Tab -->
        <v-window-item value="sources">
          <v-card>
            <v-data-table
              :headers="sourceHeaders"
              :items="scrapeSources"
              :loading="loading"
              :items-per-page="10"
            >
              <template v-slot:item.url="{ item }">
                <div class="d-flex align-center">
                  <v-icon class="mr-2" size="20">mdi-link</v-icon>
                  <a :href="item.url" target="_blank" class="text-decoration-none">
                    {{ item.url }}
                  </a>
                </div>
              </template>

              <template v-slot:item.status="{ item }">
                <v-chip
                  :color="item.is_active ? 'success' : 'grey'"
                  size="small"
                  variant="flat"
                >
                  {{ item.is_active ? '活跃' : '禁用' }}
                </v-chip>
              </template>

              <template v-slot:item.last_crawl="{ item }">
                <div v-if="item.last_crawl_time">
                  <div class="text-body-2">{{ formatDate(item.last_crawl_time) }}</div>
                  <v-chip
                    v-if="item.last_crawl_status"
                    :color="getCrawlStatusColor(item.last_crawl_status)"
                    size="x-small"
                    variant="flat"
                  >
                    {{ item.last_crawl_status }}
                  </v-chip>
                </div>
                <span v-else class="text-medium-emphasis">未爬取</span>
              </template>

              <template v-slot:item.actions="{ item }">
                <div class="d-flex gap-1 justify-center">
                  <v-tooltip text="查看详情" location="top">
                    <template v-slot:activator="{ props }">
                      <v-btn
                        icon="mdi-eye"
                        size="small"
                        variant="text"
                        color="primary"
                        @click="viewSourceDetails(item)"
                        v-bind="props"
                      />
                    </template>
                  </v-tooltip>

                  <v-tooltip text="编辑" location="top">
                    <template v-slot:activator="{ props }">
                      <v-btn
                        icon="mdi-pencil"
                        size="small"
                        variant="text"
                        color="info"
                        @click="editSource(item)"
                        v-bind="props"
                      />
                    </template>
                  </v-tooltip>

                  <v-tooltip :text="item.is_active ? '禁用' : '启用'" location="top">
                    <template v-slot:activator="{ props }">
                      <v-btn
                        :icon="item.is_active ? 'mdi-pause' : 'mdi-play'"
                        size="small"
                        variant="text"
                        :color="item.is_active ? 'warning' : 'success'"
                        @click="toggleSourceStatus(item)"
                        v-bind="props"
                      />
                    </template>
                  </v-tooltip>

                  <v-tooltip text="删除" location="top">
                    <template v-slot:activator="{ props }">
                      <v-btn
                        icon="mdi-delete"
                        size="small"
                        variant="text"
                        color="error"
                        @click="confirmDeleteSource(item)"
                        v-bind="props"
                      />
                    </template>
                  </v-tooltip>
                </div>
              </template>
            </v-data-table>
          </v-card>
        </v-window-item>

        <!-- 定时任务 Tab -->
        <v-window-item value="schedules">
          <v-card>
            <v-card-title class="d-flex justify-space-between align-center">
              <span>定时任务配置</span>
              <v-btn
                color="primary"
                prepend-icon="mdi-plus"
                @click="showAddScheduleDialog = true"
              >
                添加定时任务
              </v-btn>
            </v-card-title>
            <v-data-table
              :headers="scheduleHeaders"
              :items="schedules"
              :loading="loading"
              :items-per-page="10"
            >
              <template v-slot:item.source="{ item }">
                <div class="d-flex align-center">
                  <v-icon class="mr-2" size="20">mdi-web</v-icon>
                  {{ getSourceName(item.source_id) }}
                </div>
              </template>

              <template v-slot:item.schedule="{ item }">
                <div>
                  <v-chip size="small" variant="tonal" color="primary" class="mr-1">
                    {{ item.cron_expression }}
                  </v-chip>
                  <div class="text-caption text-medium-emphasis mt-1">
                    {{ item.description }}
                  </div>
                </div>
              </template>

              <template v-slot:item.status="{ item }">
                <v-chip
                  :color="item.is_enabled ? 'success' : 'grey'"
                  size="small"
                  variant="flat"
                >
                  {{ item.is_enabled ? '运行中' : '已暂停' }}
                </v-chip>
              </template>

              <template v-slot:item.actions="{ item }">
                <div class="d-flex gap-1 justify-center">
                  <v-tooltip :text="item.is_enabled ? '暂停' : '启用'" location="top">
                    <template v-slot:activator="{ props }">
                      <v-btn
                        :icon="item.is_enabled ? 'mdi-pause' : 'mdi-play'"
                        size="small"
                        variant="text"
                        :color="item.is_enabled ? 'warning' : 'success'"
                        @click="toggleScheduleStatus(item)"
                        v-bind="props"
                      />
                    </template>
                  </v-tooltip>

                  <v-tooltip text="编辑" location="top">
                    <template v-slot:activator="{ props }">
                      <v-btn
                        icon="mdi-pencil"
                        size="small"
                        variant="text"
                        color="info"
                        @click="editSchedule(item)"
                        v-bind="props"
                      />
                    </template>
                  </v-tooltip>

                  <v-tooltip text="删除" location="top">
                    <template v-slot:activator="{ props }">
                      <v-btn
                        icon="mdi-delete"
                        size="small"
                        variant="text"
                        color="error"
                        @click="confirmDeleteSchedule(item)"
                        v-bind="props"
                      />
                    </template>
                  </v-tooltip>
                </div>
              </template>
            </v-data-table>
          </v-card>
        </v-window-item>

        <!-- 爬取结果 Tab -->
        <v-window-item value="results">
          <v-card>
            <v-card-title>
              <v-row>
                <v-col cols="12" md="4">
                  <v-select
                    v-model="selectedSourceFilter"
                    :items="sourceFilterOptions"
                    label="筛选爬取源"
                    density="compact"
                    clearable
                  />
                </v-col>
                <v-col cols="12" md="4">
                  <v-select
                    v-model="selectedStatusFilter"
                    :items="statusFilterOptions"
                    label="筛选状态"
                    density="compact"
                    clearable
                  />
                </v-col>
              </v-row>
            </v-card-title>
            <v-data-table
              :headers="resultHeaders"
              :items="filteredResults"
              :loading="loading"
              :items-per-page="20"
            >
              <template v-slot:item.source="{ item }">
                <div class="d-flex align-center">
                  <v-avatar size="24" class="mr-2" color="primary">
                    <v-icon size="16">mdi-web</v-icon>
                  </v-avatar>
                  {{ getSourceName(item.source_id) }}
                </div>
              </template>

              <template v-slot:item.status="{ item }">
                <v-chip
                  :color="getCrawlStatusColor(item.status)"
                  size="small"
                  variant="flat"
                >
                  <v-icon size="16" start>{{ getCrawlStatusIcon(item.status) }}</v-icon>
                  {{ item.status }}
                </v-chip>
              </template>

              <template v-slot:item.records_count="{ item }">
                <div class="text-center">
                  <div class="text-h6">{{ item.records_count || 0 }}</div>
                  <div class="text-caption text-medium-emphasis">条记录</div>
                </div>
              </template>

              <template v-slot:item.crawl_time="{ item }">
                <div>
                  <div class="text-body-2">{{ formatDate(item.start_time) }}</div>
                  <div v-if="item.end_time" class="text-caption text-medium-emphasis">
                    耗时: {{ calculateDuration(item.start_time, item.end_time) }}
                  </div>
                </div>
              </template>

              <template v-slot:item.actions="{ item }">
                <div class="d-flex gap-1 justify-center">
                  <v-tooltip text="查看详情" location="top">
                    <template v-slot:activator="{ props }">
                      <v-btn
                        icon="mdi-eye"
                        size="small"
                        variant="text"
                        color="primary"
                        @click="viewResultDetails(item)"
                        v-bind="props"
                      />
                    </template>
                  </v-tooltip>

                  <v-tooltip text="查看数据" location="top">
                    <template v-slot:activator="{ props }">
                      <v-btn
                        icon="mdi-database-eye"
                        size="small"
                        variant="text"
                        color="info"
                        @click="viewCrawledData(item)"
                        v-bind="props"
                        :disabled="!item.records_count"
                      />
                    </template>
                  </v-tooltip>
                </div>
              </template>
            </v-data-table>
          </v-card>
        </v-window-item>
      </v-window>
    </v-container>

    <!-- 添加爬取源对话框 -->
    <v-dialog v-model="showAddSourceDialog" max-width="600">
      <v-card>
        <v-card-title>{{ editingSource ? '编辑爬取源' : '添加爬取源' }}</v-card-title>
        <v-divider />
        <v-card-text class="pt-4">
          <v-form ref="sourceForm">
            <v-text-field
              v-model="sourceFormData.name"
              label="爬取源名称"
              placeholder="例如：政府公告网站"
              :rules="[v => !!v || '请输入名称']"
              required
            />
            <v-text-field
              v-model="sourceFormData.url"
              label="目标URL"
              placeholder="https://example.com"
              :rules="[v => !!v || '请输入URL', v => isValidUrl(v) || '请输入有效的URL']"
              required
            />
            <v-textarea
              v-model="sourceFormData.description"
              label="描述"
              placeholder="描述此爬取源的用途..."
              rows="3"
            />
            <v-textarea
              v-model="sourceFormData.crawl_rules"
              label="爬取规则 (JSON)"
              placeholder='{"selector": ".content", "fields": ["title", "date"]}'
              rows="5"
            />
            <v-switch
              v-model="sourceFormData.is_active"
              label="启用此爬取源"
              color="success"
            />
          </v-form>
        </v-card-text>
        <v-divider />
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="closeSourceDialog">取消</v-btn>
          <v-btn color="primary" variant="tonal" @click="saveSource">
            {{ editingSource ? '保存' : '添加' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 添加定时任务对话框 -->
    <v-dialog v-model="showAddScheduleDialog" max-width="600">
      <v-card>
        <v-card-title>{{ editingSchedule ? '编辑定时任务' : '添加定时任务' }}</v-card-title>
        <v-divider />
        <v-card-text class="pt-4">
          <v-form ref="scheduleForm">
            <v-select
              v-model="scheduleFormData.source_id"
              :items="scrapeSources"
              item-title="name"
              item-value="id"
              label="选择爬取源"
              :rules="[v => !!v || '请选择爬取源']"
              required
            />
            <v-text-field
              v-model="scheduleFormData.cron_expression"
              label="Cron表达式"
              placeholder="0 0 * * *"
              hint="例如: 0 0 * * * 表示每天0点执行"
              persistent-hint
              :rules="[v => !!v || '请输入Cron表达式']"
            />
            <v-text-field
              v-model="scheduleFormData.description"
              label="任务描述"
              placeholder="例如：每天凌晨爬取"
            />
            <v-switch
              v-model="scheduleFormData.is_enabled"
              label="启用此定时任务"
              color="success"
            />
          </v-form>
        </v-card-text>
        <v-divider />
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="closeScheduleDialog">取消</v-btn>
          <v-btn color="primary" variant="tonal" @click="saveSchedule">
            {{ editingSchedule ? '保存' : '添加' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 手动触发爬取对话框 -->
    <v-dialog v-model="showManualCrawlDialog" max-width="500">
      <v-card>
        <v-card-title>手动触发爬取</v-card-title>
        <v-divider />
        <v-card-text class="pt-4">
          <v-select
            v-model="manualCrawlSourceId"
            :items="activeScrapeSources"
            item-title="name"
            item-value="id"
            label="选择爬取源"
            placeholder="请选择要爬取的数据源"
          />
        </v-card-text>
        <v-divider />
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showManualCrawlDialog = false">取消</v-btn>
          <v-btn
            color="success"
            variant="tonal"
            @click="triggerManualCrawl"
            :disabled="!manualCrawlSourceId"
            :loading="crawling"
          >
            开始爬取
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 爬取结果详情对话框 -->
    <v-dialog v-model="showResultDetailsDialog" max-width="1400" scrollable>
      <v-card v-if="selectedResult">
        <v-card-title class="d-flex justify-space-between align-center">
          <span>爬取详情 - {{ getSourceName(selectedResult.source_id) }}</span>
          <v-btn icon="mdi-close" variant="text" @click="showResultDetailsDialog = false" />
        </v-card-title>
        <v-divider />
        <v-card-text style="height: 80vh" class="pa-0">
          <v-row no-gutters style="height: 100%">
            <!-- 左侧：目标站点预览 -->
            <v-col cols="12" md="6" class="border-e" style="height: 100%">
              <div class="pa-4" style="height: 100%; display: flex; flex-direction: column;">
                <div class="d-flex justify-space-between align-center mb-2">
                  <h3 class="text-h6">目标站点预览</h3>
                  <v-btn
                    :href="getSourceUrl(selectedResult.source_id)"
                    target="_blank"
                    variant="text"
                    size="small"
                    append-icon="mdi-open-in-new"
                  >
                    在新窗口打开
                  </v-btn>
                </div>
                <v-divider class="mb-4" />
                <iframe
                  :src="getSourceUrl(selectedResult.source_id)"
                  style="width: 100%; flex: 1; border: 1px solid rgba(0,0,0,0.12); border-radius: 4px;"
                  sandbox="allow-same-origin allow-scripts"
                />
              </div>
            </v-col>

            <!-- 右侧：爬取规则和结果 -->
            <v-col cols="12" md="6" style="height: 100%; overflow-y: auto;">
              <div class="pa-4">
                <!-- 基本信息 -->
                <div class="mb-4">
                  <h3 class="text-h6 mb-3">基本信息</h3>
                  <v-list density="compact">
                    <v-list-item>
                      <template v-slot:prepend>
                        <v-icon>mdi-clock-start</v-icon>
                      </template>
                      <v-list-item-title>开始时间</v-list-item-title>
                      <v-list-item-subtitle>{{ formatDate(selectedResult.start_time) }}</v-list-item-subtitle>
                    </v-list-item>
                    <v-list-item v-if="selectedResult.end_time">
                      <template v-slot:prepend>
                        <v-icon>mdi-clock-end</v-icon>
                      </template>
                      <v-list-item-title>结束时间</v-list-item-title>
                      <v-list-item-subtitle>
                        {{ formatDate(selectedResult.end_time) }}
                        (耗时: {{ calculateDuration(selectedResult.start_time, selectedResult.end_time) }})
                      </v-list-item-subtitle>
                    </v-list-item>
                    <v-list-item>
                      <template v-slot:prepend>
                        <v-icon>mdi-database</v-icon>
                      </template>
                      <v-list-item-title>爬取记录数</v-list-item-title>
                      <v-list-item-subtitle>{{ selectedResult.records_count || 0 }} 条</v-list-item-subtitle>
                    </v-list-item>
                    <v-list-item>
                      <template v-slot:prepend>
                        <v-icon :color="getCrawlStatusColor(selectedResult.status)">
                          {{ getCrawlStatusIcon(selectedResult.status) }}
                        </v-icon>
                      </template>
                      <v-list-item-title>状态</v-list-item-title>
                      <v-list-item-subtitle>
                        <v-chip :color="getCrawlStatusColor(selectedResult.status)" size="small">
                          {{ selectedResult.status }}
                        </v-chip>
                      </v-list-item-subtitle>
                    </v-list-item>
                  </v-list>
                </div>

                <v-divider class="my-4" />

                <!-- 爬取规则 -->
                <div class="mb-4">
                  <h3 class="text-h6 mb-3">爬取规则</h3>
                  <v-card variant="tonal">
                    <v-card-text>
                      <pre class="text-caption">{{ formatJson(selectedResult.crawl_rules) }}</pre>
                    </v-card-text>
                  </v-card>
                </div>

                <v-divider class="my-4" />

                <!-- 错误信息 -->
                <div v-if="selectedResult.error_message" class="mb-4">
                  <h3 class="text-h6 mb-3 text-error">错误信息</h3>
                  <v-alert type="error" variant="tonal">
                    {{ selectedResult.error_message }}
                  </v-alert>
                </div>

                <!-- 爬取结果预览 -->
                <div v-if="selectedResult.records_count && selectedResult.records_count > 0">
                  <h3 class="text-h6 mb-3">爬取结果预览</h3>
                  <v-btn
                    color="primary"
                    variant="tonal"
                    block
                    @click="viewCrawledData(selectedResult)"
                  >
                    查看完整数据
                  </v-btn>
                </div>
              </div>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- 爬取数据查看对话框 -->
    <v-dialog v-model="showDataViewDialog" max-width="1600" scrollable>
      <v-card v-if="selectedCrawlData">
        <v-card-title class="d-flex justify-space-between align-center">
          <span>爬取数据 - {{ getSourceName(selectedCrawlData.source_id) }}</span>
          <div class="d-flex gap-2">
            <v-btn
              color="primary"
              variant="text"
              prepend-icon="mdi-download"
              @click="exportData"
            >
              导出数据
            </v-btn>
            <v-btn icon="mdi-close" variant="text" @click="showDataViewDialog = false" />
          </div>
        </v-card-title>
        <v-divider />
        <v-card-text style="max-height: 70vh">
          <v-data-table
            :headers="dataTableHeaders"
            :items="crawledDataItems"
            :items-per-page="20"
            density="compact"
            class="custom-table"
            :item-class="getItemClass"
          >
            <template v-slot:item.url="{ item, value }">
              <div style="max-width: 420px; word-break: break-all; word-wrap: break-word; line-height: 1.2;">
                <a
                  :href="formatUrl(value)"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="text-decoration-underline"
                  :title="value"
                  @click.stop
                >
                  {{ value }}
                </a>
              </div>
            </template>
          </v-data-table>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- Snackbar -->
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="3000">
      {{ snackbar.text }}
    </v-snackbar>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import StatCard from '@/components/StatCard.vue'

// 使用Crawler适配API (端口8001)
const API_BASE_URL = import.meta.env.VITE_CRAWLER_API_BASE_URL || 'http://localhost:8001'

interface ScrapeSource {
  id: string
  name: string
  url: string
  description?: string
  crawl_rules?: string
  is_active: boolean
  last_crawl_time?: string
  last_crawl_status?: string
  created_at: string
}

interface Schedule {
  id: string
  source_id: string
  cron_expression: string
  description?: string
  is_enabled: boolean
  created_at: string
}

interface CrawlResult {
  id: string
  source_id: string
  status: string
  start_time: string
  end_time?: string
  records_count?: number
  crawl_rules?: string
  error_message?: string
  created_at?: string
}

const currentTab = ref('sources')
const loading = ref(false)
const crawling = ref(false)

// 爬取源数据
const scrapeSources = ref<ScrapeSource[]>([])
const schedules = ref<Schedule[]>([])
const crawlResults = ref<CrawlResult[]>([])

// 筛选
const selectedSourceFilter = ref<string | null>(null)
const selectedStatusFilter = ref<string | null>(null)

// 对话框
const showAddSourceDialog = ref(false)
const showAddScheduleDialog = ref(false)
const showManualCrawlDialog = ref(false)
const showResultDetailsDialog = ref(false)
const showDataViewDialog = ref(false)

// 编辑状态
const editingSource = ref<ScrapeSource | null>(null)
const editingSchedule = ref<Schedule | null>(null)

// 表单数据
const sourceFormData = ref({
  name: '',
  url: '',
  description: '',
  crawl_rules: '',
  is_active: true
})

const scheduleFormData = ref({
  source_id: '',
  cron_expression: '',
  description: '',
  is_enabled: true
})

const manualCrawlSourceId = ref<string | null>(null)
const selectedResult = ref<CrawlResult | null>(null)
const selectedCrawlData = ref<CrawlResult | null>(null)
const crawledDataItems = ref<any[]>([])

const snackbar = ref({
  show: false,
  text: '',
  color: 'success'
})

// 表头定义
const sourceHeaders = [
  { title: '名称', key: 'name', sortable: true },
  { title: 'URL', key: 'url', sortable: false },
  { title: '状态', key: 'status', sortable: true },
  { title: '最后爬取', key: 'last_crawl', sortable: false },
  { title: '操作', key: 'actions', sortable: false, align: 'center' as const }
]

const scheduleHeaders = [
  { title: '爬取源', key: 'source', sortable: true },
  { title: '定时配置', key: 'schedule', sortable: false },
  { title: '状态', key: 'status', sortable: true },
  { title: '操作', key: 'actions', sortable: false, align: 'center' as const }
]

const resultHeaders = [
  { title: '爬取源', key: 'source', sortable: true },
  { title: '状态', key: 'status', sortable: true },
  { title: '记录数', key: 'records_count', sortable: true },
  { title: '爬取时间', key: 'crawl_time', sortable: true },
  { title: '操作', key: 'actions', sortable: false, align: 'center' as const }
]

// 计算属性
const activeSourcesCount = computed(() => {
  return scrapeSources.value.filter(s => s.is_active).length
})

const scheduledTasksCount = computed(() => {
  return schedules.value.filter(s => s.is_enabled).length
})

const totalRecordsCount = computed(() => {
  return crawlResults.value.reduce((sum, r) => sum + (r.records_count || 0), 0)
})

const activeScrapeSources = computed(() => {
  return scrapeSources.value.filter(s => s.is_active)
})

const sourceFilterOptions = computed(() => {
  return scrapeSources.value.map(s => ({ title: s.name, value: s.id }))
})

const statusFilterOptions = [
  { title: '成功', value: '成功' },
  { title: '失败', value: '失败' },
  { title: '进行中', value: '进行中' }
]

const filteredResults = computed(() => {
  let results = crawlResults.value
  if (selectedSourceFilter.value) {
    results = results.filter(r => r.source_id === selectedSourceFilter.value)
  }
  if (selectedStatusFilter.value) {
    results = results.filter(r => r.status === selectedStatusFilter.value)
  }
  return results
})

const dataTableHeaders = computed(() => {
  if (crawledDataItems.value.length === 0) return []
  const firstItem = crawledDataItems.value[0]
  const headers = []
  Object.keys(firstItem).forEach(key => {
    let width = undefined
    let sortable = true
    
    // 根据列名设置不同的宽度和属性
    if (key === 'title') {
      width = '400px'  // title列设置更宽
      sortable = true
    } else if (key === 'url') {
      width = '50px'  // url列再次减半
      sortable = false
    } else if (key === 'content') {
      width = '800px'  // content列最宽
      sortable = false
    } else if (key === 'publish_date') {
      width = '120px'  // 日期列较窄
      sortable = true
    } else if (key === 'publish_unit') {
      width = '200px'  // 发布单位列适中
      sortable = true
    } else if (key === 'keywords_found') {
      width = '200px'  // 关键词列适中
      sortable = false
    } else if (key === 'source') {
      width = '150px'  // 来源列较窄
      sortable = true
    }
    
    headers.push({ 
      title: key, 
      key,
      width: width,
      sortable: sortable,
      cellClass: key === 'url' ? 'url-cell' : '',
      headerClass: key === 'url' ? 'url-header' : ''
    })
  })
  return headers
})

// 为表格行添加CSS类名
const getItemClass = (item: any) => {
  return 'table-row-item'
}

// 加载数据
const loadScrapeSources = async () => {
  loading.value = true
  try {
    // 这里调用你的API - 示例使用模拟数据
    const response = await axios.get(`${API_BASE_URL}/api/scraper/sources`)
    scrapeSources.value = response.data || []
  } catch (error) {
    console.error('加载爬取源失败:', error)
    // 使用模拟数据
    scrapeSources.value = [
      {
        id: '1',
        name: '政府公告网站',
        url: 'https://www.gov.cn/xinwen/index.htm',
        description: '政府官方公告和新闻',
        is_active: true,
        last_crawl_time: new Date().toISOString(),
        last_crawl_status: '成功',
        created_at: new Date().toISOString()
      },
      {
        id: '2',
        name: '行业数据平台',
        url: 'https://data.stats.gov.cn/',
        description: '统计局数据',
        is_active: true,
        created_at: new Date().toISOString()
      }
    ]
  } finally {
    loading.value = false
  }
}

const loadSchedules = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/scraper/schedules`)
    schedules.value = response.data || []
  } catch (error) {
    console.error('加载定时任务失败:', error)
    // 模拟数据
    schedules.value = [
      {
        id: '1',
        source_id: '1',
        cron_expression: '0 0 * * *',
        description: '每天凌晨0点爬取',
        is_enabled: true,
        created_at: new Date().toISOString()
      }
    ]
  }
}

const loadCrawlResults = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/scraper/results`)
    crawlResults.value = response.data || []
  } catch (error) {
    console.error('加载爬取结果失败:', error)
    // 模拟数据
    crawlResults.value = [
      {
        id: '1',
        source_id: '1',
        status: '成功',
        start_time: new Date(Date.now() - 3600000).toISOString(),
        end_time: new Date().toISOString(),
        records_count: 125,
        created_at: new Date().toISOString()
      }
    ]
  }
}

// 工具函数
const getSourceName = (sourceId: string) => {
  const source = scrapeSources.value.find(s => s.id === sourceId)
  return source?.name || '未知源'
}

const getSourceUrl = (sourceId: string) => {
  const source = scrapeSources.value.find(s => s.id === sourceId)
  return source?.url || ''
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const calculateDuration = (start: string, end: string) => {
  const duration = new Date(end).getTime() - new Date(start).getTime()
  const seconds = Math.floor(duration / 1000)
  if (seconds < 60) return `${seconds}秒`
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}分${seconds % 60}秒`
  const hours = Math.floor(minutes / 60)
  return `${hours}小时${minutes % 60}分`
}

const getCrawlStatusColor = (status: string) => {
  switch (status) {
    case '成功':
      return 'success'
    case '失败':
      return 'error'
    case '进行中':
      return 'primary'
    default:
      return 'grey'
  }
}

const getCrawlStatusIcon = (status: string) => {
  switch (status) {
    case '成功':
      return 'mdi-check-circle'
    case '失败':
      return 'mdi-alert-circle'
    case '进行中':
      return 'mdi-loading mdi-spin'
    default:
      return 'mdi-help-circle'
  }
}

const formatJson = (jsonStr?: string) => {
  if (!jsonStr) return '{}'
  try {
    return JSON.stringify(JSON.parse(jsonStr), null, 2)
  } catch {
    return jsonStr
  }
}

const isValidUrl = (url: string) => {
  try {
    new URL(url)
    return true
  } catch {
    return false
  }
}

const formatUrl = (u: string) => {
  if (!u) return '#'
  const url = u.trim()
  // 已有协议
  if (/^https?:\/\//i.test(url)) return encodeURI(url)
  // 可能是相对路径或省略协议的域名，默认补 https
  return encodeURI(`https://${url}`)
}

// 操作函数
const viewSourceDetails = (source: ScrapeSource) => {
  // 可以打开详情对话框
  showSnackbar(`查看 ${source.name} 的详情`)
}

const editSource = (source: ScrapeSource) => {
  editingSource.value = source
  sourceFormData.value = {
    name: source.name,
    url: source.url,
    description: source.description || '',
    crawl_rules: source.crawl_rules || '',
    is_active: source.is_active
  }
  showAddSourceDialog.value = true
}

const toggleSourceStatus = async (source: ScrapeSource) => {
  try {
    await axios.patch(`${API_BASE_URL}/api/scraper/source/${source.id}/toggle`)
    source.is_active = !source.is_active
    showSnackbar(`已${source.is_active ? '启用' : '禁用'} ${source.name}`)
  } catch (error) {
    showSnackbar('操作失败', 'error')
  }
}

const confirmDeleteSource = (source: ScrapeSource) => {
  if (confirm(`确定要删除爬取源"${source.name}"吗？`)) {
    deleteSource(source.id)
  }
}

const deleteSource = async (id: string) => {
  try {
    await axios.delete(`${API_BASE_URL}/api/scraper/source/${id}`)
    scrapeSources.value = scrapeSources.value.filter(s => s.id !== id)
    showSnackbar('删除成功')
  } catch (error) {
    showSnackbar('删除失败', 'error')
  }
}

const saveSource = async () => {
  try {
    if (editingSource.value) {
      await axios.put(`${API_BASE_URL}/api/scraper/source/${editingSource.value.id}`, sourceFormData.value)
      showSnackbar('保存成功')
    } else {
      await axios.post(`${API_BASE_URL}/api/scraper/source`, sourceFormData.value)
      showSnackbar('添加成功')
    }
    closeSourceDialog()
    loadScrapeSources()
  } catch (error) {
    showSnackbar('操作失败', 'error')
  }
}

const closeSourceDialog = () => {
  showAddSourceDialog.value = false
  editingSource.value = null
  sourceFormData.value = {
    name: '',
    url: '',
    description: '',
    crawl_rules: '',
    is_active: true
  }
}

const editSchedule = (schedule: Schedule) => {
  editingSchedule.value = schedule
  scheduleFormData.value = {
    source_id: schedule.source_id,
    cron_expression: schedule.cron_expression,
    description: schedule.description || '',
    is_enabled: schedule.is_enabled
  }
  showAddScheduleDialog.value = true
}

const toggleScheduleStatus = async (schedule: Schedule) => {
  try {
    await axios.patch(`${API_BASE_URL}/api/scraper/schedule/${schedule.id}/toggle`)
    schedule.is_enabled = !schedule.is_enabled
    showSnackbar(`已${schedule.is_enabled ? '启用' : '暂停'}定时任务`)
  } catch (error) {
    showSnackbar('操作失败', 'error')
  }
}

const confirmDeleteSchedule = (schedule: Schedule) => {
  if (confirm(`确定要删除此定时任务吗？`)) {
    deleteSchedule(schedule.id)
  }
}

const deleteSchedule = async (id: string) => {
  try {
    await axios.delete(`${API_BASE_URL}/api/scraper/schedule/${id}`)
    schedules.value = schedules.value.filter(s => s.id !== id)
    showSnackbar('删除成功')
  } catch (error) {
    showSnackbar('删除失败', 'error')
  }
}

const saveSchedule = async () => {
  try {
    if (editingSchedule.value) {
      await axios.put(`${API_BASE_URL}/api/scraper/schedule/${editingSchedule.value.id}`, scheduleFormData.value)
      showSnackbar('保存成功')
    } else {
      await axios.post(`${API_BASE_URL}/api/scraper/schedule`, scheduleFormData.value)
      showSnackbar('添加成功')
    }
    closeScheduleDialog()
    loadSchedules()
  } catch (error) {
    showSnackbar('操作失败', 'error')
  }
}

const closeScheduleDialog = () => {
  showAddScheduleDialog.value = false
  editingSchedule.value = null
  scheduleFormData.value = {
    source_id: '',
    cron_expression: '',
    description: '',
    is_enabled: true
  }
}

const triggerManualCrawl = async () => {
  if (!manualCrawlSourceId.value) return

  crawling.value = true
  try {
    await axios.post(`${API_BASE_URL}/api/scraper/crawl`, {
      source_id: manualCrawlSourceId.value
    })
    showSnackbar('爬取任务已启动，请稍后查看结果')
    showManualCrawlDialog.value = false
    manualCrawlSourceId.value = null

    // 刷新结果
    setTimeout(() => {
      loadCrawlResults()
    }, 2000)
  } catch (error) {
    showSnackbar('启动爬取任务失败', 'error')
  } finally {
    crawling.value = false
  }
}

const viewResultDetails = (result: CrawlResult) => {
  selectedResult.value = result
  showResultDetailsDialog.value = true
}

const viewCrawledData = async (result: CrawlResult) => {
  selectedCrawlData.value = result
  try {
    const response = await axios.get(`${API_BASE_URL}/api/scraper/result/${result.id}/data`)
    crawledDataItems.value = response.data.items || []
    showDataViewDialog.value = true
  } catch (error) {
    // 模拟数据 - 使用与真实数据一致的结构
    crawledDataItems.value = [
      { 
        title: '示例标题1', 
        source: '北京市政府',
        url: 'https://example.com/policy1',
        publish_date: '2025-01-20', 
        publish_unit: '示例发布单位',
        keywords_found: '人工智能,政策',
        content: '示例内容1' 
      },
      { 
        title: '示例标题2', 
        source: '北京市政府',
        url: 'https://example.com/policy2',
        publish_date: '2025-01-20', 
        publish_unit: '示例发布单位',
        keywords_found: '科技创新,发展',
        content: '示例内容2' 
      }
    ]
    showDataViewDialog.value = true
  }
}

const exportData = () => {
  // 导出CSV
  const csvContent = convertToCSV(crawledDataItems.value)
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `crawl_data_${Date.now()}.csv`
  link.click()
  showSnackbar('数据已导出')
}

const convertToCSV = (data: any[]) => {
  if (data.length === 0) return ''
  const headers = Object.keys(data[0])
  const rows = data.map(item => headers.map(h => item[h]).join(','))
  return [headers.join(','), ...rows].join('\n')
}

const showSnackbar = (text: string, color: string = 'success') => {
  snackbar.value = { show: true, text, color }
}

onMounted(() => {
  loadScrapeSources()
  loadSchedules()
  loadCrawlResults()
})
</script>

<style scoped>
.scraper-manager-wrapper {
  height: 100vh;
  width: 100%;
  overflow-y: auto;
}


.scraper-manager {
  min-height: 100%;
}

/* 强制设置表格列宽 */
.custom-table :deep(.v-data-table__wrapper table) {
  table-layout: fixed !important;
  width: 100% !important;
}

.custom-table :deep(.v-data-table__wrapper table th),
.custom-table :deep(.v-data-table__wrapper table td) {
  box-sizing: border-box !important;
}

/* 强制设置各列宽度 - 移除全局white-space设置，避免冲突 */
.custom-table :deep(.v-data-table__wrapper table th),
.custom-table :deep(.v-data-table__wrapper table td) {
  overflow: hidden !important;
  text-overflow: ellipsis !important;
}

/* 第一列 - title */
.custom-table :deep(.v-data-table__wrapper table th:nth-child(1)),
.custom-table :deep(.v-data-table__wrapper table td:nth-child(1)) {
  width: 400px !important;
  min-width: 400px !important;
  max-width: 400px !important;
  white-space: normal !important;
  word-wrap: break-word !important;
}

/* 第二列 - source */
.custom-table :deep(.v-data-table__wrapper table th:nth-child(2)),
.custom-table :deep(.v-data-table__wrapper table td:nth-child(2)) {
  width: 150px !important;
  min-width: 150px !important;
  max-width: 150px !important;
}

/* URL列 - 清理CSS，因为现在使用模板方法 */

/* 第四列 - publish_date */
.custom-table :deep(.v-data-table__wrapper table th:nth-child(4)),
.custom-table :deep(.v-data-table__wrapper table td:nth-child(4)) {
  width: 120px !important;
  min-width: 120px !important;
  max-width: 120px !important;
}

/* 第五列 - publish_unit */
.custom-table :deep(.v-data-table__wrapper table th:nth-child(5)),
.custom-table :deep(.v-data-table__wrapper table td:nth-child(5)) {
  width: 200px !important;
  min-width: 200px !important;
  max-width: 200px !important;
  white-space: normal !important;
  word-wrap: break-word !important;
}

/* 第六列 - keywords_found */
.custom-table :deep(.v-data-table__wrapper table th:nth-child(6)),
.custom-table :deep(.v-data-table__wrapper table td:nth-child(6)) {
  width: 200px !important;
  min-width: 200px !important;
  max-width: 200px !important;
  white-space: normal !important;
  word-wrap: break-word !important;
}

/* 第七列 - content */
.custom-table :deep(.v-data-table__wrapper table th:nth-child(7)),
.custom-table :deep(.v-data-table__wrapper table td:nth-child(7)) {
  width: 800px !important;
  min-width: 800px !important;
  max-width: 800px !important;
  white-space: normal !important;
  word-wrap: break-word !important;
  line-height: 1.4 !important;
}

.gap-2 {
  gap: 0.5rem;
}

.gap-1 {
  gap: 4px;
}

</style>
