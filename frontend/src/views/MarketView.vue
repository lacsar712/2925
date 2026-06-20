<template>
  <div class="market-view p-4">
    <!-- 顶部筛选栏 -->
    <a-card class="mb-4 rounded-lg">
      <a-row :gutter="[16, 16]" align="middle">
        <a-col :flex="1">
          <a-input-search
            v-model:value="filters.keyword"
            placeholder="关键词搜索债券代码或简称"
            allow-clear
            enter-button="搜索"
            size="large"
            @search="handleSearch"
          />
        </a-col>
        <a-col>
          <a-select
            v-model:value="filters.bond_type"
            placeholder="债券类型"
            allow-clear
            style="width: 140px"
            :options="bondTypeOptions"
          />
        </a-col>
        <a-col>
          <a-select
            v-model:value="filters.credit_rating"
            placeholder="信用评级"
            allow-clear
            style="width: 120px"
            :options="creditRatingOptions"
          />
        </a-col>
        <a-col>
          <a-button type="primary" @click="handleSearch">
            搜索
          </a-button>
        </a-col>
      </a-row>
    </a-card>

    <!-- 债券列表表格 -->
    <a-card class="rounded-lg">
      <a-table
        :data-source="bondsWithQuotes"
        :columns="columns"
        :loading="loading"
        :pagination="false"
        :scroll="{ x: 'max-content' }"
        row-key="id"
        class="bond-table"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'code'">
            <router-link
              :to="`/market/${record.id}`"
              class="text-blue-600 hover:underline tabular-nums"
            >
              {{ record.code }}
            </router-link>
          </template>
          <template v-else-if="column.key === 'name'">
            <router-link
              :to="`/market/${record.id}`"
              class="text-blue-600 hover:underline"
            >
              {{ record.name }}
            </router-link>
          </template>
          <template v-else-if="column.key === 'type'">
            <a-tag :color="bondTypeColor(record.type)">
              {{ record.type }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'coupon_rate'">
            <span class="tabular-nums">{{ record.coupon_rate != null ? `${record.coupon_rate}%` : '--' }}</span>
          </template>
          <template v-else-if="column.key === 'remaining_term'">
            <span class="tabular-nums">{{ record.remaining_term ?? '--' }}</span>
          </template>
          <template v-else-if="column.key === 'best_bid_price'">
            <span
              class="tabular-nums"
              :class="[
                record.best_bid_price != null ? 'text-green-600 font-medium' : '',
                getFlashClass(`${record.id}-best_bid`),
              ]"
            >
              {{ record.best_bid_price != null ? record.best_bid_price.toFixed(4) : '--' }}
            </span>
          </template>
          <template v-else-if="column.key === 'best_ask_price'">
            <span
              class="tabular-nums"
              :class="[
                record.best_ask_price != null ? 'text-red-600 font-medium' : '',
                getFlashClass(`${record.id}-best_ask`),
              ]"
            >
              {{ record.best_ask_price != null ? record.best_ask_price.toFixed(4) : '--' }}
            </span>
          </template>
          <template v-else-if="column.key === 'spread'">
            <span class="tabular-nums">{{ record.spread != null ? record.spread.toFixed(4) : '--' }}</span>
          </template>
          <template v-else-if="column.key === 'best_bid_yield'">
            <span
              class="tabular-nums"
              :class="[
                'text-green-600',
                getFlashClass(`${record.id}-best_bid_yield`),
              ]"
            >
              {{ record.best_bid_yield != null ? record.best_bid_yield.toFixed(4) + '%' : '--' }}
            </span>
          </template>
          <template v-else-if="column.key === 'best_ask_yield'">
            <span
              class="tabular-nums"
              :class="[
                'text-red-600',
                getFlashClass(`${record.id}-best_ask_yield`),
              ]"
            >
              {{ record.best_ask_yield != null ? record.best_ask_yield.toFixed(4) + '%' : '--' }}
            </span>
          </template>
          <template v-else-if="column.key === 'quote_count'">
            <span class="tabular-nums">{{ record.quote_count ?? '--' }}</span>
          </template>
        </template>
      </a-table>

      <div class="flex justify-end mt-4">
        <a-pagination
          v-model:current="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :show-size-changer="true"
          :page-size-options="['10', '20', '50', '100']"
          show-total
          :show-quick-jumper="true"
          @change="handlePageChange"
        />
      </div>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch, computed, onUnmounted } from 'vue'
import api from '../api'
import { bondTypeColor } from '../utils/format'
import { BOND_TYPES, CREDIT_RATINGS } from '../utils/constants'
import { useWebSocketStore, type BondQuoteUpdate } from '../stores/websocket'
import { usePriceFlash } from '../composables/usePriceFlash'

const wsStore = useWebSocketStore()
const { compareAndFlash, getFlashClass, clearAll } = usePriceFlash()

interface Bond {
  id: string
  code: string
  name: string
  type: string
  coupon_rate?: number
  remaining_term?: string
  rating?: string
  issuer?: string
  best_bid_price?: number
  best_ask_price?: number
  best_bid_yield?: number
  best_ask_yield?: number
  spread?: number
  quote_count?: number
}

interface BondsResponse {
  items: Bond[]
  total: number
  page?: number
  page_size?: number
}

const loading = ref(false)
const bonds = ref<Bond[]>([])
const quoteDataMap = ref<Map<string, BondQuoteUpdate>>(new Map())
const filters = reactive({
  keyword: '',
  bond_type: undefined as string | undefined,
  credit_rating: undefined as string | undefined,
})
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

const bondTypeOptions = BOND_TYPES.map((t) => ({ label: t, value: t }))
const creditRatingOptions = CREDIT_RATINGS.map((r) => ({ label: r, value: r }))

