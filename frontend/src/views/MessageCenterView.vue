<template>
  <div class="message-center">
    <a-breadcrumb class="mb-4">
      <a-breadcrumb-item>
        <router-link to="/dashboard">行情看板</router-link>
      </a-breadcrumb-item>
      <a-breadcrumb-item>消息中心</a-breadcrumb-item>
    </a-breadcrumb>

    <a-card>
      <template #title>
        <div class="flex items-center justify-between w-full">
          <span class="text-lg font-semibold">消息中心</span>
          <div class="flex gap-2">
            <a-button
              type="primary"
              :disabled="currentTypeUnread === 0"
              @click="handleMarkAllRead"
            >
              <template #icon><CheckOutlined /></template>
              全部已读
            </a-button>
          </div>
        </div>
      </template>

      <div class="message-stats mb-4 flex gap-3 flex-wrap">
        <a-statistic
          v-for="stat in stats"
          :key="stat.key"
          :title="stat.label"
          :value="stat.count"
          :value-style="{ color: stat.color }"
          class="stat-card"
          @click="switchType(stat.key)"
        />
      </div>

      <a-tabs
        v-model:activeKey="activeType"
        class="message-tabs"
        @change="onTabChange"
      >
        <a-tab-pane key="all" tab="全部消息">
          <template #tab>
            <span>全部消息</span>
            <a-badge
              v-if="unreadCount.total > 0"
              :count="unreadCount.total"
              :number-style="{ marginLeft: '4px' }"
            />
          </template>
        </a-tab-pane>
        <a-tab-pane key="announcement" tab="系统公告">
          <template #tab>
            <span>系统公告</span>
            <a-badge
              v-if="unreadCount.announcement > 0"
              :count="unreadCount.announcement"
              :number-style="{ marginLeft: '4px', backgroundColor: '#1890ff' }"
            />
          </template>
        </a-tab-pane>
        <a-tab-pane key="market_movement" tab="行情异动">
          <template #tab>
            <span>行情异动</span>
            <a-badge
              v-if="unreadCount.market_movement > 0"
              :count="unreadCount.market_movement"
              :number-style="{ marginLeft: '4px', backgroundColor: '#fa8c16' }"
            />
          </template>
        </a-tab-pane>
        <a-tab-pane key="price_alert" tab="价格预警">
          <template #tab>
            <span>价格预警</span>
            <a-badge
              v-if="unreadCount.price_alert > 0"
              :count="unreadCount.price_alert"
              :number-style="{ marginLeft: '4px', backgroundColor: '#ff4d4f' }"
            />
          </template>
        </a-tab-pane>
        <a-tab-pane key="admin_broadcast" tab="管理员广播">
          <template #tab>
            <span>管理员广播</span>
            <a-badge
              v-if="unreadCount.admin_broadcast > 0"
              :count="unreadCount.admin_broadcast"
              :number-style="{ marginLeft: '4px', backgroundColor: '#722ed1' }"
            />
          </template>
        </a-tab-pane>
      </a-tabs>

      <div class="mb-4 flex gap-3 flex-wrap items-center">
        <a-input-search
          v-model:value="searchKeyword"
          placeholder="搜索消息标题或内容"
          style="width: 280px"
          allow-clear
          @search="loadMessages(1)"
          @change="onKeywordChange"
        />
        <a-select
          v-model:value="filterRead"
          placeholder="读取状态"
          style="width: 140px"
          allow-clear
          @change="loadMessages(1)"
        >
          <a-select-option :value="false">未读</a-select-option>
          <a-select-option :value="true">已读</a-select-option>
        </a-select>
        <a-range-picker
          v-model:value="dateRange"
          show-time
          format="YYYY-MM-DD HH:mm"
          placeholder="开始-结束时间"
          style="width: 360px"
          @change="loadMessages(1)"
        />
        <a-button @click="resetFilters">
          <template #icon><ReloadOutlined /></template>
          重置筛选
        </a-button>
      </div>

      <a-spin :spinning="loading">
        <a-empty
          v-if="!loading && messages.length === 0"
          description="暂无消息"
          class="py-12"
        />
        <a-list
          v-else
          :dataSource="messages"
          :pagination="false"
          class="message-list"
        >
          <template #renderItem="{ item }">
            <a-list-item
              class="message-item"
              :class="{ 'unread': !item.is_read }"
              @click="handleMessageClick(item)"
            >
              <a-list-item-meta>
                <template #avatar>
                  <a-avatar
                    :style="{ backgroundColor: getTypeColor(item.type) }"
                    :icon="getTypeIcon(item.type)"
                  />
                </template>
                <template #title>
                  <div class="flex items-center gap-2">
                    <a-tag :color="getTypeColor(item.type)" size="small">
                      {{ getTypeLabel(item.type) }}
                    </a-tag>
                    <span class="font-medium">{{ item.title }}</span>
                    <a-badge v-if="!item.is_read" status="processing" text="未读" />
                  </div>
                </template>
                <template #description>
                  <div class="message-content">{{ item.content }}</div>
                  <div class="message-meta flex items-center justify-between mt-2">
                    <span class="text-xs text-gray-400">
                      {{ formatDateTime(item.created_at) }}
                    </span>
                    <div class="flex items-center gap-2">
                      <span v-if="item.link" class="text-xs text-blue-600 hover:text-blue-700">
                        {{ getLinkText(item.link) }} →
                      </span>
                      <a-button
                        v-if="!item.is_read"
                        type="link"
                        size="small"
                        @click.stop="handleMarkRead(item.id)"
                      >
                        标记已读
                      </a-button>
                      <a-popconfirm
                        title="确定删除这条消息吗？"
                        ok-text="删除"
                        cancel-text="取消"
                        ok-button-props="{ danger: true }"
                        @confirm.stop="handleDelete(item.id)"
                      >
                        <a-button type="link" size="small" danger>
                          <template #icon><DeleteOutlined /></template>
                          删除
                        </a-button>
                      </a-popconfirm>
                    </div>
                  </div>
                </template>
              </a-list-item-meta>
            </a-list-item>
          </template>
        </a-list>

        <div v-if="total > 0" class="mt-4 flex justify-center">
          <a-pagination
            v-model:current="currentPage"
            v-model:pageSize="pageSize"
            :total="total"
            show-size-changer
            show-quick-jumper
            :show-total="(t: number) => `共 ${t} 条消息`"
            @change="loadMessages"
          />
        </div>
      </a-spin>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  CheckOutlined,
  ReloadOutlined,
  DeleteOutlined,
  NotificationOutlined,
  TrendingUpOutlined,
  BellOutlined,
  SoundOutlined,
} from '@ant-design/icons-vue'
import type { Component } from 'vue'
import dayjs, { type Dayjs } from 'dayjs'
import {
  useMessageCenterStore,
  type Message,
  type MessageType,
  type MessageLink,
  MESSAGE_TYPE_LABEL,
  MESSAGE_TYPE_COLOR,
} from '../stores/messageCenter'
import { formatDateTime } from '../utils/format'

