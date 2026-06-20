<template>
  <a-dropdown
    :trigger="['click']"
    placement="bottomRight"
    @visible-change="onDropdownVisible"
    :overlay-style="{ minWidth: '400px' }"
  >
    <a-badge
      :count="totalUnread > 99 ? '99+' : totalUnread"
      :number-style="{ backgroundColor: '#ff4d4f', boxShadow: '0 0 0 2px #fff' }"
      :offset="[-4, 4]"
    >
      <a-button
        type="text"
        size="large"
        class="alert-bell-btn"
        :class="{ 'has-unread': totalUnread > 0 }"
      >
        <BellOutlined :style="{ fontSize: '18px' }" />
      </a-button>
    </a-badge>

    <template #overlay>
      <div class="message-dropdown">
        <div class="message-dropdown-header flex items-center justify-between px-4 py-3 border-b border-gray-100">
          <span class="font-semibold text-gray-700">消息中心</span>
          <a-space>
            <a-button type="link" size="small" @click="goToMessageCenter">
              查看全部
            </a-button>
            <a-button
              v-if="totalUnread > 0"
              type="link"
              size="small"
              :loading="markAllLoading"
              @click="handleMarkAll"
            >
              全部已读
            </a-button>
          </a-space>
        </div>

        <div class="message-tabs px-4 py-2 border-b border-gray-100">
          <div class="flex gap-1 overflow-x-auto">
            <a-tag
              v-for="tab in tabs"
              :key="tab.key"
              :color="activeTab === tab.key ? tab.color : 'default'"
              class="cursor-pointer transition-all"
              :class="{ 'font-semibold': activeTab === tab.key }"
              @click="activeTab = tab.key"
            >
              {{ tab.label }}
              <span v-if="unreadByType[tab.key as MessageType] > 0" class="ml-1">
                ({{ unreadByType[tab.key as MessageType] }})
              </span>
            </a-tag>
          </div>
        </div>

        <div class="message-dropdown-body max-h-96 overflow-y-auto">
          <a-empty
            v-if="!loading && filteredMessages.length === 0"
            description="暂无消息"
            class="py-12"
          />
          <div v-else-if="loading" class="py-12 flex justify-center">
            <a-spin />
          </div>
          <div v-else>
            <div
              v-for="msg in filteredMessages"
              :key="msg.id"
              class="message-item px-4 py-3 border-b border-gray-50 hover:bg-gray-50 cursor-pointer transition-colors"
              :class="{ 'bg-red-50/40': !msg.is_read }"
              @click="handleMessageClick(msg)"
            >
              <div class="flex items-start justify-between gap-2 mb-1">
                <div class="flex items-center gap-1.5 flex-wrap">
                  <a-badge v-if="!msg.is_read" status="error" />
                  <a-tag
                    :color="getMessageTypeColor(msg.type)"
                    size="small"
                    class="!mr-0"
                  >
                    {{ getMessageTypeLabel(msg.type) }}
                  </a-tag>
                </div>
                <span class="text-xs text-gray-400 tabular-nums shrink-0 whitespace-nowrap">
                  {{ formatRelativeTime(msg.created_at) }}
                </span>
              </div>
              <div class="text-sm font-medium text-gray-800 mb-1">
                {{ msg.title }}
              </div>
              <div class="text-xs text-gray-600 line-clamp-2">
                {{ msg.content }}
              </div>
              <div v-if="msg.link" class="mt-2">
                <span class="text-xs text-blue-600 hover:text-blue-700">
                  {{ getLinkText(msg.link) }} →
                </span>
              </div>
            </div>
          </div>
        </div>

        <div class="message-dropdown-footer border-t border-gray-100 px-4 py-2">
          <router-link
            to="/messages"
            class="flex items-center justify-center gap-1.5 text-sm text-blue-600 hover:text-blue-700 py-1.5"
          >
            <InboxOutlined />
            进入消息中心
          </router-link>
        </div>
      </div>
    </template>
  </a-dropdown>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { BellOutlined, InboxOutlined } from '@ant-design/icons-vue'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'
import {
  useMessageCenterStore,
  type Message,
  type MessageType,
  type MessageLink,
  MESSAGE_TYPE_LABEL,
  MESSAGE_TYPE_COLOR,
} from '../../stores/messageCenter'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

const router = useRouter()
const messageStore = useMessageCenterStore()

const loading = ref(false)
const markAllLoading = ref(false)
const activeTab = ref<MessageType | 'all'>('all')

const totalUnread = computed(() => messageStore.totalUnread)
const unreadByType = computed(() => messageStore.unreadByType)
const messages = computed(() => messageStore.messages)

const tabs = [
  { key: 'all' as const, label: '全部', color: 'blue' },
  { key: 'announcement' as MessageType, label: '系统公告', color: 'blue' },
  { key: 'market_movement' as MessageType, label: '行情异动', color: 'orange' },
  { key: 'price_alert' as MessageType, label: '价格预警', color: 'red' },
  { key: 'admin_broadcast' as MessageType, label: '管理员广播', color: 'purple' },
]

const filteredMessages = computed(() => {
  if (activeTab.value === 'all') {
    return messages.value
  }
  return messages.value.filter((m) => m.type === activeTab.value)
})

function getMessageTypeLabel(type: MessageType): string {
  return MESSAGE_TYPE_LABEL[type] || type
}

function getMessageTypeColor(type: MessageType): string {
  return MESSAGE_TYPE_COLOR[type] || 'default'
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

function formatRelativeTime(iso?: string) {
  if (!iso) return '--'
  const d = dayjs(iso)
  const diffMin = dayjs().diff(d, 'minute')
  if (diffMin < 60) return d.fromNow()
  if (diffMin < 60 * 24) return d.format('HH:mm')
  return d.format('MM-DD HH:mm')
}

async function onDropdownVisible(visible: boolean) {
  if (visible) {
    loading.value = true
    try {
      await Promise.all([
        messageStore.fetchUnreadCount(),
        messageStore.fetchRecentMessages(20),
      ])
    } finally {
      loading.value = false
    }
  }
}

async function handleMessageClick(msg: Message) {
  if (!msg.is_read) {
    try {
      await messageStore.markMessageRead(msg.id)
    } catch {
      // ignore
    }
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

async function handleMarkAll() {
  markAllLoading.value = true
  try {
    if (activeTab.value === 'all') {
      await messageStore.markAllRead()
    } else {
      await messageStore.markAllRead(activeTab.value)
    }
    message.success('已全部标记为已读')
  } finally {
    markAllLoading.value = false
  }
}

function goToMessageCenter() {
  router.push('/messages')
}

onMounted(() => {
  messageStore.startPolling(30000)
})

onBeforeUnmount(() => {
  messageStore.stopPolling()
})
</script>

<style scoped>
.alert-bell-btn {
  border-radius: 50% !important;
  width: 40px;
  height: 40px;
  display: inline-flex !important;
  align-items: center;
  justify-content: center;
}
.alert-bell-btn:hover {
  background-color: rgba(0, 0, 0, 0.04);
}
.alert-bell-btn.has-unread {
  color: #ff4d4f;
  animation: bell-shake 2s ease-in-out infinite;
}
@keyframes bell-shake {
  0%, 90%, 100% { transform: rotate(0deg); }
  92% { transform: rotate(-10deg); }
  94% { transform: rotate(10deg); }
  96% { transform: rotate(-10deg); }
  98% { transform: rotate(10deg); }
}
.message-dropdown {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.12);
  min-width: 400px;
  overflow: hidden;
}
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
