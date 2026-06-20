<template>
  <div class="bond-compare-view p-4">
    <a-card class="mb-4 rounded-lg">
      <a-row :gutter="[16, 16]" align="middle">
        <a-col :flex="1">
          <a-input-search
            v-model:value="searchKeyword"
            placeholder="输入债券代码或名称搜索"
            allow-clear
            enter-button="搜索"
            size="large"
            @search="handleSearch"
            @change="handleSearchInput"
          />
        </a-col>
        <a-col>
          <a-button type="primary" size="large" @click="handleShare" :disabled="compareList.length === 0">
            <template #icon><ShareAltOutlined /></template>
            分享对比
          </a-button>
        </a-col>
        <a-col>
          <a-button danger size="large" @click="handleClearAll" :disabled="compareList.length === 0">
            <template #icon><DeleteOutlined /></template>
            一键清空
          </a-button>
        </a-col>
      </a-row>

      <div v-if="searchResults.length > 0" class="mt-4 search-results">
        <a-table
          :data-source="searchResults"
          :columns="searchColumns"
          :pagination="false"
          size="small"
          row-key="id"
          :scroll="{ x: 'max-content' }"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'action'">
              <a-button
                type="primary"
                size="small"
                :disabled="isInCompareList(record.id) || compareList.length >= 4"
                @click="addToCompare(record)"
              >
                {{ isInCompareList(record.id) ? '已添加' : compareList.length >= 4 ? '已达上限' : '添加对比' }}
              </a-button>
            </template>
            <template v-else-if="column.key === 'type'">
              <a-tag :color="bondTypeColor(record.bond_type)">
                {{ record.bond_type }}
              </a-tag>
            </template>
          </template>
        </a-table>
      </div>

      <div v-if="compareList.length > 0" class="mt-4">
        <a-alert
          v-if="compareList.length < 4"
          type="info"
          show-icon
          :message="`已添加 ${compareList.length}/4 只债券，还可添加 ${4 - compareList.length} 只`"
          class="mb-4"
        />
        <a-alert
          v-else
          type="warning"
          show-icon
          message="已达最大对比数量（4只）"
          class="mb-4"
        />
      </div>
    </a-card>

    <a-card v-if="compareDataList.length > 0" class="rounded-lg">
      <div class="compare-table-wrapper overflow-x-auto">
        <table class="compare-table w-full border-collapse">
          <thead>
            <tr class="bg-gray-50">
              <th class="sticky left-0 z-10 bg-gray-50 border border-gray-200 px-4 py-3 text-left font-medium text-gray-700 min-w-[120px]">指标</th>
              <th
                v-for="item in compareDataList"
                :key="item.id"
                class="border border-gray-200 px-4 py-3 text-center min-w-[180px]"
              >
                <div class="flex items-center justify-between">
                  <div class="flex-1 text-center">
                    <div class="font-semibold text-gray-800">{{ item.code }}</div>
                    <div class="text-sm text-gray-500">{{ item.name }}</div>
                  </div>
                  <a-button
                    type="text"
                    danger
                    size="small"
                    class="ml-2"
                    @click="removeFromCompare(item.id)"
                  >
                    <template #icon><CloseOutlined /></template>
                  </a-button>
                </div>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in compareRows" :key="row.key" class="hover:bg-gray-50">
              <td class="sticky left-0 z-10 bg-white border border-gray-200 px-4 py-3 font-medium text-gray-700">
                {{ row.label }}
              </td>
              <td
                v-for="item in compareDataList"
                :key="`${item.id}-${row.key}`"
                class="border border-gray-200 px-4 py-3 text-center tabular-nums"
                :class="getValueClass(row.key, item)"
              >
                <span v-if="row.key === 'bond_type'">
                  <a-tag :color="bondTypeColor(item.bond_type)">{{ item.bond_type }}</a-tag>
                </span>
                <span v-else-if="row.key === 'credit_rating'">
                  {{ item.credit_rating || '--' }}
                </span>
                <span v-else-if="row.key === 'remaining_term'">
                  {{ formatTerm(item.remaining_term) }}
                </span>
                <span v-else-if="row.key === 'coupon_rate' || row.key === 'best_bid_yield' || row.key === 'best_ask_yield' || row.key === 'latest_trade_yield'">
                  {{ formatPercent(getValue(row.key, item)) }}
                </span>
                <span v-else-if="row.key === 'volume_7d'">
                  {{ formatVolume(item.volume_7d) }}
                </span>
                <span v-else>
                  {{ formatPrice(getValue(row.key, item)) }}
                </span>
                <span v-if="shouldShowIndicator(row.key, item)" class="ml-1">
                  <ArrowUpOutlined v-if="isBest(row.key, item, 'higher')" class="text-green-500" />
                  <ArrowDownOutlined v-else-if="isBest(row.key, item, 'lower')" class="text-red-500" />
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="mt-4 flex items-center text-sm text-gray-500">
        <span class="inline-flex items-center mr-4">
          <span class="w-3 h-3 bg-green-100 border border-green-300 rounded mr-1"></span>
          最优值（越高越好）
        </span>
        <span class="inline-flex items-center mr-4">
          <span class="w-3 h-3 bg-red-100 border border-red-300 rounded mr-1"></span>
          最优值（越低越好）
        </span>
        <span class="inline-flex items-center">
          <ArrowUpOutlined class="text-green-500 mr-1" /> 指标最优
          <ArrowDownOutlined class="text-red-500 ml-2 mr-1" /> 指标最优
        </span>
      </div>
    </a-card>

    <a-empty
      v-else
      description="请搜索并添加债券进行对比，最多可添加4只"
      class="mt-12"
    >
      <a-button type="primary" @click="focusSearch">立即添加</a-button>
    </a-empty>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import {
  ShareAltOutlined,
  DeleteOutlined,
  CloseOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
} from '@ant-design/icons-vue'
import api from '../api'
import { bondTypeColor } from '../utils/format'
import { formatPrice, formatYield, formatVolume } from '../utils/format'

