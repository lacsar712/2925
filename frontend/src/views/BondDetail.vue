<template>
  <div class="bond-detail">
    <a-breadcrumb class="mb-4">
      <a-breadcrumb-item>
        <router-link to="/market">聚合行情</router-link>
      </a-breadcrumb-item>
      <a-breadcrumb-item>债券详情</a-breadcrumb-item>
    </a-breadcrumb>

    <a-spin :spinning="loading">
      <template v-if="bond">
        <div class="flex justify-between items-start mb-4 gap-3 flex-wrap">
          <h2 class="text-xl font-semibold text-gray-800">{{ bond.name }} ({{ bond.code }})</h2>
          <div class="flex gap-2">
            <a-button
              @click="openQuickAlert"
            >
              <template #icon><BellOutlined /></template>
              设预警
            </a-button>
            <a-button
              :type="isFavorited ? 'default' : 'primary'"
              :loading="favLoading"
              @click="toggleFavorite"
            >
              {{ isFavorited ? '取消收藏' : '收藏' }}
            </a-button>
          </div>
        </div>

        <a-alert
          v-if="bondRules.length > 0"
          class="mb-4"
          type="info"
          show-icon
        >
          <template #message>
            <div class="flex items-center justify-between">
              <span>当前债券已设置 <b>{{ bondRules.length }}</b> 条预警规则</span>
              <a-button type="link" size="small" @click="scrollToRules = !scrollToRules">
                {{ scrollToRules ? '收起' : '展开查看' }}
              </a-button>
            </div>
          </template>
        </a-alert>

        <a-card v-if="scrollToRules" title="当前债券预警规则" class="mb-4" size="small">
          <a-table
            :columns="bondRuleColumns"
            :data-source="bondRules"
            :row-key="(r: any) => r.id"
            :pagination="false"
            size="small"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'alert_type'">
                <a-tag :color="record.alert_type === 'yield' ? 'blue' : 'purple'">
                  {{ record.alert_type === 'yield' ? '收益率' : '净价' }}
                </a-tag>
              </template>
              <template v-else-if="column.key === 'condition'">
                {{ record.condition === 'above' ? '≥ 高于' : '≤ 低于' }}
              </template>
              <template v-else-if="column.key === 'threshold'">
                <span class="tabular-nums font-semibold">
                  {{ Number(record.threshold).toFixed(4) }}
                  {{ record.alert_type === 'yield' ? '%' : '元' }}
                </span>
              </template>
              <template v-else-if="column.key === 'is_enabled'">
                <a-badge :status="record.is_enabled ? 'success' : 'default'" :text="record.is_enabled ? '启用' : '停用'" />
              </template>
              <template v-else-if="column.key === 'actions'">
                <a-space size="small">
                  <a-button type="link" size="small" @click="toggleBondRule(record)">
                    {{ record.is_enabled ? '停用' : '启用' }}
                  </a-button>
                  <a-popconfirm
                    title="删除此预警规则？"
                    ok-text="删除"
                    cancel-text="取消"
                    ok-button-props="{ danger: true }"
                    @confirm="deleteBondRule(record.id)"
                  >
                    <a-button type="link" size="small" danger>删除</a-button>
                  </a-popconfirm>
                </a-space>
              </template>
            </template>
          </a-table>
        </a-card>

        <!-- 债券基本信息 -->
        <a-card title="债券基本信息" class="mb-4">
          <a-descriptions :column="2" bordered size="small">
            <a-descriptions-item label="代码">{{ bond.code }}</a-descriptions-item>
            <a-descriptions-item label="简称">{{ bond.name }}</a-descriptions-item>
            <a-descriptions-item label="品种">{{ bond.bond_type }}</a-descriptions-item>
            <a-descriptions-item label="发行人">{{ bond.issuer }}</a-descriptions-item>
            <a-descriptions-item label="票面利率">
              <span class="tabular-nums">{{ bond.coupon_rate != null ? bond.coupon_rate + '%' : '--' }}</span>
            </a-descriptions-item>
            <a-descriptions-item label="剩余期限">
              <span class="tabular-nums">{{ bond.remaining_term != null ? bond.remaining_term + '年' : '--' }}</span>
            </a-descriptions-item>
            <a-descriptions-item label="评级">{{ bond.credit_rating || '--' }}</a-descriptions-item>
          </a-descriptions>
        </a-card>

        <!-- 全局最优行情摘要 -->
        <a-card title="全局最优行情摘要" class="mb-4">
          <a-row :gutter="24">
            <a-col :span="6">
              <div class="text-gray-500 text-sm mb-1">最优买价</div>
              <div
                class="text-xl font-bold tabular-nums"
                :class="[
                  aggregated?.best_bid_price != null ? 'text-green-600' : '',
                  getFlashClass(`${bondId.value}-best_bid`),
                ]"
              >
                {{ formatPrice(aggregated?.best_bid_price) }}
              </div>
            </a-col>
            <a-col :span="6">
              <div class="text-gray-500 text-sm mb-1">最优卖价</div>
              <div
                class="text-xl font-bold tabular-nums"
                :class="[
                  aggregated?.best_ask_price != null ? 'text-red-600' : '',
                  getFlashClass(`${bondId.value}-best_ask`),
                ]"
              >
                {{ formatPrice(aggregated?.best_ask_price) }}
              </div>
            </a-col>
            <a-col :span="6">
              <div class="text-gray-500 text-sm mb-1">买卖价差</div>
              <div class="text-xl font-semibold tabular-nums">
                {{ formatPrice(aggregated?.spread) }}
              </div>
            </a-col>
            <a-col :span="6">
              <div class="text-gray-500 text-sm mb-1">总报价数量</div>
              <div class="text-xl font-semibold tabular-nums">{{ aggregated?.total_quotes ?? '--' }}</div>
            </a-col>
          </a-row>
          <a-row :gutter="24" class="mt-4">
            <a-col :span="12">
              <div class="text-gray-500 text-sm mb-1">最优买入收益率</div>
              <div
                class="text-lg font-semibold tabular-nums"
                :class="[
                  'text-green-600',
                  getFlashClass(`${bondId.value}-best_bid_yield`),
                ]"
              >
                {{ formatYield(aggregated?.best_bid_yield) }}
              </div>
            </a-col>
            <a-col :span="12">
              <div class="text-gray-500 text-sm mb-1">最优卖出收益率</div>
              <div
                class="text-lg font-semibold tabular-nums"
                :class="[
                  'text-red-600',
                  getFlashClass(`${bondId.value}-best_ask_yield`),
                ]"
              >
                {{ formatYield(aggregated?.best_ask_yield) }}
              </div>
            </a-col>
          </a-row>
        </a-card>

        <!-- 行情源对比区域 -->
        <a-card>
          <a-tabs v-model:active-key="activeTab">
            <a-tab-pane key="sources" tab="各源报价对比">
              <a-table
                :columns="sourceColumns"
                :data-source="aggregated?.sources ?? []"
                :row-key="(r: any) => `${r.source_name}-${r.source_type}`"
                :pagination="false"
                :scroll="{ x: 'max-content' }"
                size="small"
              >
                <template #bodyCell="{ column, record }">
                  <template v-if="column.key === 'source_type'">
                    <a-tag>{{ sourceTypeLabel(record.source_type) }}</a-tag>
                  </template>
                  <template v-else-if="column.key === 'best_bid'">
                    <span
                      class="tabular-nums"
                      :class="[
                        'text-green-600',
                        getFlashClass(`${bondId.value}-${record.source_name}-bid`),
                      ]"
                    >
                      {{ formatPrice(record.best_bid_price) }}
                    </span>
                  </template>
                  <template v-else-if="column.key === 'best_ask'">
                    <span
                      class="tabular-nums"
                      :class="[
                        'text-red-600',
                        getFlashClass(`${bondId.value}-${record.source_name}-ask`),
                      ]"
                    >
                      {{ formatPrice(record.best_ask_price) }}
                    </span>
                  </template>
                  <template v-else-if="column.key === 'bid_yield'">
                    <span
                      class="tabular-nums"
                      :class="getFlashClass(`${bondId.value}-${record.source_name}-bid_yield`)"
                    >
                      {{ formatYield(record.best_bid_yield) }}
                    </span>
                  </template>
                  <template v-else-if="column.key === 'ask_yield'">
                    <span
                      class="tabular-nums"
                      :class="getFlashClass(`${bondId.value}-${record.source_name}-ask_yield`)"
                    >
                      {{ formatYield(record.best_ask_yield) }}
                    </span>
                  </template>
                  <template v-else-if="column.key === 'latest_time'">
                    <span class="tabular-nums">{{ formatDateTime(record.latest_quote_time) }}</span>
                  </template>
                </template>
              </a-table>
            </a-tab-pane>
            <a-tab-pane key="quotes" tab="详细报价列表">
              <a-table
                :columns="quoteColumns"
                :data-source="quotes"
                row-key="id"
                :pagination="false"
                :scroll="{ x: 'max-content' }"
                size="small"
              >
                <template #bodyCell="{ column, record }">
                  <template v-if="column.key === 'source_type'">
                    <a-tag>{{ sourceTypeLabel(record.source_type) }}</a-tag>
                  </template>
                  <template v-else-if="column.key === 'bid_price'">
                    <span class="tabular-nums">{{ formatPrice(record.bid_price) }}</span>
                  </template>
                  <template v-else-if="column.key === 'ask_price'">
                    <span class="tabular-nums">{{ formatPrice(record.ask_price) }}</span>
                  </template>
                  <template v-else-if="column.key === 'bid_yield'">
                    <span class="tabular-nums">{{ formatYield(record.bid_yield) }}</span>
                  </template>
                  <template v-else-if="column.key === 'ask_yield'">
                    <span class="tabular-nums">{{ formatYield(record.ask_yield) }}</span>
                  </template>
                  <template v-else-if="column.key === 'bid_volume'">
                    <span class="tabular-nums">{{ formatVolume(record.bid_volume) }}</span>
                  </template>
                  <template v-else-if="column.key === 'ask_volume'">
                    <span class="tabular-nums">{{ formatVolume(record.ask_volume) }}</span>
                  </template>
                  <template v-else-if="column.key === 'quote_time'">
                    <span class="tabular-nums">{{ formatDateTime(record.quote_time) }}</span>
                  </template>
                </template>
              </a-table>
            </a-tab-pane>
            <a-tab-pane key="trades" tab="成交记录">
              <a-table
                :columns="tradeColumns"
                :data-source="trades"
                row-key="id"
                :pagination="false"
                :scroll="{ x: 'max-content' }"
                size="small"
              >
                <template #bodyCell="{ column, record }">
                  <template v-if="column.key === 'source_type'">
                    <a-tag>{{ sourceTypeLabel(record.source_type) }}</a-tag>
                  </template>
                  <template v-else-if="column.key === 'price'">
                    <span class="tabular-nums">{{ formatPrice(record.price) }}</span>
                  </template>
                  <template v-else-if="column.key === 'yield'">
                    <span class="tabular-nums">{{ formatYield(record.yield_rate) }}</span>
                  </template>
                  <template v-else-if="column.key === 'volume'">
                    <span class="tabular-nums">{{ formatVolume(record.volume) }}</span>
                  </template>
                  <template v-else-if="column.key === 'amount'">
                    <span class="tabular-nums">{{ formatAmount(record.amount) }}</span>
                  </template>
                  <template v-else-if="column.key === 'direction'">
                    <a-tag :color="record.direction === 'buy' ? 'red' : 'green'">
                      {{ record.direction === 'buy' ? '买入' : '卖出' }}
                    </a-tag>
                  </template>
                  <template v-else-if="column.key === 'trade_time'">
                    <span class="tabular-nums">{{ formatDateTime(record.trade_time) }}</span>
                  </template>
                </template>
              </a-table>
            </a-tab-pane>
          </a-tabs>
        </a-card>
      </template>
      <template v-else-if="!loading && error">
        <a-result status="404" title="债券不存在" sub-title="请检查债券 ID 是否正确" />
      </template>
    </a-spin>

    <a-modal
      v-model:open="quickAlertOpen"
      title="快速设置预警"
      :confirm-loading="alertSubmitLoading"
      ok-text="创建预警"
      cancel-text="取消"
      @ok="handleQuickAlertSubmit"
      @cancel="resetQuickAlert"
      width="560px"
    >
      <a-form
        ref="alertFormRef"
        :model="alertFormState"
        :rules="alertFormRules"
        layout="vertical"
      >
        <a-descriptions :column="1" size="small" bordered class="mb-4">
          <a-descriptions-item label="债券">
            {{ bond?.name || '--' }} <span class="text-gray-400 text-xs">({{ bond?.code || '--' }})</span>
          </a-descriptions-item>
        </a-descriptions>

        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="预警类型" name="alert_type">
              <a-radio-group v-model:value="alertFormState.alert_type" button-style="solid">
                <a-radio-button value="yield">收益率 (%)</a-radio-button>
                <a-radio-button value="net_price">净价 (元)</a-radio-button>
              </a-radio-group>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="触发条件" name="condition">
              <a-radio-group v-model:value="alertFormState.condition" button-style="solid">
                <a-radio-button value="above">≥ 高于</a-radio-button>
                <a-radio-button value="below">≤ 低于</a-radio-button>
              </a-radio-group>
            </a-form-item>
          </a-col>
        </a-row>

        <a-form-item label="阈值" name="threshold">
          <a-input-number
            v-model:value="alertFormState.threshold"
            :min="0"
            :step="alertFormState.alert_type === 'yield' ? 0.01 : 0.01"
            :precision="4"
            style="width: 100%"
            :addon-after="alertFormState.alert_type === 'yield' ? '%' : '元'"
          />
          <div class="text-xs text-gray-400 mt-1">
            参考当前值：
            <span v-if="alertFormState.alert_type === 'yield' && midYield !== undefined" class="font-semibold text-blue-600">
              收益率 {{ midYield.toFixed(4) }}%
            </span>
            <span v-else-if="alertFormState.alert_type === 'net_price' && midPrice !== undefined" class="font-semibold text-blue-600">
              净价 {{ midPrice.toFixed(4) }}元
            </span>
            <span v-else>（暂无行情数据）</span>
          </div>
        </a-form-item>

        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="冷却时间" name="trigger_cooldown_minutes">
              <a-input-number
                v-model:value="alertFormState.trigger_cooldown_minutes"
                :min="1"
                :max="1440"
                style="width: 100%"
                addon-after="分钟"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="立即启用" name="is_enabled" value-prop-name="checked">
              <a-switch v-model:checked="alertFormState.is_enabled" />
            </a-form-item>
          </a-col>
        </a-row>

        <a-form-item label="备注" name="description">
          <a-textarea
            v-model:value="alertFormState.description"
            :rows="2"
            placeholder="选填"
            maxlength="500"
            show-count
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import type { FormInstance } from 'ant-design-vue'
import { BellOutlined } from '@ant-design/icons-vue'
import api from '../api'
import {
  formatPrice,
  formatYield,
  formatVolume,
  formatAmount,
  formatDateTime,
  sourceTypeLabel,
} from '../utils/format'
import { useAlertStore, type AlertRule, type AlertRuleCreate } from '../stores/alert'
import { useWebSocketStore, type BondQuoteUpdate } from '../stores/websocket'
import { usePriceFlash } from '../composables/usePriceFlash'

