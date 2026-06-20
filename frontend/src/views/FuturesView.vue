<template>
  <div class="futures-view p-4">
    <!-- 顶部筛选 -->
    <a-card class="mb-4 rounded-lg">
      <a-radio-group v-model:value="contractType" button-style="solid" @change="fetchContracts">
        <a-radio-button value="">全部</a-radio-button>
        <a-radio-button value="T">T (10年)</a-radio-button>
        <a-radio-button value="TF">TF (5年)</a-radio-button>
        <a-radio-button value="TS">TS (2年)</a-radio-button>
      </a-radio-group>
    </a-card>

    <!-- 合约行情表格 -->
    <a-card class="mb-4 rounded-lg" title="合约行情">
      <a-table
        :data-source="contracts"
        :columns="contractColumns"
        :loading="loading"
        :pagination="false"
        :scroll="{ x: 'max-content' }"
        :row-key="(r: any) => r.contract_code"
        size="small"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'contract_code'">
            <span class="tabular-nums font-medium">{{ record.contract_code }}</span>
          </template>
          <template v-else-if="column.key === 'contract_type'">
            <a-tag :color="typeColor(record.contract_type)">{{ record.contract_type }}</a-tag>
          </template>
          <template v-else-if="column.key === 'latest_price'">
            <span class="tabular-nums font-semibold">{{ formatPrice(record.latest_price) }}</span>
          </template>
          <template v-else-if="column.key === 'settlement_price'">
            <span class="tabular-nums">{{ formatPrice(record.settlement_price) }}</span>
          </template>
          <template v-else-if="column.key === 'open_price'">
            <span class="tabular-nums">{{ formatPrice(record.open_price) }}</span>
          </template>
          <template v-else-if="column.key === 'high_price'">
            <span class="tabular-nums text-red-500">{{ formatPrice(record.high_price) }}</span>
          </template>
          <template v-else-if="column.key === 'low_price'">
            <span class="tabular-nums text-green-500">{{ formatPrice(record.low_price) }}</span>
          </template>
          <template v-else-if="column.key === 'change_pct'">
            <span
              :class="[
                'tabular-nums font-medium',
                record.change_pct != null && record.change_pct > 0 ? 'text-red-600' : '',
                record.change_pct != null && record.change_pct < 0 ? 'text-green-600' : '',
              ]"
            >
              <ArrowUpOutlined v-if="record.change_pct != null && record.change_pct > 0" class="mr-0.5" />
              <ArrowDownOutlined v-else-if="record.change_pct != null && record.change_pct < 0" class="mr-0.5" />
              {{ record.change_pct != null ? record.change_pct.toFixed(4) + '%' : '--' }}
            </span>
          </template>
          <template v-else-if="column.key === 'volume'">
            <span class="tabular-nums">{{ record.volume != null ? record.volume.toLocaleString() : '--' }}</span>
          </template>
          <template v-else-if="column.key === 'open_interest'">
            <span class="tabular-nums">{{ record.open_interest != null ? record.open_interest.toLocaleString() : '--' }}</span>
          </template>
          <template v-else-if="column.key === 'basis'">
            <span class="tabular-nums">{{ formatPrice(record.basis) }}</span>
          </template>
          <template v-else-if="column.key === 'quote_time'">
            <span class="tabular-nums text-gray-500">{{ formatTime(record.quote_time) }}</span>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 基差分析卡片 -->
    <a-card title="基差分析" class="rounded-lg">
      <a-table
        :data-source="basisData"
        :columns="basisColumns"
        :loading="basisLoading"
        :pagination="false"
        :scroll="{ x: 'max-content' }"
        :row-key="(r: any) => r.contract_code"
        size="small"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'contract_type'">
            <a-tag :color="typeColor(record.contract_type)">{{ record.contract_type }}</a-tag>
          </template>
          <template v-else-if="column.key === 'latest_price'">
            <span class="tabular-nums">{{ formatPrice(record.latest_price) }}</span>
          </template>
          <template v-else-if="column.key === 'basis'">
            <span class="tabular-nums font-medium">{{ formatPrice(record.basis) }}</span>
          </template>
          <template v-else-if="column.key === 'volume'">
            <span class="tabular-nums">{{ record.volume != null ? record.volume.toLocaleString() : '--' }}</span>
          </template>
          <template v-else-if="column.key === 'open_interest'">
            <span class="tabular-nums">{{ record.open_interest != null ? record.open_interest.toLocaleString() : '--' }}</span>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons-vue'
