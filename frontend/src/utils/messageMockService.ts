import type { Message, MessageType, UnreadCountByType, MessageListResponse, MessageLink } from '../stores/messageCenter'

const STORAGE_KEY = 'bondview_messages_mock'
const INIT_FLAG_KEY = 'bondview_messages_mock_initialized'

function generateId(): string {
  return 'msg_' + Date.now() + '_' + Math.random().toString(36).substring(2, 10)
}

function nowIso(): string {
  return new Date().toISOString()
}

function createMockMessages(): Message[] {
  const now = Date.now()
  const minutesAgo = (min: number) => new Date(now - min * 60 * 1000).toISOString()
  const hoursAgo = (h: number) => new Date(now - h * 60 * 60 * 1000).toISOString()
  const daysAgo = (d: number) => new Date(now - d * 24 * 60 * 60 * 1000).toISOString()

  return [
    {
      id: generateId(),
      type: 'announcement',
      title: '系统维护通知',
      content: '系统将于本周六（6月28日）凌晨 2:00-4:00 进行例行维护，届时行情查询和预警功能可能短暂不可用，请提前做好相关安排。',
      is_read: false,
      metadata: { priority: 'high', category: 'maintenance' },
      created_at: hoursAgo(2),
    },
    {
      id: generateId(),
      type: 'admin_broadcast',
      title: '新功能上线：债券对比分析',
      content: '债券对比分析功能已正式上线！支持最多 5 只债券的多维度对比，包括收益率、期限、信用评级等关键指标。请在侧边栏点击「债券对比」体验。',
      is_read: false,
      metadata: { feature: 'bond_compare', version: 'v2.1.0' },
      created_at: hoursAgo(5),
    },
    {
      id: generateId(),
      type: 'price_alert',
      title: '价格预警：24国债01 收益率高于阈值',
      content: '24国债01（代码：240001.IB）当前收益率 3.2500%，已高于您设置的阈值 3.2000%。',
      is_read: false,
      link: { type: 'bond_detail', params: { id: 'bond_240001' } } as MessageLink,
      metadata: {
        bond_id: 'bond_240001',
        bond_code: '240001.IB',
        bond_name: '24国债01',
        alert_type: 'yield',
        condition: 'above',
        actual_value: 3.25,
        threshold: 3.2,
      },
      created_at: minutesAgo(15),
    },
    {
      id: generateId(),
      type: 'price_alert',
      title: '价格预警：23国开10 净价低于阈值',
      content: '23国开10（代码：230210.IB）当前净价 100.2500 元，已低于您设置的阈值 100.5000 元。',
      is_read: true,
      link: { type: 'bond_detail', params: { id: 'bond_230210' } } as MessageLink,
      metadata: {
        bond_id: 'bond_230210',
        bond_code: '230210.IB',
        bond_name: '23国开10',
        alert_type: 'net_price',
        condition: 'below',
        actual_value: 100.25,
        threshold: 100.5,
      },
      created_at: hoursAgo(1),
    },
    {
      id: generateId(),
      type: 'market_movement',
      title: '行情异动：24国债05 上涨 1.85%',
      content: '24国债05（代码：240005.IB）价格出现大幅上涨，当前涨幅 1.85%，建议关注。',
      is_read: false,
      link: { type: 'bond_detail', params: { id: 'bond_240005' } } as MessageLink,
      metadata: {
        bond_id: 'bond_240005',
        bond_code: '240005.IB',
        bond_name: '24国债05',
        change_percent: 1.85,
      },
      created_at: minutesAgo(42),
    },
    {
      id: generateId(),
      type: 'market_movement',
      title: '行情异动：22农发08 下跌 2.10%',
      content: '22农发08（代码：220408.IB）价格出现大幅下跌，当前跌幅 2.10%，请关注持仓风险。',
      is_read: true,
      link: { type: 'bond_detail', params: { id: 'bond_220408' } } as MessageLink,
      metadata: {
        bond_id: 'bond_220408',
        bond_code: '220408.IB',
        bond_name: '22农发08',
        change_percent: -2.1,
      },
      created_at: hoursAgo(3),
    },
    {
      id: generateId(),
      type: 'announcement',
      title: '数据接口升级通知',
      content: '行情数据接口已升级至 v3.0，数据延迟从 500ms 降至 200ms，同时新增了多档深度行情数据。',
      is_read: true,
      metadata: { priority: 'normal', category: 'upgrade' },
      created_at: daysAgo(1),
    },
    {
      id: generateId(),
      type: 'admin_broadcast',
      title: '用户数据迁移完成',
      content: '所有用户的自定义分组和预警规则数据已迁移至新存储系统，原有数据不受影响。如有异常请联系管理员。',
      is_read: true,
      metadata: { category: 'migration' },
      created_at: daysAgo(2),
    },
  ]
}