const route = useRoute()
const alertStore = useAlertStore()
const wsStore = useWebSocketStore()
const { compareAndFlash, getFlashClass, clearAll } = usePriceFlash()
const bondId = computed(() => route.params.id as string)

interface Bond {
  id: string
  code: string
  name: string
  bond_type: string
  issuer: string
  coupon_rate?: number
  remaining_term?: number
  credit_rating?: string
}

interface SourceSummary {
  source_name: string
  source_type: string
  best_bid_price?: number
  best_ask_price?: number
  best_bid_yield?: number
  best_ask_yield?: number
  quote_count: number
  latest_quote_time?: string
}

interface Aggregated {
  bond: Bond
  sources: SourceSummary[]
  best_bid_price?: number
  best_ask_price?: number
  best_bid_yield?: number
  best_ask_yield?: number
  spread?: number
  total_quotes: number
}

interface Quote {
  id: string
  source_name?: string
  source_type?: string
  bid_price?: number
  ask_price?: number
  bid_yield?: number
  ask_yield?: number
  bid_volume?: number
  ask_volume?: number
  counterparty?: string
  quote_time?: string
}

interface Trade {
  id: string
  source_name?: string
  source_type?: string
  price: number
  yield_rate?: number
  volume: number
  amount?: number
  direction: string
  counterparty?: string
  trade_time?: string
}

