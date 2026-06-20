<template>
  <div class="swaps-view p-4">
    <!-- 筛选栏 -->
    <a-card class="mb-4 rounded-lg">
      <a-input-search
        v-model:value="dealerKeyword"
        placeholder="搜索交易商"
        allow-clear
        enter-button="搜索"
        size="large"
        class="max-w-md"
        @search="fetchSwaps"
      />
    </a-card>

    <!-- 报价列表 -->
    <a-card class="rounded-lg">
      <a-table
        :data-source="swaps"
        :columns="columns"
        :loading="loading"
        :pagination="false"
        :scroll="{ x: 'max-content' }"
        :row-key="(r) => r.id || `${r.bond_code}-${r.dealer}-${r.quote_time}`"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'bond_code'">
            <span class="tabular-nums">{{ record.bond_code }}</span>
          </template>
          <template v-else-if="column.key === 'swap_rate'">
            <span class="tabular-nums">{{ formatPrice(record.swap_rate) }}</span>
          </template>
          <template v-else-if="column.key === 'direction'">
            <a-tag :color="record.direction === 'pay_fixed' ? 'blue' : 'green'">
              {{ record.direction === 'pay_fixed' ? '支付固定' : '收取固定' }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'min_notional'">
            <span class="tabular-nums">{{ formatAmount(record.min_notional) }}</span>
          </template>
          <template v-else-if="column.key === 'quote_time'">
            <span class="tabular-nums">{{ formatDateTime(record.quote_time) }}</span>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '../api'
import { formatPrice, formatAmount, formatDateTime } from '../utils/format'

interface SwapQuote {
  id?: string
  bond_code: string
  bond_name?: string
  dealer: string
  swap_rate?: number
  term?: string
  direction: 'pay_fixed' | 'receive_fixed'
  min_notional?: number
  quote_time?: string
}

const dealerKeyword = ref('')
const loading = ref(false)
const swaps = ref<SwapQuote[]>([])

const columns = [
  { title: '标的债券代码', key: 'bond_code', dataIndex: 'bond_code', width: 120 },
  { title: '债券简称', dataIndex: 'bond_name', key: 'bond_name', width: 140 },
  { title: '交易商', dataIndex: 'dealer', key: 'dealer', width: 120 },
  { title: '互换利率', key: 'swap_rate', dataIndex: 'swap_rate', width: 100 },
  { title: '期限', dataIndex: 'term', key: 'term', width: 80 },
  { title: '方向', key: 'direction', dataIndex: 'direction', width: 120 },
  { title: '最小名义金额', key: 'min_notional', dataIndex: 'min_notional', width: 120 },
  { title: '报价时间', key: 'quote_time', dataIndex: 'quote_time', width: 100 },
]

async function fetchSwaps() {
  loading.value = true
  try {
    const res = await api.get<SwapQuote[] | { items: SwapQuote[] }>('/api/swaps', {
      params: { dealer: dealerKeyword.value || undefined },
    })
    const data = res.data
    swaps.value = Array.isArray(data) ? data : (data as { items: SwapQuote[] }).items ?? []
  } catch {
    swaps.value = []
  } finally {
    loading.value = false
  }
}

onMounted(fetchSwaps)
</script>
