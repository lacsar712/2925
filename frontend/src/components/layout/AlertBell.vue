<template>
  <a-dropdown
    :trigger="['click']"
    placement="bottomRight"
    @visible-change="onDropdownVisible"
    :overlay-style="{ minWidth: '400px' }"
  >
    <a-badge
      :count="unreadCount > 99 ? '99+' : unreadCount"
      :number-style="{ backgroundColor: '#ff4d4f', boxShadow: '0 0 0 2px #fff' }"
      :offset="[-4, 4]"
    >
      <a-button
        type="text"
        size="large"
        class="alert-bell-btn"
        :class="{ 'has-unread': unreadCount > 0 }"
      >
        <BellOutlined :style="{ fontSize: '18px' }" />
      </a-button>
    </a-badge>

    <template #overlay>
      <div class="alert-dropdown">
        <div class="alert-dropdown-header flex items-center justify-between px-4 py-3 border-b border-gray-100">
          <span class="font-semibold text-gray-700">价格预警通知</span>
          <a-space>
            <a-button type="link" size="small" @click="goToHistory">
              查看全部
            </a-button>
            <a-button
              v-if="unreadCount > 0"
              type="link"
              size="small"
              :loading="markAllLoading"
              @click="handleMarkAll"
            >
              全部已读
            </a-button>
          </a-space>
        </div>

        <div class="alert-dropdown-body max-h-96 overflow-y-auto">
          <a-empty
            v-if="!loading && recentTriggers.length === 0"
            description="暂无预警通知"
            class="py-12"
          />
          <div v-else-if="loading" class="py-12 flex justify-center">
            <a-spin />
          </div>
          <div v-else>
            <div
              v-for="t in recentTriggers"
              :key="t.id"
              class="alert-item px-4 py-3 border-b border-gray-50 hover:bg-gray-50 cursor-pointer transition-colors"
              :class="{ 'bg-red-50/40': !t.is_read }"
              @click="handleItemClick(t)"
            >
              <div class="flex items-start justify-between gap-2 mb-1">
                <div class="flex items-center gap-1.5 flex-wrap">
                  <a-badge v-if="!t.is_read" status="error" />
                  <a-tag
                    :color="t.alert_type === 'yield' ? 'blue' : 'purple'"
                    size="small"
                    class="!mr-0"
                  >
                    {{ t.alert_type === 'yield' ? '收益率' : '净价' }}
                  </a-tag>
                  <a-tag
                    :color="t.condition === 'above' ? 'red' : 'green'"
                    size="small"
                    class="!mr-0"
                  >
                    {{ t.condition === 'above' ? '高于阈值' : '低于阈值' }}
                  </a-tag>
                </div>
                <span class="text-xs text-gray-400 tabular-nums shrink-0 whitespace-nowrap">
                  {{ formatRelativeTime(t.created_at) }}
                </span>
              </div>
              <div class="text-sm font-medium text-gray-800 mb-1 truncate">
                {{ t.bond?.name || '--' }}
                <span class="text-gray-500 text-xs ml-1">({{ t.bond?.code || '--' }})</span>
              </div>
              <div class="text-xs text-gray-600 tabular-nums">
                当前：
                <span :class="t.condition === 'above' ? 'text-red-600 font-semibold' : 'text-green-600 font-semibold'">
                  {{ Number(t.actual_value).toFixed(4) }}{{ t.alert_type === 'yield' ? '%' : '元' }}
                </span>
                <span class="mx-1 text-gray-400">/</span>
                阈值：{{ Number(t.threshold).toFixed(4) }}{{ t.alert_type === 'yield' ? '%' : '元' }}
              </div>
            </div>
          </div>
        </div>

        <div class="alert-dropdown-footer border-t border-gray-100 px-4 py-2">
          <router-link
            to="/alerts/rules"
            class="flex items-center justify-center gap-1.5 text-sm text-blue-600 hover:text-blue-700 py-1.5"
          >
            <SettingOutlined />
            管理预警规则
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
import { BellOutlined, SettingOutlined } from '@ant-design/icons-vue'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'
import { useAlertStore, type AlertTrigger } from '../../stores/alert'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

const router = useRouter()
const alertStore = useAlertStore()

const loading = ref(false)
const markAllLoading = ref(false)

const unreadCount = computed(() => alertStore.unreadCount)
const recentTriggers = computed(() => alertStore.recentTriggers)

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
        alertStore.fetchUnreadCount(),
        alertStore.fetchRecentTriggers(20),
      ])
    } finally {
      loading.value = false
    }
  }
}

async function handleItemClick(t: AlertTrigger) {
  if (!t.is_read) {
    try {
      await alertStore.markTriggerRead(t.id)
    } catch {
      // ignore
    }
  }
  router.push(`/market/${t.bond_id}`)
}

async function handleMarkAll() {
  markAllLoading.value = true
  try {
    await alertStore.markAllRead()
    message.success('已全部标记为已读')
  } finally {
    markAllLoading.value = false
  }
}

function goToHistory() {
  router.push('/alerts/history')
}

onMounted(() => {
  alertStore.startPolling(30000)
})

onBeforeUnmount(() => {
  alertStore.stopPolling()
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
.alert-dropdown {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.12);
  min-width: 400px;
  overflow: hidden;
}
</style>
