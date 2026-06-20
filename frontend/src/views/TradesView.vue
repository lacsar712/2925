<template>
  <div class="trades-view">
    <h2 class="text-xl font-semibold text-gray-800 mb-4">成交记录</h2>

    <!-- 顶部统计卡片 -->
    <a-row :gutter="16" class="mb-4">
      <a-col :span="6">
        <a-card>
          <a-statistic title="总成交量" :value="formatVolume(stats.total_volume)" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic title="总成交额" :value="formatAmount(stats.total_amount)" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic title="成交笔数" :value="stats.trade_count" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic title="平均成交价" :value="stats.avg_price ?? '--'" />
        </a-card>
      </a-col>
    </a-row>

    <!-- 筛选栏 -->
    <a-card class="mb-4">
      <a-space wrap>
        <a-select
          v-model:value="filters.source_type"
          placeholder="行情源类型"
          allow-clear
          style="width: 140px"
          @change="handleSearch"
        >
          <a-select-option
            v-for="opt in SOURCE_TYPES"
            :key="opt.value"
            :value="opt.value"
          >
            {{ opt.label }}
          </a-select-option>
        </a-select>
        <a-select
          v-model:value="filters.bond_type"
          placeholder="债券类型"
          allow-clear
          style="width: 120px"
          @change="handleSearch"
        >
          <a-select-option
            v-for="t in BOND_TYPES"
            :key="t"
            :value="t"
          >
            {{ t }}
          </a-select-option>
        </a-select>
        <a-button type="primary" @click="handleSearch">查询</a-button>
      </a-space>
    </a-card>

    <!-- 主表格 -->
    <a-card>
      <a-table
        :columns="columns"
        :data-source="trades"
        row-key="id"
        :loading="loading"
        :scroll="{ x: 'max-content' }"
        :pagination="pagination"
        @change="handleTableChange"
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
          <template v-else-if="column.key === 'bond_code'">
            <router-link :to="`/market/${record.bond_id}`" class="text-blue-600 hover:underline">
              {{ record.bond_code }}
            </router-link>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import api from '../api'
import {
  formatPrice,
  formatYield,
  formatVolume,
  formatAmount,
  formatDateTime,
  sourceTypeLabel,
} from '../utils/format'
import { SOURCE_TYPES, BOND_TYPES } from '../utils/constants'

interface Trade {
  id: string
  bond_id: string
  bond_code?: string
  bond_name?: string
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

interface TradeListRes {
  items: Trade[]
  total: number
  page: number
  page_size: number
}

interface TradeStats {
  total_volume: number
  total_amount: number
  trade_count: number
  avg_price?: number
}

const loading = ref(false)
const trades = ref<Trade[]>([])
const stats = reactive<TradeStats>({
  total_volume: 0,
  total_amount: 0,
  trade_count: 0,
  avg_price: undefined,
})

const filters = reactive({
  source_type: undefined as string | undefined,
  bond_type: undefined as string | undefined,
})

const pagination = reactive({
  current: 1,
  pageSize: 30,
  total: 0,
  showSizeChanger: true,
  showTotal: (total: number) => `共 ${total} 条`,
})

const columns = [
  { title: '债券代码', key: 'bond_code', width: 120 },
  { title: '简称', dataIndex: 'bond_name', key: 'bond_name', width: 140 },
  { title: '行情源', dataIndex: 'source_name', key: 'source_name', width: 100 },
  { title: '源类型', key: 'source_type', width: 120 },
  { title: '成交价', key: 'price', width: 90 },
  { title: '收益率', key: 'yield', width: 90 },
  { title: '面额', key: 'volume', width: 100 },
  { title: '金额', key: 'amount', width: 100 },
  { title: '方向', key: 'direction', width: 80 },
  { title: '对手方', dataIndex: 'counterparty', key: 'counterparty' },
  { title: '成交时间', key: 'trade_time', width: 160 },
]

async function fetchStats() {
  try {
    const res = await api.get<TradeStats>('/api/trades/statistics')
    stats.total_volume = res.data.total_volume
    stats.total_amount = res.data.total_amount
    stats.trade_count = res.data.trade_count
    stats.avg_price = res.data.avg_price
  } catch {
    // 静默失败
  }
}

async function fetchTrades() {
  loading.value = true
  try {
    const res = await api.get<TradeListRes>('/api/trades/recent', {
      params: {
        page: pagination.current,
        page_size: pagination.pageSize,
        source_type: filters.source_type || undefined,
        bond_type: filters.bond_type || undefined,
      },
    })
    trades.value = res.data.items
    pagination.total = res.data.total
  } catch {
    trades.value = []
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  pagination.current = 1
  fetchTrades()
}

function handleTableChange(pag: { current?: number; pageSize?: number }) {
  if (pag?.current != null) pagination.current = pag.current
  if (pag?.pageSize != null) {
    pagination.pageSize = pag.pageSize
    pagination.current = 1
  }
  fetchTrades()
}

onMounted(() => {
  fetchStats()
  fetchTrades()
})
</script>
