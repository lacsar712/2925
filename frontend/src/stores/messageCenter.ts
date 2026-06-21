import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api'
import { mockMessageService } from '../utils/messageMockService'

export type MessageType = 'announcement' | 'market_movement' | 'price_alert' | 'admin_broadcast'

export interface MessageLink {
  type: 'bond_detail' | 'alert_list' | 'market' | 'external'
  params: Record<string, string>
}

export interface Message {
  id: string
  type: MessageType
  title: string
  content: string
  is_read: boolean
  link?: MessageLink
  metadata: Record<string, unknown>
  created_at: string
  updated_at?: string
}

export interface MessageListResponse {
  items: Message[]
  total: number
  page: number
  page_size: number
}

export interface UnreadCountByType {
  announcement: number
  market_movement: number
  price_alert: number
  admin_broadcast: number
  total: number
}

export const MESSAGE_TYPE_LABEL: Record<MessageType, string> = {
  announcement: '系统公告',
  market_movement: '行情异动',
  price_alert: '价格预警',
  admin_broadcast: '管理员广播',
}

export const MESSAGE_TYPE_COLOR: Record<MessageType, string> = {
  announcement: 'blue',
  market_movement: 'orange',
  price_alert: 'red',
  admin_broadcast: 'purple',
}

export const MESSAGE_TYPE_ICON: Record<MessageType, string> = {
  announcement: 'NotificationOutlined',
  market_movement: 'TrendingUpOutlined',
  price_alert: 'BellOutlined',
  admin_broadcast: 'SoundOutlined',
}

function refreshMessagesByType(allMessages: Message[]): Record<MessageType, Message[]> {
  const byType: Record<MessageType, Message[]> = {
    announcement: [],
    market_movement: [],
    price_alert: [],
    admin_broadcast: [],
  }
  allMessages.forEach((m) => {
    byType[m.type].push(m)
  })
  return byType
}

