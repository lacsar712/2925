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
        <div class="flex justify-between items-start mb-4">
          <h2 class="text-xl font-semibold text-gray-800">{{ bond.name }} ({{ bond.code }})</h2>
          <a-button
            :type="isFavorited ? 'default' : 'primary'"
            :loading="favLoading"
            @click="toggleFavorite"
          >
            {{ isFavorited ? '取消收藏' : '收藏' }}
          </a-button>
        </div>

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
              <div class="text-xl font-bold text-green-600 tabular-nums">
                {{ formatPrice(aggregated?.best_bid_price) }}
              </div>
            </a-col>
            <a-col :span="6">
              <div class="text-gray-500 text-sm mb-1">最优卖价</div>
              <div class="text-xl font-bold text-red-600 tabular-nums">
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
              <div class="text-lg font-semibold tabular-nums text-green-600">
                {{ formatYield(aggregated?.best_bid_yield) }}
              </div>
            </a-col>
            <a-col :span="12">
              <div class="text-gray-500 text-sm mb-1">最优卖出收益率</div>
              <div class="text-lg font-semibold tabular-nums text-red-600">
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
                :row-key="(r) => `${r.source_name}-${r.source_type}`"
                :pagination="false"
                :scroll="{ x: 'max-content' }"
                size="small"
              >
                <template #bodyCell="{ column, record }">
                  <template v-if="column.key === 'source_type'">
                    <a-tag>{{ sourceTypeLabel(record.source_type) }}</a-tag>
                  </template>
                  <template v-else-if="column.key === 'best_bid'">
                    <span class="tabular-nums text-green-600">{{ formatPrice(record.best_bid_price) }}</span>
                  </template>
                  <template v-else-if="column.key === 'best_ask'">
                    <span class="tabular-nums text-red-600">{{ formatPrice(record.best_ask_price) }}</span>
                  </template>
                  <template v-else-if="column.key === 'bid_yield'">
                    <span class="tabular-nums">{{ formatYield(record.best_bid_yield) }}</span>
                  </template>
                  <template v-else-if="column.key === 'ask_yield'">
                    <span class="tabular-nums">{{ formatYield(record.best_ask_yield) }}</span>
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
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import api from '../api'
import {
  formatPrice,
  formatYield,
  formatVolume,
  formatAmount,
  formatDateTime,
  sourceTypeLabel,
} from '../utils/format'

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

const route = useRoute()
const bondId = computed(() => route.params.id as string)

const loading = ref(true)
const error = ref(false)
const bond = ref<Bond | null>(null)
const aggregated = ref<Aggregated | null>(null)
const quotes = ref<Quote[]>([])
const trades = ref<Trade[]>([])
const favorites = ref<string[]>([])
const favLoading = ref(false)
const activeTab = ref('sources')

const isFavorited = computed(() => bondId.value && favorites.value.includes(bondId.value))

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

watch(bondId, fetchData, { immediate: true })
</script>
