<template>
  <a-tooltip :title="statusText" placement="bottom">
    <div class="connection-status flex items-center gap-2 cursor-default">
      <span class="status-dot" :class="statusClass"></span>
      <span class="status-text text-xs" :class="textClass">{{ statusLabel }}</span>
    </div>
  </a-tooltip>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useWebSocketStore } from '../../stores/websocket'

const wsStore = useWebSocketStore()

const statusClass = computed(() => {
  switch (wsStore.status) {
    case 'connected':
      return 'status-connected'
    case 'connecting':
    case 'reconnecting':
      return 'status-reconnecting'
    case 'disconnected':
      return 'status-disconnected'
    case 'idle':
    default:
      return 'status-idle'
  }
})

const textClass = computed(() => {
  switch (wsStore.status) {
    case 'connected':
      return 'text-green-600'
    case 'connecting':
    case 'reconnecting':
      return 'text-yellow-600'
    case 'disconnected':
      return 'text-red-500'
    case 'idle':
    default:
      return 'text-gray-400'
  }
})

const statusLabel = computed(() => {
  switch (wsStore.status) {
    case 'connected':
      return '实时'
    case 'connecting':
      return '连接中'
    case 'reconnecting':
      return '重连中'
    case 'disconnected':
      return '已断开'
    case 'idle':
    default:
      return '未启用'
  }
})

const statusText = computed(() => {
  switch (wsStore.status) {
    case 'connected':
      return '行情实时连接正常'
    case 'connecting':
      return '正在连接行情服务...'
    case 'reconnecting':
      return `连接中断，正在重连 (${wsStore.reconnectAttempts})...`
    case 'disconnected':
      return '行情服务连接异常，请刷新页面重试'
    case 'idle':
    default:
      return '当前页面无需实时行情'
  }
})
</script>

<style scoped>
.connection-status {
  padding: 2px 8px;
  border-radius: 12px;
  background: rgba(0, 0, 0, 0.02);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

.status-connected {
  background-color: #52c41a;
  box-shadow: 0 0 6px rgba(82, 196, 26, 0.6);
  animation: pulse-green 2s ease-in-out infinite;
}

.status-reconnecting {
  background-color: #faad14;
  box-shadow: 0 0 6px rgba(250, 173, 20, 0.6);
  animation: pulse-yellow 1s ease-in-out infinite;
}

.status-disconnected {
  background-color: #ff4d4f;
  box-shadow: 0 0 6px rgba(255, 77, 79, 0.4);
}

.status-idle {
  background-color: #bfbfbf;
  box-shadow: none;
}

@keyframes pulse-green {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

@keyframes pulse-yellow {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.7; transform: scale(1.15); }
}
</style>