const loading = ref(true)
const error = ref(false)
const bond = ref<Bond | null>(null)
const aggregated = ref<Aggregated | null>(null)
const quotes = ref<Quote[]>([])
const trades = ref<Trade[]>([])
const favorites = ref<string[]>([])
const favLoading = ref(false)
const activeTab = ref('sources')

const bondRules = ref<AlertRule[]>([])
const scrollToRules = ref(false)

const isFavorited = computed(() => bondId.value && favorites.value.includes(bondId.value))

const midPrice = computed(() => {
  const b = aggregated.value?.best_bid_price
  const a = aggregated.value?.best_ask_price
  if (b != null && a != null) return (b + a) / 2
  if (b != null) return b
  if (a != null) return a
  return undefined
})

const midYield = computed(() => {
  const b = aggregated.value?.best_bid_yield
  const a = aggregated.value?.best_ask_yield
  if (b != null && a != null) return (b + a) / 2
  if (b != null) return b
  if (a != null) return a
  return undefined
})

const sourceColumns = [
  { title: '行情源', dataIndex: 'source_name', key: 'source_name' },
  { title: '源类型', key: 'source_type', width: 120 },
  { title: '最优买价', key: 'best_bid', width: 100 },
  { title: '最优卖价', key: 'best_ask', width: 100 },
  { title: '买入收益率', key: 'bid_yield', width: 110 },
  { title: '卖出收益率', key: 'ask_yield', width: 110 },
  { title: '报价数量', dataIndex: 'quote_count', key: 'quote_count', width: 90 },
  { title: '最新时间', key: 'latest_time', width: 160 },
]

