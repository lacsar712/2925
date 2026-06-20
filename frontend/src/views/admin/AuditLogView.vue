<template>
  <div class="audit-log-view p-4">
    <a-card class="rounded-lg">
      <template #title>
        <div class="flex items-center justify-between w-full">
          <span class="text-lg font-semibold">操作审计日志</span>
          <span class="text-sm text-gray-400">日志只读，不可篡改</span>
        </div>
      </template>

      <div class="mb-4 flex gap-3 flex-wrap items-center">
        <a-input
          v-model:value="filterUsername"
          placeholder="搜索用户名"
          style="width: 180px"
          allow-clear
          @pressEnter="loadLogs(1)"
        />
        <a-select
          v-model:value="filterActionType"
          placeholder="动作类型"
          style="width: 180px"
          allow-clear
          @change="loadLogs(1)"
        >
          <a-select-option v-for="t in actionTypes" :key="t.key" :value="t.key">
            {{ t.label }}
          </a-select-option>
        </a-select>
        <a-range-picker
          v-model:value="dateRange"
          show-time
          format="YYYY-MM-DD HH:mm"
          placeholder="开始-结束时间"
          style="width: 360px"
          @change="loadLogs(1)"
        />
        <a-button type="primary" @click="loadLogs(1)">
          <template #icon><SearchOutlined /></template>
          查询
        </a-button>
        <a-button @click="resetFilters">重置</a-button>
      </div>

      <a-spin :spinning="loading">
        <a-table
          :data-source="logs"
          :columns="columns"
          :pagination="false"
          :row-key="(r) => r.id"
          size="middle"
        >
          <template #expandedRowRender="{ record }">
            <div class="expanded-content">
              <a-descriptions :column="2" size="small" bordered>
                <a-descriptions-item label="日志ID">
                  <span class="font-mono text-xs">{{ record.id }}</span>
                </a-descriptions-item>
                <a-descriptions-item label="用户ID">
                  <span class="font-mono text-xs">{{ record.user_id || '--' }}</span>
                </a-descriptions-item>
                <a-descriptions-item label="来源IP">
                  <span class="font-mono">{{ record.ip_address || '--' }}</span>
                </a-descriptions-item>
                <a-descriptions-item label="发生时间">
                  <span class="tabular-nums">{{ formatDateTime(record.created_at) }}</span>
                </a-descriptions-item>
                <a-descriptions-item label="操作对象" :span="2">
                  {{ record.action_target || '--' }}
                </a-descriptions-item>
                <a-descriptions-item label="操作摘要" :span="2">
                  {{ record.action_summary }}
                </a-descriptions-item>
                <a-descriptions-item label="User-Agent" :span="2">
                  <span class="text-gray-500 text-xs break-all">{{ record.user_agent || '--' }}</span>
                </a-descriptions-item>
                <a-descriptions-item label="详细信息" :span="2">
                  <pre v-if="record.detail" class="detail-json">{{ formatDetail(record.detail) }}</pre>
                  <span v-else class="text-gray-400">--</span>
                </a-descriptions-item>
              </a-descriptions>
            </div>
          </template>

          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'action_type'">
              <a-tag :color="actionTypeColor(record.action_type)">
                {{ actionTypeLabel(record.action_type) }}
              </a-tag>
            </template>
            <template v-else-if="column.key === 'username'">
              <div class="flex items-center gap-2">
                <a-avatar size="small" :style="{ backgroundColor: getUserColor(record.username) }">
                  {{ record.username.charAt(0).toUpperCase() }}
                </a-avatar>
                <span>{{ record.username }}</span>
              </div>
            </template>
            <template v-else-if="column.key === 'created_at'">
              <span class="tabular-nums text-gray-600">
                {{ formatDateTime(record.created_at) }}
              </span>
            </template>
            <template v-else-if="column.key === 'ip_address'">
              <span class="text-gray-500 font-mono text-sm">
                {{ record.ip_address || '--' }}
              </span>
            </template>
          </template>
        </a-table>

        <div class="flex justify-end mt-4">
          <a-pagination
            v-model:current="currentPage"
            :total="total"
            :page-size="pageSize"
            :show-size-changer="true"
            :page-size-options="['10', '20', '50', '100']"
            :show-total="(t) => `共 ${t} 条记录`"
            @change="handlePageChange"
            @showSizeChange="handleSizeChange"
          />
        </div>
      </a-spin>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { SearchOutlined } from '@ant-design/icons-vue'
import api from '../../api'
import { formatDateTime } from '../../utils/format'
import type { TableColumnsType } from 'ant-design-vue'

interface AuditLogItem {
  id: string
  user_id: string | null
  username: string
  action_type: string
  action_target: string | null
  action_summary: string
  detail: Record<string, any> | null
  ip_address: string | null
  user_agent: string | null
  created_at: string
}

interface ActionType {
  key: string
  label: string
}