import api from '../api'
import { formatPrice, formatTime } from '../utils/format'

interface FuturesContract {
  id: string
  contract_code: string
  contract_type: string
  latest_price: number
  settlement_price?: number
  open_price?: number
  high_price?: number
  low_price?: number
  prev_close?: number
  change_pct?: number
  volume?: number
  open_interest?: number
  basis?: number
  quote_time?: string
}

interface BasisItem {
  contract_code: string
  contract_type: string
  latest_price: number
  basis?: number
  volume?: number
  open_interest?: number
}

const contractType = ref('')
const loading = ref(false)
const basisLoading = ref(false)
const contracts = ref<FuturesContract[]>([])
const basisData = ref<BasisItem[]>([])

const contractColumns = [
  { title: '合约代码', key: 'contract_code', dataIndex: 'contract_code', width: 110 },
  { title: '类型', key: 'contract_type', dataIndex: 'contract_type', width: 80 },
  { title: '最新价', key: 'latest_price', dataIndex: 'latest_price', width: 100 },
  { title: '结算价', key: 'settlement_price', dataIndex: 'settlement_price', width: 100 },
  { title: '开盘价', key: 'open_price', dataIndex: 'open_price', width: 100 },
  { title: '最高价', key: 'high_price', dataIndex: 'high_price', width: 100 },
  { title: '最低价', key: 'low_price', dataIndex: 'low_price', width: 100 },
  { title: '涨跌幅', key: 'change_pct', dataIndex: 'change_pct', width: 110 },
  { title: '成交量(手)', key: 'volume', dataIndex: 'volume', width: 110 },
  { title: '持仓量', key: 'open_interest', dataIndex: 'open_interest', width: 100 },
  { title: '基差', key: 'basis', dataIndex: 'basis', width: 90 },
  { title: '行情时间', key: 'quote_time', dataIndex: 'quote_time', width: 110 },
]

const basisColumns = [
  { title: '合约代码', dataIndex: 'contract_code', key: 'contract_code', width: 110 },
  { title: '类型', key: 'contract_type', dataIndex: 'contract_type', width: 80 },
  { title: '最新价', key: 'latest_price', dataIndex: 'latest_price', width: 100 },
  { title: '基差', key: 'basis', dataIndex: 'basis', width: 100 },
  { title: '成交量(手)', key: 'volume', dataIndex: 'volume', width: 110 },
  { title: '持仓量', key: 'open_interest', dataIndex: 'open_interest', width: 100 },
]

function typeColor(t: string): string {
  if (t === 'T') return 'red'
  if (t === 'TF') return 'blue'
  if (t === 'TS') return 'green'
  return 'default'
}

async function fetchContracts() {
  loading.value = true
  try {
    const params: Record<string, string> = {}
    if (contractType.value) {
      params.contract_type = contractType.value
    }
    const res = await api.get('/api/futures/contracts', { params })
    contracts.value = Array.isArray(res.data) ? res.data : []
  } catch {
    contracts.value = []
  } finally {
    loading.value = false
  }
}

async function fetchBasis() {
  basisLoading.value = true
  try {
    const res = await api.get('/api/futures/basis')
    basisData.value = Array.isArray(res.data) ? res.data : []
  } catch {
    basisData.value = []
  } finally {
    basisLoading.value = false
  }
}

onMounted(() => {
  fetchContracts()
  fetchBasis()
})
</script>
