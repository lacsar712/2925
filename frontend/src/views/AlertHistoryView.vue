<template>
  <div class="alert-history">
    <a-breadcrumb class="mb-4">
      <a-breadcrumb-item>
        <router-link to="/dashboard">行情看板</router-link>
      </a-breadcrumb-item>
      <a-breadcrumb-item>
        <router-link to="/alerts/rules">预警规则管理</router-link>
      </a-breadcrumb-item>
      <a-breadcrumb-item>触发历史</a-breadcrumb-item>
    </a-breadcrumb>

    <a-card>
      <template #title>
        <div class="flex items-center justify-between w-full">
          <span class="text-lg font-semibold">告警触发历史</span>
          <div class="flex gap-2">
            <router-link to="/alerts/rules">
              <a-button>
                <template #icon><SettingOutlined /></template>
                规则管理
              </a-button>
            </router-link>
            <a-button type="primary" :disabled="unreadCount === 0" @click="markAllRead">
              全部标记已读
            </a-button>
          </div>
        </div>
      </template>

      <div class="mb-4 flex gap-3 flex-wrap items-center">
        <a-input-search
          v-model:value="searchKeyword"
          placeholder="搜索债券代码/简称"
          style="width: 240px"
          allow-clear
          @search="loadTriggers(1)"
          @change="onKeywordChange"
        />
        <a-select
          v-model:value="filterRead"
          placeholder="读取状态"
          style="width: 140px"
          allow-clear
          @change="loadTriggers(1)"
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
          @change="loadTriggers(1)"
        />
        <a-button @click="resetFilters">重置筛选</a-button>
      </div>

      <a-spin :spinning="loading">
        <a-empty v-if="!loading && triggers.length === 0" description="暂无触发记录" />
        <a-timeline v-else mode="left" class="pt-2">
          <a-timeline-item
            v-for="t in triggers"
            :key="t.id"
            :color="t.is_read ? 'gray' : (t.condition === 'above' ? 'red' : 'green')"
          >
            <div class="flex items-start justify-between gap-4 p-3 rounded"
                 :class="t.is_read ? 'bg-white' : 'bg-red-50/60'">
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-1 flex-wrap">
                  <a-tag :color="t.alert_type === 'yield' ? 'blue' : 'purple'" size="small">
                    {{ t.alert_type === 'yield' ? '收益率' : '净价' }}
                  </a-tag>
                  <a-tag :color="t.condition === 'above' ? 'red' : 'green'" size="small">
                    {{ t.condition === 'above' ? '高于阈值' : '低于阈值' }}
                  </a-tag>
                  <router-link :to="`/market/${t.bond_id}`"
                               class="text-blue-600 hover:underline font-semibold"
                               @click="onTriggerClick(t)">
                    {{ t.bond?.name || '--' }}
                    <span class="text-gray-500 text-xs ml-1">({{ t.bond?.code || '--' }})</span>
                  </router-link>
                  <a-badge v-if="!t.is_read" status="processing" text="未读" />
                </div>
                <div class="text-sm text-gray-700 mb-1 tabular-nums">
                  当前值：<span class="font-semibold" :class="t.condition === 'above' ? 'text-red-600' : 'text-green-600'">
                    {{ Number(t.actual_value).toFixed(4) }}{{ t.alert_type === 'yield' ? '%' : '元' }}
                  </span>
                  ，阈值：<span class="font-semibold">
                    {{ Number(t.threshold).toFixed(4) }}{{ t.alert_type === 'yield' ? '%' : '元' }}
                  </span>
                </div>
                <div v-if="t.message" class="text-xs text-gray-500">{{ t.message }}</div>
              </div>
              <div class="text-right flex flex-col items-end gap-2 shrink-0">
                <span class="text-xs text-gray-400 tabular-nums whitespace-nowrap">
                  {{ formatDateTime(t.created_at) }}
                </span>
                <a-button v-if="!t.is_read" type="link" size="small" @click="markRead(t.id)">
                  标记已读
                </a-button>
              </div>
            </div>
          </a-timeline-item>
        </a-timeline>

        <div v-if="total > 0" class="mt-4 flex justify-center">
          <a-pagination
            v-model:current="currentPage"
            v-model:page-size="pageSize"
            :total="total"
            show-size-changer
            show-quick-jumper
            :show-total="(t: number) => `共 ${t} 条`"
            @change="loadTriggers"
          />
        </div>
      </a-spin>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { SettingOutlined } from '@ant-design/icons-vue'