const router = useRouter()
const messageStore = useMessageCenterStore()

const loading = ref(false)
const activeType = ref<MessageType | 'all'>('all')
const searchKeyword = ref<string>('')
const filterRead = ref<boolean | undefined>(undefined)
const dateRange = ref<[Dayjs | null, Dayjs | null] | null>(null)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const messages = ref<Message[]>([])

const unreadCount = computed(() => messageStore.unreadCount)

const currentTypeUnread = computed(() => {
  if (activeType.value === 'all') {
    return unreadCount.value.total
  }
  return unreadCount.value[activeType.value]
})

const stats = computed(() => [
  { key: 'all' as const, label: '全部消息', count: total.value, color: '#1890ff' },
  { key: 'announcement' as MessageType, label: '系统公告', count: messageStore.messagesByType.announcement.length, color: '#1890ff' },
  { key: 'market_movement' as MessageType, label: '行情异动', count: messageStore.messagesByType.market_movement.length, color: '#fa8c16' },
  { key: 'price_alert' as MessageType, label: '价格预警', count: messageStore.messagesByType.price_alert.length, color: '#ff4d4f' },
  { key: 'admin_broadcast' as MessageType, label: '管理员广播', count: messageStore.messagesByType.admin_broadcast.length, color: '#722ed1' },
])

const typeIconMap: Record<MessageType, Component> = {
  announcement: NotificationOutlined,
  market_movement: TrendingUpOutlined,
  price_alert: BellOutlined,
  admin_broadcast: SoundOutlined,
}

function getTypeLabel(type: MessageType): string {
  return MESSAGE_TYPE_LABEL[type] || type
}

function getTypeColor(type: MessageType): string {
  return MESSAGE_TYPE_COLOR[type] || 'default'
}

function getTypeIcon(type: MessageType): Component {
  return typeIconMap[type] || BellOutlined
}

function getLinkText(link: MessageLink): string {
  switch (link.type) {
    case 'bond_detail':
      return '查看债券详情'
    case 'alert_list':
      return '查看预警列表'
    case 'market':
      return '查看行情'
    default:
      return '查看详情'
  }
}

let cachedMessages: Message[] = []
let keywordDebounceTimer: number | null = null

function onKeywordChange() {
  if (keywordDebounceTimer) clearTimeout(keywordDebounceTimer)
  keywordDebounceTimer = window.setTimeout(() => {
    applyLocalFilter()
  }, 300)
}

