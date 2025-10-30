<template>
  <div class="conversation-history">
    <!-- 历史对话按钮 -->
    <v-btn
      ref="historyBtnRef"
      icon
      size="small"
      variant="text"
      class="history-btn"
      @click="toggleMenu">
      <v-icon>mdi-history</v-icon>
    </v-btn>

    <!-- 历史对话菜单 -->
    <Transition name="menu-fade">
      <div
        v-if="showMenu"
        ref="menuRef"
        class="history-menu">
        <div class="menu-header">
          <div class="menu-title">历史对话</div>
          <div class="menu-actions">
            <v-tooltip text="新建对话" location="bottom">
              <template v-slot:activator="{ props }">
                <v-btn
                  v-bind="props"
                  icon
                  size="x-small"
                  variant="text"
                  @click="createNewConversation">
                  <v-icon size="18">mdi-plus</v-icon>
                </v-btn>
              </template>
            </v-tooltip>
            <v-btn
              icon
              size="x-small"
              variant="text"
              @click="showMenu = false">
              <v-icon size="18">mdi-close</v-icon>
            </v-btn>
          </div>
        </div>

        <v-divider></v-divider>

        <div class="menu-content">
          <div v-if="isLoading" class="loading-state">
            <v-progress-circular indeterminate color="primary" size="32"></v-progress-circular>
            <p class="text-body-2 text-medium-emphasis mt-2">加载中...</p>
          </div>

          <template v-else>
            <div
              v-for="conversation in conversations"
              :key="conversation.id"
              class="conversation-item-wrapper">
              <!-- 操作按钮 - 悬停时显示在右上角 -->
              <div class="conversation-actions">
                <v-tooltip text="编辑标题" location="top">
                  <template v-slot:activator="{ props }">
                    <v-btn
                      v-bind="props"
                      icon
                      size="x-small"
                      variant="text"
                      class="action-btn"
                      @click.stop="openEditDialog(conversation)">
                      <v-icon size="16">mdi-pencil</v-icon>
                    </v-btn>
                  </template>
                </v-tooltip>
                <v-tooltip text="删除对话" location="top">
                  <template v-slot:activator="{ props }">
                    <v-btn
                      v-bind="props"
                      icon
                      size="x-small"
                      variant="text"
                      color="error"
                      class="action-btn"
                      @click.stop="openDeleteDialog(conversation)">
                      <v-icon size="16">mdi-delete</v-icon>
                    </v-btn>
                  </template>
                </v-tooltip>
              </div>

              <!-- 对话项内容 -->
              <div class="conversation-item" @click="handleSelectConversation(conversation)">
                <div class="conversation-main">
                  <div class="conversation-header">
                    <div class="conversation-name">{{ conversation.title }}</div>
                    <div class="conversation-date">{{ formatDate(conversation.last_message_time) }}</div>
                  </div>
                  <div class="conversation-footer">
                    <div class="conversation-preview">{{ conversation.last_user_message }}</div>
                    <div class="conversation-hour">{{ formatTime(conversation.last_message_time) }}</div>
                  </div>
                </div>
              </div>
            </div>

            <div v-if="conversations.length === 0" class="empty-state">
              <v-icon size="48" color="grey-lighten-1">mdi-message-outline</v-icon>
              <p class="text-body-2 text-medium-emphasis mt-2">暂无历史对话</p>
            </div>
          </template>
        </div>
      </div>
    </Transition>

    <!-- 编辑对话标题对话框 -->
    <v-dialog v-model="editDialog" max-width="500">
      <v-card>
        <v-card-title class="text-h6">编辑对话标题</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="editTitle"
            label="对话标题"
            variant="outlined"
            autofocus
            @keyup.enter="confirmEdit"
          ></v-text-field>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="editDialog = false">取消</v-btn>
          <v-btn color="primary" variant="flat" @click="confirmEdit">确认</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 删除对话确认对话框 -->
    <v-dialog v-model="deleteDialog" max-width="400">
      <v-card>
        <v-card-title class="text-h6">确认删除</v-card-title>
        <v-card-text>
          确定要删除对话 <strong>"{{ deleteTarget?.title }}"</strong> 吗？此操作无法撤销。
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="deleteDialog = false">取消</v-btn>
          <v-btn color="error" variant="flat" @click="confirmDelete">删除</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'

interface Conversation {
  id: number
  title: string
  last_user_message: string
  created_at: string
  updated_at: string
  last_message_time: string
  message_count: number
}

const emit = defineEmits<{
  (e: 'select-conversation', conversationId: number): void
  (e: 'new-conversation'): void
}>()

const showMenu = ref(false)
const historyBtnRef = ref<{ $el: HTMLElement } | HTMLElement>()
const menuRef = ref<HTMLElement>()
const conversations = ref<Conversation[]>([])
const isLoading = ref(false)

// 编辑对话框相关
const editDialog = ref(false)
const editTitle = ref('')
const editTarget = ref<Conversation | null>(null)

// 删除对话框相关
const deleteDialog = ref(false)
const deleteTarget = ref<Conversation | null>(null)

// 格式化日期时间
const formatDate = (isoString: string) => {
  const date = new Date(isoString)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}/${month}/${day}`
}

const formatTime = (isoString: string) => {
  const date = new Date(isoString)
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${hours}:${minutes}`
}

// 从后端加载历史对话列表
const loadConversations = async () => {
  isLoading.value = true
  try {
    const response = await axios.get(
      `${import.meta.env.VITE_API_BASE_URL}/api/conversations/1`,  // 使用固定用户ID=1
      { params: { limit: 20 } }
    )

    if (response.data.success) {
      conversations.value = response.data.conversations
      console.log('加载历史对话成功:', conversations.value)
    }
  } catch (error) {
    console.error('加载历史对话失败:', error)
  } finally {
    isLoading.value = false
  }
}