const columns = [
  { title: '代码', key: 'code', dataIndex: 'code', width: 120, fixed: 'left' },
  { title: '简称', key: 'name', dataIndex: 'name', width: 180 },
  { title: '品种', key: 'type', dataIndex: 'type', width: 100 },
  { title: '票面利率', key: 'coupon_rate', dataIndex: 'coupon_rate', width: 100 },
  { title: '剩余期限', key: 'remaining_term', dataIndex: 'remaining_term', width: 100 },
  { title: '评级', dataIndex: 'rating', key: 'rating', width: 80 },
  { title: '最优买价', key: 'best_bid_price', width: 110 },
  { title: '最优卖价', key: 'best_ask_price', width: 110 },
  { title: '价差', key: 'spread', width: 90 },
  { title: '最优买收益率', key: 'best_bid_yield', width: 130 },
  { title: '最优卖收益率', key: 'best_ask_yield', width: 130 },
  { title: '报价数', key: 'quote_count', width: 80 },
  { title: '发行人', dataIndex: 'issuer', key: 'issuer', ellipsis: true },
]

const bondsWithQuotes = computed(() => {
  return bonds.value.map((b) => {
    const quote = quoteDataMap.value.get(b.id)
    if (quote) {
      return {
        ...b,
        best_bid_price: quote.best_bid_price,
        best_ask_price: quote.best_ask_price,
        best_bid_yield: quote.best_bid_yield,
        best_ask_yield: quote.best_ask_yield,
        spread: quote.spread,
        quote_count: quote.total_quotes,
      }
    }
    return b
  })
})

const prevPrices = new Map<string, { best_bid?: number; best_ask?: number; best_bid_yield?: number; best_ask_yield?: number }>()

function handleQuoteUpdate(update: BondQuoteUpdate) {
  const prev = prevPrices.get(update.bond_id) || {}

  compareAndFlash(`${update.bond_id}-best_bid`, update.best_bid_price, prev.best_bid)
  compareAndFlash(`${update.bond_id}-best_ask`, update.best_ask_price, prev.best_ask)
  compareAndFlash(`${update.bond_id}-best_bid_yield`, update.best_bid_yield, prev.best_bid_yield)
  compareAndFlash(`${update.bond_id}-best_ask_yield`, update.best_ask_yield, prev.best_ask_yield)

  prevPrices.set(update.bond_id, {
    best_bid: update.best_bid_price,
    best_ask: update.best_ask_price,
    best_bid_yield: update.best_bid_yield,
    best_ask_yield: update.best_ask_yield,
  })

  quoteDataMap.value.set(update.bond_id, update)
}

async function fetchBonds() {
  loading.value = true
  try {
    const res = await api.get<BondsResponse>('/api/bonds', {
      params: {
        keyword: filters.keyword || undefined,
        bond_type: filters.bond_type,
        credit_rating: filters.credit_rating,
        page: pagination.page,
        page_size: pagination.pageSize,
      },
    })
    const data = res.data
    bonds.value = data.items ?? data as unknown as Bond[] ?? []
    pagination.total = data.total ?? bonds.value.length

    const bondIds = bonds.value.map((b) => b.id)
    if (bondIds.length > 0) {
      try {
        const compareRes = await api.get<{ items: any[] }>('/api/bonds/compare/batch', {
          params: { bond_ids: bondIds.join(',') },
        })
        const compareItems = compareRes.data.items || []
        compareItems.forEach((item) => {
          quoteDataMap.value.set(item.id, {
            bond_id: item.id,
            code: item.code,
            name: item.name,
            sources: [],
            best_bid_price: item.best_bid_price,
            best_ask_price: item.best_ask_price,
            best_bid_yield: item.best_bid_yield,
            best_ask_yield: item.best_ask_yield,
            spread: item.spread,
            total_quotes: 0,
            timestamp: new Date().toISOString(),
          })
          prevPrices.set(item.id, {
            best_bid: item.best_bid_price,
            best_ask: item.best_ask_price,
            best_bid_yield: item.best_bid_yield,
            best_ask_yield: item.best_ask_yield,
          })
        })
      } catch {
        // ignore
      }
    }
  } catch {
    bonds.value = []
    pagination.total = 0
  } finally {
    loading.value = false
  }
}

function subscribeCurrentBonds() {
  const bondIds = bonds.value.map((b) => b.id)
  if (bondIds.length > 0) {
    wsStore.subscribeBonds(bondIds, handleQuoteUpdate)
  }
}

function unsubscribeCurrentBonds() {
  const bondIds = bonds.value.map((b) => b.id)
  if (bondIds.length > 0) {
    wsStore.unsubscribeBonds(bondIds, handleQuoteUpdate)
  }
}

let searchTimer: ReturnType<typeof setTimeout> | null = null
function handleSearch() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    unsubscribeCurrentBonds()
    pagination.page = 1
    fetchBonds().then(() => {
      subscribeCurrentBonds()
    })
    searchTimer = null
  }, 300)
}

function handlePageChange(page: number, pageSize: number) {
  unsubscribeCurrentBonds()
  pagination.page = page
  pagination.pageSize = pageSize
  fetchBonds().then(() => {
    subscribeCurrentBonds()
  })
}

watch(
  () => [filters.keyword, filters.bond_type, filters.credit_rating],
  () => {
    pagination.page = 1
  }
)

onMounted(() => {
  fetchBonds().then(() => {
    subscribeCurrentBonds()
  })
})

onUnmounted(() => {
  unsubscribeCurrentBonds()
  clearAll()
  prevPrices.clear()
  quoteDataMap.value.clear()
})
</script>

<style scoped>
.bond-table :deep(.ant-table-tbody > tr:hover > td) {
  background-color: rgb(239 246 255) !important;
}
</style>