async function loadMessages(page = currentPage.value) {
  loading.value = true
  try {
    const params: Record<string, unknown> = {
      page,
      page_size: 500,
    }
    if (activeType.value !== 'all') {
      params.type = activeType.value
    }
    if (filterRead.value !== undefined) {
      params.is_read = filterRead.value
    }
    if (dateRange.value && dateRange.value[0]) {
      params.start_time = dateRange.value[0].toISOString()
    }
    if (dateRange.value && dateRange.value[1]) {
      params.end_time = dateRange.value[1].toISOString()
    }

    const res = await messageStore.fetchMessages(params)
    if (res) {
      cachedMessages = res.items
      total.value = res.total
      currentPage.value = res.page
      pageSize.value = res.page_size
      applyLocalFilter()
    }
  } finally {
    loading.value = false
  }
}

function applyLocalFilter() {
  let list = [...cachedMessages]
  if (searchKeyword.value) {
    const kw = searchKeyword.value.toLowerCase()
    list = list.filter(
      (m) =>
        m.title.toLowerCase().includes(kw) ||
        m.content.toLowerCase().includes(kw)
    )
  }
  total.value = list.length
  const start = (currentPage.value - 1) * pageSize.value
  messages.value = list.slice(start, start + pageSize.value)
}

watch([currentPage, pageSize], () => {
  applyLocalFilter()
})

function onTabChange(key: string) {
  activeType.value = key as MessageType | 'all'
  currentPage.value = 1
  loadMessages(1)
}

function switchType(key: MessageType | 'all') {
  activeType.value = key
  currentPage.value = 1
  loadMessages(1)
}

function resetFilters() {
  searchKeyword.value = ''
  filterRead.value = undefined
  dateRange.value = null
  currentPage.value = 1
  loadMessages(1)
}

async function handleMarkRead(id: string) {
  try {
    await messageStore.markMessageRead(id)
    const msg = messages.value.find((m) => m.id === id)
    if (msg) msg.is_read = true
    const cached = cachedMessages.find((m) => m.id === id)
    if (cached) cached.is_read = true
    message.success('已标记为已读')
  } catch {
    // handled
  }
}

async function handleMarkAllRead() {
  try {
    if (activeType.value === 'all') {
      await messageStore.markAllRead()
    } else {
      await messageStore.markAllRead(activeType.value)
    }
    messages.value = messages.value.map((m) => ({ ...m, is_read: true }))
    cachedMessages = cachedMessages.map((m) => ({ ...m, is_read: true }))
    message.success('已全部标记为已读')
  } catch {
    // handled
  }
}

async function handleDelete(id: string) {
  try {
    await messageStore.deleteMessage(id)
    messages.value = messages.value.filter((m) => m.id !== id)
    cachedMessages = cachedMessages.filter((m) => m.id !== id)
    total.value = Math.max(0, total.value - 1)
    message.success('消息已删除')
  } catch {
    // handled
  }
}

async function handleMessageClick(msg: Message) {
  if (!msg.is_read) {
    await handleMarkRead(msg.id)
  }

  if (msg.link) {
    navigateToLink(msg.link)
  }
}

function navigateToLink(link: MessageLink) {
  switch (link.type) {
    case 'bond_detail':
      router.push(`/market/${link.params.id}`)
      break
    case 'alert_list':
      router.push('/alerts/history')
      break
    case 'market':
      router.push('/market')
      break
    case 'external':
      if (link.params.url) {
        window.open(link.params.url, '_blank')
      }
      break
  }
}

onMounted(() => {
  messageStore.fetchUnreadCount()
  loadMessages(1)
})
</script>

<style scoped>
.message-center {
  max-width: 1200px;
  margin: 0 auto;
}

.stat-card {
  cursor: pointer;
  padding: 8px 16px;
  background: #fafafa;
  border-radius: 8px;
  transition: all 0.2s;
}

.stat-card:hover {
  background: #f0f0f0;
  transform: translateY(-2px);
}

.message-list {
  border-radius: 8px;
  overflow: hidden;
}

.message-item {
  cursor: pointer;
  transition: all 0.2s;
  border-radius: 8px;
  margin-bottom: 8px;
  background: #fff;
  border: 1px solid #f0f0f0;
}

.message-item:hover {
  background: #fafafa;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.message-item.unread {
  background: linear-gradient(to right, #fff1f0 0%, #fff 100%);
  border-left: 3px solid #ff4d4f;
}

.message-content {
  color: #595959;
  line-height: 1.6;
}

.message-meta {
  border-top: 1px dashed #f0f0f0;
  padding-top: 8px;
}

:deep(.ant-tabs-nav) {
  margin-bottom: 16px !important;
}

:deep(.ant-list-item) {
  padding: 16px 24px !important;
}

:deep(.ant-list-split .ant-list-item) {
  border-bottom: none;
}
</style>