export const useMessageCenterStore = defineStore('messageCenter', () => {
  const messages = ref<Message[]>([])
  const messagesByType = ref<Record<MessageType, Message[]>>({
    announcement: [],
    market_movement: [],
    price_alert: [],
    admin_broadcast: [],
  })
  const unreadCount = ref<UnreadCountByType>({
    announcement: 0,
    market_movement: 0,
    price_alert: 0,
    admin_broadcast: 0,
    total: 0,
  })
  const loading = ref(false)
  const pollTimer = ref<number | null>(null)
  const currentPage = ref(1)
  const pageSize = ref(20)
  const total = ref(0)

  const totalUnread = computed(() => unreadCount.value.total)

  const unreadByType = computed(() => ({
    announcement: unreadCount.value.announcement,
    market_movement: unreadCount.value.market_movement,
    price_alert: unreadCount.value.price_alert,
    admin_broadcast: unreadCount.value.admin_broadcast,
  }))

  mockMessageService.init()

  async function fetchUnreadCount() {
    try {
      const res = await api.get<UnreadCountByType>('/api/messages/unread-count')
      unreadCount.value = res.data
    } catch {
      unreadCount.value = mockMessageService.getUnreadCount()
    }
  }

  async function fetchMessages(params?: {
    type?: MessageType
    is_read?: boolean
    page?: number
    page_size?: number
    start_time?: string
    end_time?: string
  }) {
    loading.value = true
    try {
      const res = await api.get<MessageListResponse>('/api/messages', {
        params: {
          page: currentPage.value,
          page_size: pageSize.value,
          ...params,
        },
      })
      messages.value = res.data.items
      messagesByType.value = refreshMessagesByType(res.data.items)
      total.value = res.data.total
      currentPage.value = res.data.page
      pageSize.value = res.data.page_size
      return res.data
    } catch {
      const mockResult = mockMessageService.getMessages({
        page: currentPage.value,
        page_size: pageSize.value,
        ...params,
      })
      messages.value = mockResult.items
      messagesByType.value = refreshMessagesByType(mockResult.items)
      total.value = mockResult.total
      currentPage.value = mockResult.page
      pageSize.value = mockResult.page_size
      return mockResult
    } finally {
      loading.value = false
    }
  }

  async function fetchMessagesByType(type: MessageType, page = 1, page_size = 20) {
    try {
      const res = await api.get<MessageListResponse>('/api/messages', {
        params: { type, page, page_size },
      })
      messagesByType.value[type] = res.data.items
      return res.data
    } catch {
      const mockResult = mockMessageService.getMessages({ type, page, page_size })
      messagesByType.value[type] = mockResult.items
      return mockResult
    }
  }

  async function fetchRecentMessages(limit = 20) {
    try {
      const res = await api.get<Message[]>('/api/messages/recent', {
        params: { limit },
      })
      messages.value = res.data
      messagesByType.value = refreshMessagesByType(res.data)
      return res.data
    } catch {
      const mockResult = mockMessageService.getRecentMessages(limit)
      messages.value = mockResult
      messagesByType.value = refreshMessagesByType(mockResult)
      return mockResult
    }
  }

  async function markMessageRead(messageId: string) {
    try {
      await api.post(`/api/messages/${messageId}/mark-read`)
    } catch {
      mockMessageService.markMessageRead(messageId)
    }

    const msg = messages.value.find((m) => m.id === messageId)
    if (msg && !msg.is_read) {
      msg.is_read = true
      if (unreadCount.value[msg.type] > 0) {
        unreadCount.value[msg.type]--
      }
      if (unreadCount.value.total > 0) {
        unreadCount.value.total--
      }
    }
    const typeMsg = messagesByType.value[msg?.type as MessageType]?.find((m) => m.id === messageId)
    if (typeMsg) {
      typeMsg.is_read = true
    }
  }

  async function markAllRead(type?: MessageType) {
    try {
      const params = type ? { type } : {}
      await api.post('/api/messages/mark-read-all', params)
    } catch {
      mockMessageService.markAllRead(type)
    }

    if (type) {
      messages.value.forEach((m) => {
        if (m.type === type) m.is_read = true
      })
      messagesByType.value[type].forEach((m) => {
        m.is_read = true
      })
      unreadCount.value.total -= unreadCount.value[type]
      unreadCount.value[type] = 0
    } else {
      messages.value.forEach((m) => {
        m.is_read = true
      })
      Object.keys(messagesByType.value).forEach((key) => {
        messagesByType.value[key as MessageType].forEach((m) => {
          m.is_read = true
        })
      })
      unreadCount.value = {
        announcement: 0,
        market_movement: 0,
        price_alert: 0,
        admin_broadcast: 0,
        total: 0,
      }
    }
  }

  async function pushMessage(data: {
    type: MessageType
    title: string
    content: string
    link?: MessageLink
    metadata?: Record<string, unknown>
  }) {
    try {
      const res = await api.post<Message>('/api/messages', data)
      messages.value.unshift(res.data)
      messagesByType.value[data.type].unshift(res.data)
      unreadCount.value[data.type]++
      unreadCount.value.total++
      return res.data
    } catch {
      const newMsg = mockMessageService.createMessage(data)
      messages.value.unshift(newMsg)
      messagesByType.value[data.type].unshift(newMsg)
      unreadCount.value[data.type]++
      unreadCount.value.total++
      return newMsg
    }
  }

  async function deleteMessage(messageId: string) {
    try {
      await api.delete(`/api/messages/${messageId}`)
    } catch {
      mockMessageService.deleteMessage(messageId)
    }

    const idx = messages.value.findIndex((m) => m.id === messageId)
    if (idx > -1) {
      const msg = messages.value[idx]
      if (!msg.is_read && unreadCount.value[msg.type] > 0) {
        unreadCount.value[msg.type]--
        if (unreadCount.value.total > 0) {
          unreadCount.value.total--
        }
      }
      messages.value.splice(idx, 1)
    }
    Object.keys(messagesByType.value).forEach((key) => {
      const typeIdx = messagesByType.value[key as MessageType].findIndex((m) => m.id === messageId)
      if (typeIdx > -1) {
        messagesByType.value[key as MessageType].splice(typeIdx, 1)
      }
    })
  }

  function startPolling(intervalMs = 30000) {
    stopPolling()
    fetchUnreadCount()
    fetchRecentMessages(20)
    pollTimer.value = window.setInterval(() => {
      fetchUnreadCount()
      fetchRecentMessages(20)
    }, intervalMs)
  }

  function stopPolling() {
    if (pollTimer.value !== null) {
      clearInterval(pollTimer.value)
      pollTimer.value = null
    }
  }

  return {
    messages,
    messagesByType,
    unreadCount,
    totalUnread,
    unreadByType,
    loading,
    currentPage,
    pageSize,
    total,
    fetchUnreadCount,
    fetchMessages,
    fetchMessagesByType,
    fetchRecentMessages,
    markMessageRead,
    markAllRead,
    pushMessage,
    deleteMessage,
    startPolling,
    stopPolling,
  }
})
