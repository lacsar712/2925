import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export type ConnectionStatus = 'connecting' | 'connected' | 'reconnecting' | 'disconnected'

export interface SourceSummary {
  source_name: string
  source_type: string
  best_bid_price?: number
  best_ask_price?: number
  best_bid_yield?: number
  best_ask_yield?: number
  quote_count: number
  latest_quote_time?: string
}

export interface BondQuoteUpdate {
  bond_id: string
  code: string
  name: string
  sources: SourceSummary[]
  best_bid_price?: number
  best_ask_price?: number
  best_bid_yield?: number
  best_ask_yield?: number
  spread?: number
  total_quotes: number
  timestamp: string
}

interface WsMessage {
  type: string
  data: any
}

type QuoteCallback = (update: BondQuoteUpdate) => void

export const useWebSocketStore = defineStore('websocket', () => {
  const status = ref<ConnectionStatus>('disconnected')
  const reconnectAttempts = ref(0)
  const maxReconnectAttempts = 10
  const reconnectDelay = 2000

  let ws: WebSocket | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let pingTimer: ReturnType<typeof setInterval> | null = null
  const subscribedBondIds = ref<Set<string>>(new Set())
  const callbacks = ref<Map<string, Set<QuoteCallback>>>(new Map())
  const lastPrices = ref<Map<string, { best_bid?: number; best_ask?: number }>>(new Map())

  const isConnected = computed(() => status.value === 'connected')
  const isReconnecting = computed(() => status.value === 'reconnecting')
  const isDisconnected = computed(() => status.value === 'disconnected')

  function getWsUrl(): string {
    const token = localStorage.getItem('bondview_token') || ''
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    return `${protocol}//${host}/ws/quotes?token=${encodeURIComponent(token)}`
  }

  function connect() {
    if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
      return
    }

    if (reconnectAttempts.value === 0) {
      status.value = 'connecting'
    } else {
      status.value = 'reconnecting'
    }

    try {
      ws = new WebSocket(getWsUrl())
    } catch (e) {
      scheduleReconnect()
      return
    }

    ws.onopen = () => {
      status.value = 'connected'
      reconnectAttempts.value = 0
      if (subscribedBondIds.value.size > 0) {
        sendSubscribe(Array.from(subscribedBondIds.value))
      }
      startPing()
    }

    ws.onmessage = (event) => {
      try {
        const msg: WsMessage = JSON.parse(event.data)
        handleMessage(msg)
      } catch (e) {
        // ignore parse errors
      }
    }

    ws.onerror = () => {
      // error will trigger close
    }

    ws.onclose = () => {
      stopPing()
      if (status.value !== 'disconnected') {
        scheduleReconnect()
      }
    }
  }

  function disconnect() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    stopPing()
    if (ws) {
      ws.close()
      ws = null
    }
    status.value = 'disconnected'
    reconnectAttempts.value = 0
  }

  function scheduleReconnect() {
    if (reconnectAttempts.value >= maxReconnectAttempts) {
      status.value = 'disconnected'
      return
    }
    status.value = 'reconnecting'
    reconnectAttempts.value++
    const delay = reconnectDelay * Math.min(reconnectAttempts.value, 5)
    if (reconnectTimer) clearTimeout(reconnectTimer)
    reconnectTimer = setTimeout(() => {
      connect()
    }, delay)
  }

  function startPing() {
    stopPing()
    pingTimer = setInterval(() => {
      send({ type: 'ping' })
    }, 30000)
  }

  function stopPing() {
    if (pingTimer) {
      clearInterval(pingTimer)
      pingTimer = null
    }
  }

  function send(message: any) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(message))
    }
  }

  function sendSubscribe(bondIds: string[]) {
    if (bondIds.length === 0) return
    send({ type: 'subscribe', data: { bond_ids: bondIds } })
  }

  function sendUnsubscribe(bondIds: string[]) {
    if (bondIds.length === 0) return
    send({ type: 'unsubscribe', data: { bond_ids: bondIds } })
  }

  function handleMessage(msg: WsMessage) {
    switch (msg.type) {
      case 'quote_update':
        handleQuoteUpdate(msg.data as BondQuoteUpdate)
        break
      case 'connected':
      case 'subscribed':
      case 'unsubscribed':
      case 'pong':
      case 'error':
        break
    }
  }

  function handleQuoteUpdate(update: BondQuoteUpdate) {
    const bondId = update.bond_id
    const cbs = callbacks.value.get(bondId)
    if (cbs) {
      cbs.forEach((cb) => {
        try {
          cb(update)
        } catch (e) {
          // ignore
        }
      })
    }
  }

  function subscribeBond(bondId: string, callback: QuoteCallback) {
    if (!callbacks.value.has(bondId)) {
      callbacks.value.set(bondId, new Set())
    }
    callbacks.value.get(bondId)!.add(callback)

    const wasEmpty = subscribedBondIds.value.size === 0
    subscribedBondIds.value.add(bondId)

    if (wasEmpty && status.value === 'disconnected') {
      connect()
    } else if (status.value === 'connected') {
      sendSubscribe([bondId])
    }
  }

  function unsubscribeBond(bondId: string, callback: QuoteCallback) {
    const cbs = callbacks.value.get(bondId)
    if (cbs) {
      cbs.delete(callback)
      if (cbs.size === 0) {
        callbacks.value.delete(bondId)
        subscribedBondIds.value.delete(bondId)
        if (status.value === 'connected') {
          sendUnsubscribe([bondId])
        }
      }
    }

    if (subscribedBondIds.value.size === 0) {
      disconnect()
    }
  }

  function subscribeBonds(bondIds: string[], callback: QuoteCallback) {
    const newIds: string[] = []
    bondIds.forEach((bondId) => {
      if (!callbacks.value.has(bondId)) {
        callbacks.value.set(bondId, new Set())
      }
      const beforeSize = callbacks.value.get(bondId)!.size
      callbacks.value.get(bondId)!.add(callback)
      if (beforeSize === 0) {
        const wasEmpty = subscribedBondIds.value.size === 0
        subscribedBondIds.value.add(bondId)
        if (!wasEmpty) newIds.push(bondId)
      }
    })

    if (subscribedBondIds.value.size > 0 && status.value === 'disconnected') {
      connect()
    } else if (status.value === 'connected' && newIds.length > 0) {
      sendSubscribe(newIds)
    }
  }

  function unsubscribeBonds(bondIds: string[], callback: QuoteCallback) {
    const removedIds: string[] = []
    bondIds.forEach((bondId) => {
      const cbs = callbacks.value.get(bondId)
      if (cbs) {
        cbs.delete(callback)
        if (cbs.size === 0) {
          callbacks.value.delete(bondId)
          subscribedBondIds.value.delete(bondId)
          removedIds.push(bondId)
        }
      }
    })

    if (status.value === 'connected' && removedIds.length > 0) {
      sendUnsubscribe(removedIds)
    }

    if (subscribedBondIds.value.size === 0) {
      disconnect()
    }
  }

  function getPreviousPrice(bondId: string) {
    return lastPrices.value.get(bondId)
  }

  function setPreviousPrice(bondId: string, prices: { best_bid?: number; best_ask?: number }) {
    lastPrices.value.set(bondId, prices)
  }

  return {
    status,
    reconnectAttempts,
    isConnected,
    isReconnecting,
    isDisconnected,
    subscribedBondIds,
    connect,
    disconnect,
    subscribeBond,
    unsubscribeBond,
    subscribeBonds,
    unsubscribeBonds,
    getPreviousPrice,
    setPreviousPrice,
  }
})