const quoteColumns = [
  { title: '行情源', dataIndex: 'source_name', key: 'source_name' },
  { title: '源类型', key: 'source_type', width: 120 },
  { title: '买价', key: 'bid_price', width: 90 },
  { title: '卖价', key: 'ask_price', width: 90 },
  { title: '买入收益率', key: 'bid_yield', width: 110 },
  { title: '卖出收益率', key: 'ask_yield', width: 110 },
  { title: '买入面额', key: 'bid_volume', width: 100 },
  { title: '卖出面额', key: 'ask_volume', width: 100 },
  { title: '对手方', dataIndex: 'counterparty', key: 'counterparty' },
  { title: '时间', key: 'quote_time', width: 160 },
]

const tradeColumns = [
  { title: '行情源', dataIndex: 'source_name', key: 'source_name' },
  { title: '源类型', key: 'source_type', width: 120 },
  { title: '成交价', key: 'price', width: 90 },
  { title: '收益率', key: 'yield', width: 90 },
  { title: '成交面额', key: 'volume', width: 100 },
  { title: '成交金额', key: 'amount', width: 100 },
  { title: '方向', key: 'direction', width: 80 },
  { title: '对手方', dataIndex: 'counterparty', key: 'counterparty' },
  { title: '时间', key: 'trade_time', width: 160 },
]