interface Bond {
  id: string
  code: string
  name: string
  bond_type: string
  credit_rating?: string
  remaining_term?: number
  coupon_rate?: number
}

interface BondCompareData extends Bond {
  best_bid_price?: number
  best_ask_price?: number
  best_bid_yield?: number
  best_ask_yield?: number
  latest_trade_price?: number
  latest_trade_yield?: number
  volume_7d?: number
  spread?: number
}

interface CompareRow {
  key: string
  label: string
  type: 'higher' | 'lower' | 'neutral'
}

const route = useRoute()
const router = useRouter()

const searchKeyword = ref('')
const searchResults = ref<Bond[]>([])
const searchLoading = ref(false)
const compareList = ref<string[]>([])
const compareDataList = ref<BondCompareData[]>([])
const loading = ref(false)

const searchColumns = [
  { title: '代码', key: 'code', dataIndex: 'code', width: 120 },
  { title: '名称', key: 'name', dataIndex: 'name', width: 200 },
  { title: '品种', key: 'type', dataIndex: 'bond_type', width: 100 },
  { title: '评级', key: 'credit_rating', dataIndex: 'credit_rating', width: 80 },
  { title: '操作', key: 'action', width: 120, fixed: 'right' },
]

const compareRows: CompareRow[] = [
  { key: 'code', label: '代码', type: 'neutral' },
  { key: 'name', label: '名称', type: 'neutral' },
  { key: 'bond_type', label: '品种', type: 'neutral' },
  { key: 'credit_rating', label: '评级', type: 'higher' },
  { key: 'remaining_term', label: '剩余期限(年)', type: 'neutral' },
  { key: 'coupon_rate', label: '票面利率', type: 'higher' },
  { key: 'best_bid_price', label: '最优买价', type: 'higher' },
  { key: 'best_ask_price', label: '最优卖价', type: 'lower' },
  { key: 'best_bid_yield', label: '最优买收益率', type: 'higher' },
  { key: 'best_ask_yield', label: '最优卖收益率', type: 'lower' },
  { key: 'spread', label: '买卖价差', type: 'lower' },
  { key: 'latest_trade_price', label: '最新成交价', type: 'neutral' },
  { key: 'latest_trade_yield', label: '最新成交收益率', type: 'neutral' },
  { key: 'volume_7d', label: '近7日成交量', type: 'higher' },
]

function formatPercent(val: number | null | undefined): string {
  if (val == null) return '--'
  return val.toFixed(4) + '%'
}

function formatTerm(val: number | null | undefined): string {
  if (val == null) return '--'
  return val.toFixed(2)
}

function getValue(key: string, item: BondCompareData): number | string | undefined {
  return (item as any)[key]
}

function getBestValues(key: string, type: 'higher' | 'lower'): number[] {
  const values = compareDataList.value
    .map(item => (item as any)[key])
    .filter((v: any) => v != null && !isNaN(v))
  if (values.length === 0) return []
  if (type === 'higher') {
    const max = Math.max(...values)
    return values.filter((v: number) => v === max)
  } else {
    const min = Math.min(...values)
    return values.filter((v: number) => v === min)
  }
}

function isBest(key: string, item: BondCompareData, type: 'higher' | 'lower'): boolean {
  const row = compareRows.find(r => r.key === key)
  if (!row || row.type === 'neutral') return false
  const val = (item as any)[key]
  if (val == null || isNaN(val)) return false
  const bestVals = getBestValues(key, row.type)
  return bestVals.includes(val)
}

function shouldShowIndicator(key: string, item: BondCompareData): boolean {
  const row = compareRows.find(r => r.key === key)
  if (!row || row.type === 'neutral') return false
  const val = (item as any)[key]
  if (val == null || isNaN(val)) return false
  const bestVals = getBestValues(key, row.type)
  return bestVals.includes(val) && compareDataList.value.length > 1
}

