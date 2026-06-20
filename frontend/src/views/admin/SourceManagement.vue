<template>
  <div class="source-management p-4">
    <a-card class="rounded-lg">
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
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
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

const loading = ref(false)
const sources = ref<SourceItem[]>([])

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

async function handleToggleEnabled(id: string, enabled: boolean) {
  try {
    await api.put(`/api/admin/sources/${id}`, { enabled })
    const item = sources.value.find((s) => s.id === id)
    if (item) item.enabled = enabled
  } catch {
    // 错误由 api 拦截器处理
  }
}

onMounted(fetchSources)
</script>