const bondRuleColumns = [
  { title: '类型', key: 'alert_type', width: 100 },
  { title: '条件', key: 'condition', width: 100 },
  { title: '阈值', key: 'threshold', width: 140 },
  { title: '冷却', dataIndex: 'trigger_cooldown_minutes', key: 'cooldown', width: 80, customRender: ({ text }: { text: number }) => `${text}分` },
  { title: '状态', key: 'is_enabled', width: 100 },
  { title: '备注', dataIndex: 'description', key: 'desc', ellipsis: true },
  { title: '操作', key: 'actions', width: 160 },
]

async function fetchBondRules() {
  if (!bondId.value) return
  try {
    const res = await api.get<{ items: AlertRule[]; total: number }>('/api/alerts/rules', {
      params: { bond_id: bondId.value, page: 1, page_size: 100 },
    })
    bondRules.value = res.data.items
  } catch {
    bondRules.value = []
  }
}

async function fetchData() {
  if (!bondId.value) return
  loading.value = true
  error.value = false
  try {
    const [bondRes, aggRes, quotesRes, tradesRes, favRes] = await Promise.all([
      api.get<Bond>(`/api/bonds/${bondId.value}`),
      api.get<Aggregated>(`/api/bonds/${bondId.value}/aggregated`),
      api.get<Quote[]>(`/api/bonds/${bondId.value}/quotes`),
      api.get<Trade[]>(`/api/bonds/${bondId.value}/trades`),
      api.get<Bond[]>('/api/favorites'),
    ])
    bond.value = bondRes.data
    aggregated.value = aggRes.data
    quotes.value = quotesRes.data
    trades.value = tradesRes.data
    favorites.value = (favRes.data || []).map((b) => b.id)
    await fetchBondRules()
  } catch (e) {
    error.value = true
    bond.value = null
    aggregated.value = null
    quotes.value = []
    trades.value = []
  } finally {
    loading.value = false
  }
}