const toggleMenu = async () => {
  showMenu.value = !showMenu.value
  // 打开菜单时重新加载对话列表
  if (showMenu.value) {
    await loadConversations()
  }
}

const handleSelectConversation = (conversation: Conversation) => {
  console.log('选择对话:', conversation)
  emit('select-conversation', conversation.id)
  showMenu.value = false
}

// 创建新会话 - 不实际创建，只是通知父组件重置状态
const createNewConversation = () => {
  // 通知父组件进入新会话模式
  emit('new-conversation')
  // 关闭菜单
  showMenu.value = false
  console.log('触发新会话，重置到初始状态')
}

// 打开编辑对话框
const openEditDialog = (conversation: Conversation) => {
  editTarget.value = conversation
  editTitle.value = conversation.title
  editDialog.value = true
}

// 确认编辑
const confirmEdit = async () => {
  if (!editTarget.value || !editTitle.value.trim()) {
    return
  }

  if (editTitle.value.trim() === editTarget.value.title) {
    editDialog.value = false
    return
  }

  try {
    const response = await axios.put(
      `${import.meta.env.VITE_API_BASE_URL}/api/conversation/${editTarget.value.id}/title`,
      { title: editTitle.value.trim() }
    )

    if (response.data.success) {
      // 更新本地列表
      const index = conversations.value.findIndex(c => c.id === editTarget.value!.id)
      if (index !== -1) {
        conversations.value[index].title = editTitle.value.trim()
      }
      console.log('对话标题已更新')
      editDialog.value = false
    }
  } catch (error) {
    console.error('更新对话标题失败:', error)
    alert('更新失败，请稍后重试')
  }
}

// 打开删除确认对话框
const openDeleteDialog = (conversation: Conversation) => {
  deleteTarget.value = conversation
  deleteDialog.value = true
}

// 确认删除
const confirmDelete = async () => {
  if (!deleteTarget.value) {
    return
  }

  try {
    const response = await axios.delete(
      `${import.meta.env.VITE_API_BASE_URL}/api/conversation/${deleteTarget.value.id}`
    )

    if (response.data.success) {
      // 从本地列表移除
      conversations.value = conversations.value.filter(c => c.id !== deleteTarget.value!.id)
      console.log('对话已删除')
      deleteDialog.value = false
    }
  } catch (error) {
    console.error('删除对话失败:', error)
    alert('删除失败，请稍后重试')
  }
}

// 点击外部关闭菜单
const handleClickOutside = (event: MouseEvent) => {
  if (showMenu.value) {
    const target = event.target as Node
    const historyBtnEl = historyBtnRef.value && '$el' in historyBtnRef.value
      ? historyBtnRef.value.$el
      : historyBtnRef.value
    const menu = menuRef.value

    if (
      historyBtnEl && !historyBtnEl.contains(target) &&
      menu && !menu.contains(target)
    ) {
      showMenu.value = false
    }
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

// 暴露方法供父组件调用
defineExpose({
  refreshConversations: loadConversations
})
</script>

<style scoped>
.conversation-history {
  position: relative;
  display: inline-block;
}

.history-btn {
  flex-shrink: 0;
}

.history-menu {
  position: absolute;
  top: 3rem;
  left: 0;
  z-index: 2000;
  width: 400px;
  max-height: 600px;
  background-color: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.menu-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem;
}

.menu-title {
  font-size: 1rem;
  font-weight: 600;
}

.menu-actions {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.menu-content {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem 0;
}

.conversation-item-wrapper {
  position: relative;
  transition: background-color 0.2s;
  border-radius: 8px;
  margin: 0 0.5rem;
  margin-bottom: 0.25rem;
}

.conversation-item-wrapper:hover {
  background-color: rgba(var(--v-theme-on-surface), 0.08);
}

.conversation-item-wrapper:hover .conversation-actions {
  opacity: 1;
}

.conversation-item {
  padding: 0.875rem 1rem;
  cursor: pointer;
}

.conversation-actions {
  position: absolute;
  right: 0.5rem;
  top: 0.5rem;
  display: flex;
  gap: 0.25rem;
  opacity: 0;
  transition: opacity 0.2s;
  background-color: rgb(var(--v-theme-surface));
  border-radius: 6px;
  padding: 0.125rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.action-btn {
  background-color: rgba(var(--v-theme-on-surface), 0.05);
}

.action-btn:hover {
  background-color: rgba(var(--v-theme-on-surface), 0.1);
}

.conversation-main {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.conversation-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 0.5rem;
}

.conversation-name {
  font-size: 0.9375rem;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  padding-right: 3rem; /* 为操作按钮留出空间 */
}

.conversation-date {
  font-size: 0.8125rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
  flex-shrink: 0;
}

.conversation-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
}

.conversation-preview {
  font-size: 0.8125rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.conversation-hour {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  flex-shrink: 0;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
}

/* 动画 */
.menu-fade-enter-active,
.menu-fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.menu-fade-enter-from,
.menu-fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* 暗色主题适配 */
:global(.v-theme--dark) .history-menu {
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
}

/* 滚动条样式 */
.menu-content::-webkit-scrollbar {
  width: 6px;
}

.menu-content::-webkit-scrollbar-track {
  background: transparent;
}

.menu-content::-webkit-scrollbar-thumb {
  background-color: rgba(var(--v-theme-on-surface), 0.2);
  border-radius: 3px;
}

.menu-content::-webkit-scrollbar-thumb:hover {
  background-color: rgba(var(--v-theme-on-surface), 0.3);
}
</style>