import dayjs, { type Dayjs } from 'dayjs'
import api from '../api'
import { formatDateTime } from '../utils/format'
import { useAlertStore, type AlertTrigger } from '../stores/alert'

const router = useRouter()
const alertStore = useAlertStore()

const loading = ref(false)
const triggers = ref<AlertTrigger[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const searchKeyword = ref<string>('')
const filterRead = ref<boolean | undefined>(undefined)
const dateRange = ref<[Dayjs | null, Dayjs | null] | null>(null)

const unreadCount = computed(() => alertStore.unreadCount)

let cachedAllTriggers: AlertTrigger[] = []

let keywordDebounceTimer: number | null = null
function onKeywordChange() {
  if (keywordDebounceTimer) clearTimeout(keywordDebounceTimer)
  keywordDebounceTimer = window.setTimeout(() => {
    applyLocalFilter()
  }, 300)
}

async function loadTriggers(page = currentPage.value) {
  loading.value = true
  try {
    const params: Record<string, unknown> = {
      page,
      page_size: 200,
    }
    if (filterRead.value !== undefined) params.is_read = filterRead.value
    if (dateRange.value && dateRange.value[0]) {
      params.start_time = dateRange.value[0].toISOString()
    }
    if (dateRange.value && dateRange.value[1]) {
      params.end_time = dateRange.value[1].toISOString()
    }

    const res = await api.get<{ items: AlertTrigger[]; total: number; page: number; page_size: number }>(
      '/api/alerts/triggers',
      { params }
    )
    cachedAllTriggers = res.data.items
    total.value = res.data.total
    currentPage.value = page
    applyLocalFilter()
  } catch {
    // handled
  } finally {
    loading.value = false
  }
}

function applyLocalFilter() {
  let list = [...cachedAllTriggers]
  if (searchKeyword.value) {
    const kw = searchKeyword.value.toLowerCase()
    list = list.filter((t) =>
      t.bond?.code.toLowerCase().includes(kw) ||
      t.bond?.name.toLowerCase().includes(kw)
    )
  }
  total.value = list.length
  const start = (currentPage.value - 1) * pageSize.value
  triggers.value = list.slice(start, start + pageSize.value)
}

watch([currentPage, pageSize], () => {
  applyLocalFilter()
})

function resetFilters() {
  searchKeyword.value = ''
  filterRead.value = undefined
  dateRange.value = null
  currentPage.value = 1
  loadTriggers(1)
}

async function markRead(id: string) {
  try {
    await alertStore.markTriggerRead(id)
    const t = triggers.value.find((x) => x.id === id)
    if (t) t.is_read = true
    const cached = cachedAllTriggers.find((x) => x.id === id)
    if (cached) cached.is_read = true
    message.success('已标记为已读')
  } catch {
    // handled
  }
}

async function markAllRead() {
  try {
    await alertStore.markAllRead()
    triggers.value = triggers.value.map((t) => ({ ...t, is_read: true }))
    cachedAllTriggers = cachedAllTriggers.map((t) => ({ ...t, is_read: true }))
    message.success('已全部标记为已读')
  } catch {
    // handled
  }
}

function onTriggerClick(t: AlertTrigger) {
  if (!t.is_read) {
    markRead(t.id)
  }
}

loadTriggers(1)
</script>