async function toggleFavorite() {
  if (!bondId.value || favLoading.value) return
  favLoading.value = true
  try {
    if (isFavorited.value) {
      await api.delete(`/api/favorites/${bondId.value}`)
      favorites.value = favorites.value.filter((id) => id !== bondId.value)
      message.success('已取消收藏')
    } else {
      await api.post(`/api/favorites/${bondId.value}`)
      favorites.value = [...favorites.value, bondId.value]
      message.success('收藏成功')
    }
  } catch {
    // message 由 interceptor 处理
  } finally {
    favLoading.value = false
  }
}

async function toggleBondRule(record: AlertRule) {
  try {
    const res = await alertStore.toggleRule(record.id)
    record.is_enabled = res.is_enabled
    message.success(res.message)
  } catch {
    // handled
  }
}

async function deleteBondRule(id: string) {
  try {
    await alertStore.deleteRule(id)
    bondRules.value = bondRules.value.filter((r) => r.id !== id)
    message.success('删除成功')
  } catch {
    // handled
  }
}

const quickAlertOpen = ref(false)
const alertSubmitLoading = ref(false)
const alertFormRef = ref<FormInstance>()
const defaultAlertForm = () => ({
  alert_type: 'yield' as 'yield' | 'net_price',
  condition: 'above' as 'above' | 'below',
  threshold: undefined as number | undefined,
  trigger_cooldown_minutes: 5,
  is_enabled: true,
  description: '',
})
const alertFormState = reactive(defaultAlertForm())

const alertFormRules = {
  alert_type: [{ required: true, message: '请选择预警类型', trigger: 'change' as const }],
  condition: [{ required: true, message: '请选择触发条件', trigger: 'change' as const }],
  threshold: [{ required: true, message: '请输入阈值', trigger: 'blur' as const, type: 'number' as const, min: 0 }],
}

function openQuickAlert() {
  Object.assign(alertFormState, defaultAlertForm())
  if (midYield.value !== undefined) {
    alertFormState.threshold = Number(midYield.value.toFixed(4))
  } else if (midPrice.value !== undefined) {
    alertFormState.alert_type = 'net_price'
    alertFormState.threshold = Number(midPrice.value.toFixed(4))
  }
  quickAlertOpen.value = true
}

