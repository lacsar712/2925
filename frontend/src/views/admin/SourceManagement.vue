<template>
  <div class="source-management p-4">
    <a-row :gutter="[16, 16]">
      <a-col :span="24">
        <a-card title="缓存管理" class="rounded-lg mb-4">
          <a-space>
            <a-select
              v-model:value="selectedScope"
              style="width: 280px"
              placeholder="选择缓存范围"
              :options="cacheScopes"
            />
            <a-button
              type="primary"
              :loading="cacheLoading"
              @click="handleRefreshCache"
            >
              <template #icon><ReloadOutlined /></template>
              一键刷新缓存
            </a-button>
            <a-button
              :loading="cacheLoading"
              danger
              @click="handleRefreshAllCache"
            >
              刷新全部缓存
            </a-button>
          </a-space>
          <div class="text-xs text-gray-400 mt-2">
            缓存说明：看板(30s) · 报价(15s) · 债券行情(20s)，刷新后下一次请求将获取最新数据
          </div>
        </a-card>
      </a-col>
      <a-col :span="24">
        <a-card title="行情源管理" class="rounded-lg">
          <a-table
            :data-source="sources"
            :columns="columns"
            :loading="loading"
            :pagination="false"
            :scroll="{ x: 'max-content' }"
            :row-key="(r) => r.id"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'type'">
                <a-tag>{{ sourceTypeLabel(record.type) }}</a-tag>
              </template>
              <template v-else-if="column.key === 'status'">
                <a-badge
                  :status="sourceStatusBadge(record.status)"
                  :text="sourceStatusText(record.status)"
                />
              </template>
              <template v-else-if="column.key === 'enabled'">
                <a-switch
                  :checked="record.enabled"
                  @change="(checked) => handleToggleEnabled(record.id, !!checked)"
                />
              </template>
            </template>
          </a-table>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { ReloadOutlined } from '@ant-design/icons-vue'
import api from '../../api'
import { sourceTypeLabel } from '../../utils/format'

interface SourceItem {
  id: string
  name: string
  type: string
  status: 'online' | 'offline' | 'error'
  description?: string
  enabled: boolean
}

interface CacheScope {
  label: string
  value: string
}

const loading = ref(false)
const cacheLoading = ref(false)
const sources = ref<SourceItem[]>([])
const cacheScopes = ref<CacheScope[]>([])
const selectedScope = ref<string>('dashboard')

function sourceStatusBadge(status: string): 'success' | 'warning' | 'error' | 'default' {
  const map: Record<string, 'success' | 'warning' | 'error' | 'default'> = {
    online: 'success',
    offline: 'warning',
    error: 'error',
  }
  return map[status] || 'default'
}

function sourceStatusText(status: string): string {
  const map: Record<string, string> = {
    online: '在线',
    offline: '离线',
    error: '异常',
  }
  return map[status] || status
}

const columns = [
  { title: '名称', dataIndex: 'name', key: 'name', width: 140 },
  { title: '类型', key: 'type', dataIndex: 'type', width: 120 },
  { title: '状态', key: 'status', dataIndex: 'status', width: 100 },
  { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
  { title: '是否启用', key: 'enabled', dataIndex: 'enabled', width: 100 },
]

async function fetchSources() {
  loading.value = true
  try {
    const res = await api.get<SourceItem[] | { items: SourceItem[] }>('/api/admin/sources')
    const data = res.data
    sources.value = Array.isArray(data) ? data : (data as { items: SourceItem[] }).items ?? []
  } catch {
    sources.value = []
  } finally {
    loading.value = false
  }
}

async function fetchCacheScopes() {
  try {
    const res = await api.get<{ key: string; label: string }[]>('/api/admin/cache/scopes')
    cacheScopes.value = res.data.map((s) => ({ label: s.label, value: s.key }))
    if (cacheScopes.value.length > 0) {
      selectedScope.value = cacheScopes.value[0].value
    }
  } catch {
    cacheScopes.value = [
      { label: '看板数据', value: 'dashboard' },
      { label: '报价数据', value: 'quotes' },
      { label: '债券聚合行情', value: 'bonds' },
      { label: '全部缓存', value: 'all' },
    ]
  }
}

async function handleRefreshCache() {
  cacheLoading.value = true
  try {
    const res = await api.post('/api/admin/cache/refresh', null, {
      params: { scope: selectedScope.value === 'all' ? undefined : selectedScope.value },
    })
    message.success(res.data?.message || '缓存刷新成功')
  } catch {
    // handled by interceptor
  } finally {
    cacheLoading.value = false
  }
}

async function handleRefreshAllCache() {
  cacheLoading.value = true
  try {
    const res = await api.post('/api/admin/cache/refresh', null, {
      params: { scope: 'all' },
    })
    message.success(res.data?.message || '全部缓存刷新成功')
  } catch {
    // handled by interceptor
  } finally {
    cacheLoading.value = false
  }
}

async function handleToggleEnabled(id: string, enabled: boolean) {
  try {
    await api.put(`/api/admin/sources/${id}`, { enabled })
    const item = sources.value.find((s) => s.id === id)
    if (item) item.enabled = enabled
  } catch {
    // 错误由 api 拦截器处理
  }
}

onMounted(() => {
  fetchSources()
  fetchCacheScopes()
})
</script>