function getValueClass(key: string, item: BondCompareData): string {
  if (compareDataList.value.length <= 1) return ''
  if (isBest(key, item, 'higher')) return 'bg-green-50 text-green-700 font-medium'
  if (isBest(key, item, 'lower')) return 'bg-red-50 text-red-700 font-medium'
  return ''
}

function isInCompareList(id: string): boolean {
  return compareList.value.includes(id)
}

function addToCompare(bond: Bond) {
  if (compareList.value.length >= 4) {
    message.warning('最多只能对比4只债券')
    return
  }
  if (isInCompareList(bond.id)) {
    message.info('该债券已在对比列表中')
    return
  }
  compareList.value.push(bond.id)
  updateURL()
  fetchCompareData()
  message.success(`已添加「${bond.name}」到对比列表`)
}

function removeFromCompare(id: string) {
  const index = compareList.value.indexOf(id)
  if (index > -1) {
    const removed = compareDataList.value.find(d => d.id === id)
    compareList.value.splice(index, 1)
    updateURL()
    fetchCompareData()
    if (removed) {
      message.info(`已移除「${removed.name}」`)
    }
  }
}

function handleClearAll() {
  Modal.confirm({
    title: '确认清空',
    content: '确定要清空所有对比债券吗？',
    okText: '确定',
    cancelText: '取消',
    onOk: () => {
      compareList.value = []
      compareDataList.value = []
      updateURL()
      message.success('已清空对比列表')
    },
  })
}

function updateURL() {
  if (compareList.value.length > 0) {
    router.replace({
      path: '/compare',
      query: { bonds: compareList.value.join(',') },
    })
  } else {
    router.replace({ path: '/compare' })
  }
}

function handleShare() {
  if (compareList.value.length === 0) {
    message.warning('请先添加债券到对比列表')
    return
  }
  const url = `${window.location.origin}/compare?bonds=${compareList.value.join(',')}`
  navigator.clipboard.writeText(url).then(() => {
    message.success('对比链接已复制到剪贴板，可分享给同事')
  }).catch(() => {
    Modal.info({
      title: '分享链接',
      content: url,
      okText: '知道了',
    })
  })
}

let searchTimer: ReturnType<typeof setTimeout> | null = null

function handleSearchInput() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    handleSearch()
  }, 300)
}

async function handleSearch() {
  if (!searchKeyword.value.trim()) {
    searchResults.value = []
    return
  }
  searchLoading.value = true
  try {
    const res = await api.get<{ items: Bond[] }>('/api/bonds', {
      params: {
        keyword: searchKeyword.value,
        page_size: 10,
      },
    })
    searchResults.value = res.data.items ?? []
  } catch {
    searchResults.value = []
  } finally {
    searchLoading.value = false
  }
}

async function fetchCompareData() {
  if (compareList.value.length === 0) {
    compareDataList.value = []
    return
  }
  loading.value = true
  try {
    const res = await api.get<{ items: BondCompareData[] }>('/api/bonds/compare/batch', {
      params: { bond_ids: compareList.value.join(',') },
    })
    compareDataList.value = res.data.items ?? []
    const validIds = compareDataList.value.map(d => d.id)
    const invalidIds = compareList.value.filter(id => !validIds.includes(id))
    if (invalidIds.length > 0) {
      compareList.value = validIds
      updateURL()
      message.warning(`${invalidIds.length}只债券不存在，已自动移除`)
    }
  } catch {
    compareDataList.value = []
  } finally {
    loading.value = false
  }
}

function focusSearch() {
  nextTick(() => {
    const input = document.querySelector('.ant-input-search input') as HTMLInputElement
    input?.focus()
  })
}

onMounted(() => {
  const bondsParam = route.query.bonds as string
  if (bondsParam) {
    const ids = bondsParam.split(',').filter(id => id.trim())
    if (ids.length > 0) {
      compareList.value = ids.slice(0, 4)
      fetchCompareData()
    }
  }
})

watch(
  () => route.query.bonds,
  (newBonds) => {
    const bondsParam = newBonds as string
    if (bondsParam) {
      const ids = bondsParam.split(',').filter(id => id.trim())
      if (ids.length > 0) {
        const newIds = ids.slice(0, 4)
        if (newIds.join(',') !== compareList.value.join(',')) {
          compareList.value = newIds
          fetchCompareData()
        }
      }
    }
  }
)
</script>

<style scoped>
.compare-table-wrapper {
  overflow-x: auto;
}

.compare-table {
  border-collapse: collapse;
  min-width: 100%;
}

.compare-table th {
  background-color: #f9fafb;
  font-weight: 600;
  white-space: nowrap;
}

.compare-table th:first-child,
.compare-table td:first-child {
  position: sticky;
  left: 0;
  z-index: 10;
}

.compare-table td {
  transition: background-color 0.2s;
}

.compare-table tbody tr:hover td {
  background-color: #eff6ff;
}

.compare-table tbody tr:hover td:first-child {
  background-color: #eff6ff;
}

.search-results {
  border-top: 1px solid #f0f0f0;
  padding-top: 16px;
}
</style>