const loading = ref(false)
const logs = ref<AuditLogItem[]>([])
const actionTypes = ref<ActionType[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

const filterUsername = ref('')
const filterActionType = ref<string | undefined>(undefined)
const dateRange = ref<[Date, Date] | null>(null)

const columns: TableColumnsType = [
  { title: '操作人', dataIndex: 'username', key: 'username', width: 160 },
  { title: '动作类型', dataIndex: 'action_type', key: 'action_type', width: 140 },
  { title: '操作对象', dataIndex: 'action_target', key: 'action_target', width: 200, ellipsis: true },
  { title: '操作摘要', dataIndex: 'action_summary', key: 'action_summary', ellipsis: true },
  { title: '来源IP', dataIndex: 'ip_address', key: 'ip_address', width: 140 },
  { title: '发生时间', dataIndex: 'created_at', key: 'created_at', width: 180 },
]

const actionTypeMap: Record<string, string> = {
  user_login: '用户登录',
  user_logout: '用户登出',
  user_login_failed: '登录失败',
  favorite_add: '添加收藏',
  favorite_remove: '取消收藏',
  source_enable: '启用行情源',
  source_disable: '禁用行情源',
  source_update: '更新行情源',
  user_create: '创建用户',
  user_update: '更新用户',
  user_delete: '删除用户',
  cache_refresh: '刷新缓存',
  watchlist_group_create: '创建分组',
  watchlist_group_update: '更新分组',
  watchlist_group_delete: '删除分组',
  alert_rule_create: '创建预警规则',
  alert_rule_update: '更新预警规则',
  alert_rule_delete: '删除预警规则',
}

const actionColorMap: Record<string, string> = {
  user_login: 'green',
  user_logout: 'default',
  user_login_failed: 'red',
  favorite_add: 'blue',
  favorite_remove: 'orange',
  source_enable: 'green',
  source_disable: 'red',
  source_update: 'blue',
  user_create: 'green',
  user_update: 'blue',
  user_delete: 'red',
  cache_refresh: 'purple',
  watchlist_group_create: 'green',
  watchlist_group_update: 'blue',
  watchlist_group_delete: 'red',
  alert_rule_create: 'green',
  alert_rule_update: 'blue',
  alert_rule_delete: 'red',
}

function actionTypeLabel(type: string): string {
  return actionTypeMap[type] || type
}

function actionTypeColor(type: string): string {
  return actionColorMap[type] || 'default'
}

function getUserColor(username: string): string {
  const colors = [
    '#1890ff', '#52c41a', '#faad14', '#f5222d',
    '#722ed1', '#13c2c2', '#eb2f96', '#fa8c16',
  ]
  let hash = 0
  for (let i = 0; i < username.length; i++) {
    hash = username.charCodeAt(i) + ((hash << 5) - hash)
  }
  return colors[Math.abs(hash) % colors.length]
}

function formatDetail(detail: Record<string, any>): string {
  try {
    return JSON.stringify(detail, null, 2)
  } catch {
    return String(detail)
  }
}

async function loadActionTypes() {
  try {
    const res = await api.get<ActionType[]>('/api/admin/audit-action-types')
    actionTypes.value = res.data
  } catch {
    actionTypes.value = Object.entries(actionTypeMap).map(([key, label]) => ({ key, label }))
  }
}

async function loadLogs(page: number) {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page,
      page_size: pageSize.value,
    }

    if (filterUsername.value.trim()) {
      params.username = filterUsername.value.trim()
    }
    if (filterActionType.value) {
      params.action_type = filterActionType.value
    }
    if (dateRange.value && dateRange.value[0]) {
      params.start_date = dateRange.value[0].toISOString()
    }
    if (dateRange.value && dateRange.value[1]) {
      params.end_date = dateRange.value[1].toISOString()
    }

    const res = await api.get<{ items: AuditLogItem[]; total: number; page: number; page_size: number }>(
      '/api/admin/audit-logs',
      { params }
    )
    logs.value = res.data.items
    total.value = res.data.total
    currentPage.value = res.data.page
    pageSize.value = res.data.page_size
  } catch {
    message.error('加载审计日志失败')
  } finally {
    loading.value = false
  }
}

function handlePageChange(page: number, size: number) {
  pageSize.value = size
  loadLogs(page)
}

function handleSizeChange(current: number, size: number) {
  pageSize.value = size
  loadLogs(1)
}

function resetFilters() {
  filterUsername.value = ''
  filterActionType.value = undefined
  dateRange.value = null
  loadLogs(1)
}

onMounted(() => {
  loadActionTypes()
  loadLogs(1)
})
</script>

<style scoped>
.audit-log-view {
  min-height: 100%;
}

.expanded-content {
  padding: 8px 16px 16px 48px;
  background: #fafafa;
}

.detail-json {
  margin: 0;
  padding: 12px;
  background: #fff;
  border: 1px solid #f0f0f0;
  border-radius: 4px;
  font-family: 'SF Mono', Monaco, 'Cascadia Code', Consolas, monospace;
  font-size: 12px;
  line-height: 1.5;
  max-height: 300px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