function resetQuickAlert() {
  quickAlertOpen.value = false
  Object.assign(alertFormState, defaultAlertForm())
  alertFormRef.value?.clearValidate()
}

async function handleQuickAlertSubmit() {
  try {
    await alertFormRef.value?.validate()
  } catch {
    return
  }
  if (!bondId.value) return
  alertSubmitLoading.value = true
  try {
    const data: AlertRuleCreate = {
      bond_id: bondId.value,
      alert_type: alertFormState.alert_type,
      condition: alertFormState.condition,
      threshold: alertFormState.threshold as number,
      is_enabled: alertFormState.is_enabled,
      trigger_cooldown_minutes: alertFormState.trigger_cooldown_minutes,
      description: alertFormState.description || undefined,
    }
    await alertStore.createRule(data)
    message.success('预警规则创建成功')
    quickAlertOpen.value = false
    await fetchBondRules()
    scrollToRules.value = true
  } catch {
    // handled
  } finally {
    alertSubmitLoading.value = false
  }
}

watch(bondId, fetchData, { immediate: true })

const prevPrices = new Map<string, { best_bid?: number; best_ask?: number; best_bid_yield?: number; best_ask_yield?: number; sources?: Map<string, { bid?: number; ask?: number; bid_yield?: number; ask_yield?: number }> }>()

function handleQuoteUpdate(update: BondQuoteUpdate) {
  if (!aggregated.value) return

  const prev = prevPrices.get(update.bond_id) || {}

  compareAndFlash(`${update.bond_id}-best_bid`, update.best_bid_price, prev.best_bid)
  compareAndFlash(`${update.bond_id}-best_ask`, update.best_ask_price, prev.best_ask)
  compareAndFlash(`${update.bond_id}-best_bid_yield`, update.best_bid_yield, prev.best_bid_yield)
  compareAndFlash(`${update.bond_id}-best_ask_yield`, update.best_ask_yield, prev.best_ask_yield)

  const prevSources = prev.sources || new Map()
  update.sources.forEach((src) => {
    const prevSrc = prevSources.get(src.source_name) || {}
    compareAndFlash(`${update.bond_id}-${src.source_name}-bid`, src.best_bid_price, prevSrc.bid)
    compareAndFlash(`${update.bond_id}-${src.source_name}-ask`, src.best_ask_price, prevSrc.ask)
    compareAndFlash(`${update.bond_id}-${src.source_name}-bid_yield`, src.best_bid_yield, prevSrc.bid_yield)
    compareAndFlash(`${update.bond_id}-${src.source_name}-ask_yield`, src.best_ask_yield, prevSrc.ask_yield)
  })

  const newSourcesMap = new Map<string, { bid?: number; ask?: number; bid_yield?: number; ask_yield?: number }>()
  update.sources.forEach((src) => {
    newSourcesMap.set(src.source_name, {
      bid: src.best_bid_price,
      ask: src.best_ask_price,
      bid_yield: src.best_bid_yield,
      ask_yield: src.best_ask_yield,
    })
  })

  prevPrices.set(update.bond_id, {
    best_bid: update.best_bid_price,
    best_ask: update.best_ask_price,
    best_bid_yield: update.best_bid_yield,
    best_ask_yield: update.best_ask_yield,
    sources: newSourcesMap,
  })

  aggregated.value = {
    ...aggregated.value,
    sources: update.sources,
    best_bid_price: update.best_bid_price,
    best_ask_price: update.best_ask_price,
    best_bid_yield: update.best_bid_yield,
    best_ask_yield: update.best_ask_yield,
    spread: update.spread,
    total_quotes: update.total_quotes,
  }
}

onMounted(() => {
  if (bondId.value) {
    wsStore.subscribeBond(bondId.value, handleQuoteUpdate)
  }
})

onUnmounted(() => {
  if (bondId.value) {
    wsStore.unsubscribeBond(bondId.value, handleQuoteUpdate)
  }
  clearAll()
  prevPrices.clear()
})
</script>