function loadMessages(): Message[] {
  const raw = localStorage.getItem(STORAGE_KEY)
  if (!raw) return []
  try {
    return JSON.parse(raw) as Message[]
  } catch {
    return []
  }
}

function saveMessages(messages: Message[]): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(messages))
}

function initializeIfNeeded(): void {
  const initialized = localStorage.getItem(INIT_FLAG_KEY)
  if (initialized) return

  const mockMessages = createMockMessages()
  saveMessages(mockMessages)
  localStorage.setItem(INIT_FLAG_KEY, '1')
}

function computeUnreadCount(messages: Message[]): UnreadCountByType {
  const count: UnreadCountByType = {
    announcement: 0,
    market_movement: 0,
    price_alert: 0,
    admin_broadcast: 0,
    total: 0,
  }
  messages.forEach((m) => {
    if (!m.is_read) {
      count[m.type]++
      count.total++
    }
  })
  return count
}

export const mockMessageService = {
  init(): void {
    initializeIfNeeded()
  },

  resetMockData(): void {
    localStorage.removeItem(INIT_FLAG_KEY)
    localStorage.removeItem(STORAGE_KEY)
    initializeIfNeeded()
  },

  getUnreadCount(): UnreadCountByType {
    initializeIfNeeded()
    const messages = loadMessages()
    return computeUnreadCount(messages)
  },

  getMessages(params?: {
    type?: MessageType
    is_read?: boolean
    page?: number
    page_size?: number
    start_time?: string
    end_time?: string
  }): MessageListResponse {
    initializeIfNeeded()
    let messages = loadMessages()

    if (params?.type) {
      messages = messages.filter((m) => m.type === params.type)
    }
    if (params?.is_read !== undefined) {
      messages = messages.filter((m) => m.is_read === params.is_read)
    }
    if (params?.start_time) {
      messages = messages.filter((m) => m.created_at >= params.start_time!)
    }
    if (params?.end_time) {
      messages = messages.filter((m) => m.created_at <= params.end_time!)
    }

    messages.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())

    const page = params?.page ?? 1
    const pageSize = params?.page_size ?? 20
    const total = messages.length
    const start = (page - 1) * pageSize
    const items = messages.slice(start, start + pageSize)

    return { items, total, page, page_size: pageSize }
  },

  getRecentMessages(limit = 20): Message[] {
    initializeIfNeeded()
    const messages = loadMessages()
    messages.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    return messages.slice(0, limit)
  },

  markMessageRead(messageId: string): boolean {
    initializeIfNeeded()
    const messages = loadMessages()
    const msg = messages.find((m) => m.id === messageId)
    if (msg) {
      msg.is_read = true
      msg.updated_at = nowIso()
      saveMessages(messages)
      return true
    }
    return false
  },

  markAllRead(type?: MessageType): void {
    initializeIfNeeded()
    const messages = loadMessages()
    const now = nowIso()
    messages.forEach((m) => {
      if (!type || m.type === type) {
        if (!m.is_read) {
          m.is_read = true
          m.updated_at = now
        }
      }
    })
    saveMessages(messages)
  },

  createMessage(data: {
    type: MessageType
    title: string
    content: string
    link?: MessageLink
    metadata?: Record<string, unknown>
  }): Message {
    initializeIfNeeded()
    const messages = loadMessages()
    const newMsg: Message = {
      id: generateId(),
      type: data.type,
      title: data.title,
      content: data.content,
      is_read: false,
      link: data.link,
      metadata: data.metadata ?? {},
      created_at: nowIso(),
    }
    messages.unshift(newMsg)
    saveMessages(messages)
    return newMsg
  },

  deleteMessage(messageId: string): boolean {
    initializeIfNeeded()
    const messages = loadMessages()
    const idx = messages.findIndex((m) => m.id === messageId)
    if (idx > -1) {
      messages.splice(idx, 1)
      saveMessages(messages)
      return true
    }
    return false
  },
}
