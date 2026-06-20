<template>
  <div class="alert-rules">
    <a-breadcrumb class="mb-4">
      <a-breadcrumb-item>
        <router-link to="/dashboard">行情看板</router-link>
      </a-breadcrumb-item>
      <a-breadcrumb-item>预警规则管理</a-breadcrumb-item>
    </a-breadcrumb>

    <a-card>
      <template #title>
        <div class="flex items-center justify-between w-full">
          <span class="text-lg font-semibold">预警规则管理</span>
          <div class="flex gap-2">
            <a-button type="primary" @click="openCreateModal">
              <template #icon><PlusOutlined /></template>
              新增预警
            </a-button>
            <router-link to="/alerts/history">
              <a-button>
                <template #icon><HistoryOutlined /></template>
                触发历史
              </a-button>
            </router-link>
          </div>
        </div>
      </template>

      <div class="mb-4 flex gap-3 flex-wrap items-center">
        <a-input-search
          v-model:value="searchKeyword"
          placeholder="搜索债券代码/简称"
          style="width: 240px"
          allow-clear
          @search="loadRules(1)"
          @change="onKeywordChange"
        />
        <a-select
          v-model:value="filterEnabled"
          placeholder="启用状态"
          style="width: 140px"
          allow-clear
          @change="loadRules(1)"
        >
          <a-select-option :value="true">已启用</a-select-option>
          <a-select-option :value="false">已停用</a-select-option>
        </a-select>
        <a-select
          v-model:value="filterType"
          placeholder="预警类型"
          style="width: 140px"
          allow-clear
          @change="loadRules(1)"
        >
          <a-select-option value="yield">收益率</a-select-option>
          <a-select-option value="net_price">净价</a-select-option>
        </a-select>
      </div>

      <a-spin :spinning="loading">
        <a-table
          :columns="columns"
          :data-source="rules"
          :row-key="(r) => r.id"
          :pagination="paginationConfig"
          size="middle"
          @change="handleTableChange"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'bond'">
              <router-link :to="`/market/${record.bond_id}`" class="text-blue-600 hover:underline">
                {{ record.bond?.name || '--' }}
                <span class="text-gray-500 text-xs ml-1">({{ record.bond?.code || '--' }})</span>
              </router-link>
            </template>
            <template v-else-if="column.key === 'alert_type'">
              <a-tag :color="record.alert_type === 'yield' ? 'blue' : 'purple'">
                {{ record.alert_type === 'yield' ? '收益率' : '净价' }}
              </a-tag>
            </template>
            <template v-else-if="column.key === 'condition'">
              <span>
                {{ record.condition === 'above' ? '≥ 高于' : '≤ 低于' }}
              </span>
            </template>
            <template v-else-if="column.key === 'threshold'">
              <span class="tabular-nums font-semibold">
                {{ Number(record.threshold).toFixed(4) }}
                {{ record.alert_type === 'yield' ? '%' : '元' }}
              </span>
            </template>
            <template v-else-if="column.key === 'is_enabled'">
              <a-badge
                :status="record.is_enabled ? 'success' : 'default'"
                :text="record.is_enabled ? '启用中' : '已停用'"
              />
            </template>
            <template v-else-if="column.key === 'last_triggered_at'">
              <span class="tabular-nums text-xs text-gray-500">
                {{ record.last_triggered_at ? formatDateTime(record.last_triggered_at) : '未触发' }}
              </span>
            </template>
            <template v-else-if="column.key === 'actions'">
              <a-space size="small">
                <a-button type="link" size="small" @click="toggleRule(record)">
                  {{ record.is_enabled ? '停用' : '启用' }}
                </a-button>
                <a-button type="link" size="small" @click="openEditModal(record)">编辑</a-button>
                <a-popconfirm
                  title="确定要删除此预警规则吗？"
                  ok-text="删除"
                  cancel-text="取消"
                  ok-button-props="{ danger: true }"
                  @confirm="deleteRule(record.id)"
                >
                  <a-button type="link" size="small" danger>删除</a-button>
                </a-popconfirm>
              </a-space>
            </template>
          </template>
        </a-table>
      </a-spin>
    </a-card>

    <a-modal
      v-model:open="modalOpen"
      :title="isEdit ? '编辑预警规则' : '新增预警规则'"
      :confirm-loading="submitLoading"
      ok-text="确认"
      cancel-text="取消"
      @ok="handleSubmit"
      @cancel="resetForm"
    >
      <a-form
        ref="formRef"
        :model="formState"
        :rules="formRules"
        layout="vertical"
        :label-col="{ span: 6 }"
      >
        <a-form-item label="选择债券" name="bond_id">
          <a-select
            v-model:value="formState.bond_id"
            show-search
            :filter-option="false"
            placeholder="搜索并选择债券"
            :loading="bondSearchLoading"
            style="width: 100%"
            @search="searchBonds"
            :disabled="isEdit"
          >
            <a-select-option v-for="b in bondOptions" :key="b.id" :value="b.id">
              {{ b.name }} ({{ b.code }}) - {{ b.bond_type }}
            </a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="预警类型" name="alert_type">
          <a-radio-group v-model:value="formState.alert_type">
            <a-radio-button value="yield">收益率 (%)</a-radio-button>
            <a-radio-button value="net_price">净价 (元)</a-radio-button>
          </a-radio-group>
        </a-form-item>

        <a-form-item label="触发条件" name="condition">
          <a-radio-group v-model:value="formState.condition">
            <a-radio-button value="above">高于/大于等于</a-radio-button>
            <a-radio-button value="below">低于/小于等于</a-radio-button>
          </a-radio-group>
        </a-form-item>

        <a-form-item label="阈值" name="threshold">
          <a-input-number
            v-model:value="formState.threshold"
            :min="0"
            :step="formState.alert_type === 'yield' ? 0.01 : 0.01"
            :precision="formState.alert_type === 'yield' ? 4 : 4"
            style="width: 100%"
            :addon-after="formState.alert_type === 'yield' ? '%' : '元'"
          />
        </a-form-item>

        <a-form-item label="冷却时间" name="trigger_cooldown_minutes">
          <a-input-number
            v-model:value="formState.trigger_cooldown_minutes"
            :min="1"
            :max="1440"
            style="width: 100%"
            addon-after="分钟"
          />
          <div class="text-xs text-gray-400 mt-1">避免同一规则在短时间内重复触发，默认5分钟</div>
        </a-form-item>

        <a-form-item label="启用" name="is_enabled" value-prop-name="checked">
          <a-switch v-model:checked="formState.is_enabled" />
        </a-form-item>

        <a-form-item label="备注" name="description">
          <a-textarea
            v-model:value="formState.description"
            :rows="2"
            placeholder="选填，用于备注该预警规则的用途"
            maxlength="500"
            show-count
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import type { FormInstance, TablePaginationConfig } from 'ant-design-vue'
import { PlusOutlined, HistoryOutlined } from '@ant-design/icons-vue'
import api from '../api'
import { formatDateTime } from '../utils/format'
import { useAlertStore, type AlertRule, type AlertRuleCreate, type AlertRuleUpdate } from '../stores/alert'

