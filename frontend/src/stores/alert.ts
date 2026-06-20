import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api'

export interface AlertRule {
  id: string
  user_id: string
  bond_id: string
  bond?: Bond
  alert_type: 'yield' | 'net_price'
  condition: 'above' | 'below'
  threshold: number
  is_enabled: boolean
  trigger_cooldown_minutes: number
  description?: string
  last_triggered_at?: string
  created_at?: string
  updated_at?: string
}

export interface Bond {
  id: string
  code: string
  name: string
  bond_type: string
  issuer: string
  coupon_rate?: number
  remaining_term?: number
  credit_rating?: string
}

export interface AlertTrigger {
  id: string
  rule_id: string
  user_id: string
  bond_id: string
  bond?: Bond
  alert_type: 'yield' | 'net_price'
  condition: 'above' | 'below'
  threshold: number
  actual_value: number
  is_read: boolean
  message?: string
  created_at?: string
}

export interface AlertRuleCreate {
  bond_id: string
  alert_type: 'yield' | 'net_price'
  condition: 'above' | 'below'
  threshold: number
  is_enabled?: boolean
  trigger_cooldown_minutes?: number
  description?: string
}

export interface AlertRuleUpdate {
  alert_type?: 'yield' | 'net_price'
  condition?: 'above' | 'below'
  threshold?: number
  is_enabled?: boolean
  trigger_cooldown_minutes?: number
  description?: string
}

export const useAlertStore = defineStore('alert', () => {
  const unreadCount = ref(0)
  const recentTriggers = ref<AlertTrigger[]>([])
  const pollTimer = ref<number | null>(null)

  async function fetchUnreadCount() {
    try {
      const res = await api.get<{ count: number }>('/api/alerts/unread-count')
      unreadCount.value = res.data.count
    } catch {
      // ignore
    }
  }

  async function fetchRecentTriggers(limit = 20) {
    try {
      const res = await api.get<AlertTrigger[]>('/api/alerts/triggers/recent', { params: { limit } })
      recentTriggers.value = res.data
    } catch {
      // ignore
    }
  }

  async function markAllRead() {
    try {
      await api.post('/api/alerts/triggers/mark-read', {})
      unreadCount.value = 0
      recentTriggers.value = recentTriggers.value.map((t) => ({ ...t, is_read: true }))
    } catch {
      // ignore
    }
  }

  async function markTriggerRead(triggerId: string) {
    try {
      await api.post(`/api/alerts/triggers/${triggerId}/mark-read`)
      const t = recentTriggers.value.find((x) => x.id === triggerId)
      if (t && !t.is_read) {
        t.is_read = true
        unreadCount.value = Math.max(0, unreadCount.value - 1)
      }
    } catch {
      // ignore
    }
  }

  function startPolling(intervalMs = 30000) {
    stopPolling()
    fetchUnreadCount()
    fetchRecentTriggers()
    pollTimer.value = window.setInterval(() => {
      fetchUnreadCount()
      fetchRecentTriggers()
    }, intervalMs)
  }

  function stopPolling() {
    if (pollTimer.value !== null) {
      clearInterval(pollTimer.value)
      pollTimer.value = null
    }
  }

  async function createRule(data: AlertRuleCreate) {
    const res = await api.post<AlertRule>('/api/alerts/rules', data)
    return res.data
  }

  async function updateRule(id: string, data: AlertRuleUpdate) {
    const res = await api.put<AlertRule>(`/api/alerts/rules/${id}`, data)
    return res.data
  }

  async function deleteRule(id: string) {
    await api.delete(`/api/alerts/rules/${id}`)
  }

  async function toggleRule(id: string) {
    const res = await api.post<{ id: string; is_enabled: boolean; message: string }>(
      `/api/alerts/rules/${id}/toggle`
    )
    return res.data
  }

  return {
    unreadCount,
    recentTriggers,
    fetchUnreadCount,
    fetchRecentTriggers,
    markAllRead,
    markTriggerRead,
    startPolling,
    stopPolling,
    createRule,
    updateRule,
    deleteRule,
    toggleRule,
  }
})