const router = useRouter()
const alertStore = useAlertStore()

const loading = ref(false)
const rules = ref<AlertRule[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const searchKeyword = ref<string>('')
const filterEnabled = ref<boolean | undefined>(undefined)
const filterType = ref<string | undefined>(undefined)

const columns = [
  { title: '债券', key: 'bond', width: 220 },
  { title: '类型', key: 'alert_type', width: 100 },
  { title: '条件', key: 'condition', width: 120 },
  { title: '阈值', key: 'threshold', width: 140 },
  { title: '冷却时间', dataIndex: 'trigger_cooldown_minutes', key: 'cooldown', width: 100, customRender: ({ text }: { text: number }) => `${text}分钟` },
  { title: '状态', key: 'is_enabled', width: 100 },
  { title: '最近触发', key: 'last_triggered_at', width: 170 },
  { title: '备注', dataIndex: 'description', key: 'description', ellipsis: true },
  { title: '操作', key: 'actions', width: 200, fixed: 'right' as const },
]

const paginationConfig = computed(() => ({
  current: currentPage.value,
  pageSize: pageSize.value,
  total: total.value,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (t: number) => `共 ${t} 条`,
}))

let keywordDebounceTimer: number | null = null
function onKeywordChange() {
  if (keywordDebounceTimer) clearTimeout(keywordDebounceTimer)
  keywordDebounceTimer = window.setTimeout(() => {
    loadRules(1)
  }, 400)
}

async function loadRules(page = currentPage.value) {
  loading.value = true
  try {
    const params: Record<string, unknown> = {
      page,
      page_size: pageSize.value,
    }
    if (searchKeyword.value) params.keyword = searchKeyword.value
    if (filterEnabled.value !== undefined) params.is_enabled = filterEnabled.value
    if (filterType.value) params.alert_type = filterType.value

    const res = await api.get<{ items: AlertRule[]; total: number; page: number; page_size: number }>(
      '/api/alerts/rules',
      { params }
    )
    rules.value = res.data.items
    total.value = res.data.total
    currentPage.value = page
  } catch {
    // handled by interceptor
  } finally {
    loading.value = false
  }
}

function handleTableChange(pag: TablePaginationConfig) {
  if (pag.current !== currentPage.value || pag.pageSize !== pageSize.value) {
    currentPage.value = pag.current || 1
    pageSize.value = pag.pageSize || 20
    loadRules(currentPage.value)
  }
}

async function toggleRule(record: AlertRule) {
  try {
    const res = await alertStore.toggleRule(record.id)
    record.is_enabled = res.is_enabled
    message.success(res.message)
  } catch {
    // handled
  }
}

async function deleteRule(id: string) {
  try {
    await alertStore.deleteRule(id)
    message.success('删除成功')
    loadRules(currentPage.value)
  } catch {
    // handled
  }
}

const modalOpen = ref(false)
const isEdit = ref(false)
const submitLoading = ref(false)
const editingId = ref<string | null>(null)
const formRef = ref<FormInstance>()

const defaultForm = () => ({
  bond_id: '' as string,
  alert_type: 'yield' as 'yield' | 'net_price',
  condition: 'above' as 'above' | 'below',
  threshold: undefined as number | undefined,
  is_enabled: true,
  trigger_cooldown_minutes: 5,
  description: '',
})

const formState = reactive(defaultForm())

const formRules = {
  bond_id: [{ required: true, message: '请选择债券', trigger: 'change' as const }],
  alert_type: [{ required: true, message: '请选择预警类型', trigger: 'change' as const }],
  condition: [{ required: true, message: '请选择触发条件', trigger: 'change' as const }],
  threshold: [{ required: true, message: '请输入阈值', trigger: 'blur' as const, type: 'number' as const, min: 0 }],
}

const bondSearchLoading = ref(false)
const bondOptions = ref<Array<{ id: string; code: string; name: string; bond_type: string }>>([])

async function searchBonds(keyword: string) {
  if (!keyword || keyword.length < 1) {
    bondOptions.value = []
    return
  }
  bondSearchLoading.value = true
  try {
    const res = await api.get<{ items: Array<{ id: string; code: string; name: string; bond_type: string }> }>(
      '/api/bonds',
      { params: { keyword, page: 1, page_size: 20 } }
    )
    bondOptions.value = res.data.items
  } finally {
    bondSearchLoading.value = false
  }
}

function openCreateModal() {
  isEdit.value = false
  editingId.value = null
  Object.assign(formState, defaultForm())
  bondOptions.value = []
  modalOpen.value = true
}

function openEditModal(record: AlertRule) {
  isEdit.value = true
  editingId.value = record.id
  Object.assign(formState, {
    bond_id: record.bond_id,
    alert_type: record.alert_type,
    condition: record.condition,
    threshold: Number(record.threshold),
    is_enabled: record.is_enabled,
    trigger_cooldown_minutes: record.trigger_cooldown_minutes,
    description: record.description || '',
  })
  bondOptions.value = record.bond
    ? [{ id: record.bond.id, code: record.bond.code, name: record.bond.name, bond_type: record.bond.bond_type }]
    : []
  modalOpen.value = true
}

function resetForm() {
  modalOpen.value = false
  Object.assign(formState, defaultForm())
  formRef.value?.clearValidate()
}

async function handleSubmit() {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }

  submitLoading.value = true
  try {
    if (isEdit.value && editingId.value) {
      const data: AlertRuleUpdate = {
        alert_type: formState.alert_type,
        condition: formState.condition,
        threshold: formState.threshold,
        is_enabled: formState.is_enabled,
        trigger_cooldown_minutes: formState.trigger_cooldown_minutes,
        description: formState.description || undefined,
      }
      await alertStore.updateRule(editingId.value, data)
      message.success('更新成功')
    } else {
      const data: AlertRuleCreate = {
        bond_id: formState.bond_id,
        alert_type: formState.alert_type,
        condition: formState.condition,
        threshold: formState.threshold as number,
        is_enabled: formState.is_enabled,
        trigger_cooldown_minutes: formState.trigger_cooldown_minutes,
        description: formState.description || undefined,
      }
      await alertStore.createRule(data)
      message.success('创建成功')
    }
    modalOpen.value = false
    loadRules(currentPage.value)
  } catch {
    // handled
  } finally {
    submitLoading.value = false
  }
}

loadRules(1)
</script>
