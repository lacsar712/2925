<template>
  <div class="watchlist-group-view p-4">
    <a-card class="mb-4 rounded-lg">
      <a-row :gutter="[16, 16]" align="middle">
      <a-col :flex="1">
        <div class="flex items-center gap-3 items-center">
          <h2 class="text-xl font-semibold text-gray-800 flex items-center gap-2">
            <FolderOutlined class="text-blue-500" />
            {{ groupName }}
          </h2>
          <a-tag color="blue">{{ currentGroup?.bonds?.length || 0 }} 只债券</a-tag>
        </div>
      </a-col>
      <a-col>
        <a-button @click="openRenameModal">
          <template #icon><EditOutlined /></template>
          重命名
        </a-button>
      </a-col>
      <a-col>
        <a-popconfirm
          title="确定删除该分组吗？"
          ok-text="删除"
          cancel-text="取消"
          ok-button-props="{ danger: true }"
          @confirm="handleDeleteGroup"
        >
          <a-button danger>
            <template #icon><DeleteOutlined /></template>
            删除分组
          </a-button>
        </a-popconfirm>
      </a-col>
    </a-row>
    </a-card>

    <a-card class="mb-4 rounded-lg">
      <a-row :gutter="[16, 16]" align="middle">
        <a-col :flex="1">
          <a-input-search
            v-model:value="searchKeyword"
            placeholder="输入债券代码或名称搜索添加"
            allow-clear
            enter-button="搜索"
            size="large"
            @search="handleSearch"
            @change="handleSearchInput"
          />
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
                :disabled="isInGroup(record.id)"
                @click="handleAddBond(record)"
              >
                {{ isInGroup(record.id) ? '已在组内' : '添加' }}
              </a-button>
            </template>
            <template v-else-if="column.key === 'bond_type'">
              <a-tag :color="bondTypeColor(record.bond_type)">
                {{ record.bond_type }}
              </a-tag>
            </template>
          </template>
        </a-table>
      </div>
    </a-card>

    <a-card class="rounded-lg">
      <a-spin :spinning="loading">
        <a-empty
          v-if="!loading && (!currentGroup || currentGroup.bonds.length === 0)"
          description="分组暂无债券，请搜索并添加债券"
          class="my-8"
        />
        <a-table
          v-else
          :data-source="currentGroup?.bonds || []"
          :columns="bondColumns"
          :pagination="false"
          :scroll="{ x: 'max-content' }"
          row-key="id"
          class="bond-table"
        >
          <template #bodyCell="{ column, record, index }">
            <template v-if="column.key === 'order'">
              <div class="flex items-center gap-1">
                <a-button
                  type="text"
                  size="small"
                  :disabled="index === 0"
                  @click="moveBond(index, -1)"
                >
                  <template #icon><UpOutlined /></template>
                </a-button>
                <a-button
                  type="text"
                  size="small"
                  :disabled="index === (currentGroup?.bonds.length - 1)"
                  @click="moveBond(index, 1)"
                >
                  <template #icon><DownOutlined /></template>
                </a-button>
              </div>
            </template>
            <template v-else-if="column.key === 'code'">
              <router-link
                :to="`/market/${record.id}"
                class="text-blue-600 hover:underline tabular-nums"
              >
                {{ record.code }}
              </router-link>
            </template>
            <template v-else-if="column.key === 'name'">
              <router-link
                :to="`/market/${record.id}"
                class="text-blue-600 hover:underline"
              >
                {{ record.name }}
              </router-link>
            </template>
            <template v-else-if="column.key === 'bond_type'">
              <a-tag :color="bondTypeColor(record.bond_type)">
                {{ record.bond_type }}
              </a-tag>
            </template>
            <template v-else-if="column.key === 'coupon_rate'">
              <span class="tabular-nums">{{ record.coupon_rate != null ? `${record.coupon_rate.toFixed(4) + '%' : '--' }}</span>
            </template>
            <template v-else-if="column.key === 'remaining_term'">
              <span class="tabular-nums">{{ record.remaining_term != null ? record.remaining_term.toFixed(2) : '--' }}</span>
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
            <template v-else-if="column.key === 'latest_trade_price'">
              <span class="tabular-nums">{{ record.latest_trade_price != null ? record.latest_trade_price.toFixed(4) : '--' }}</span>
            </template>
            <template v-else-if="column.key === 'latest_trade_yield'">
              <span class="tabular-nums">{{ record.latest_trade_yield != null ? record.latest_trade_yield.toFixed(4) + '%' : '--' }}</span>
            </template>
            <template v-else-if="column.key === 'volume_7d'">
              <span class="tabular-nums">{{ formatVolume(record.volume_7d) }}</span>
            </template>
            <template v-else-if="column.key === 'spread'">
              <span class="tabular-nums">{{ record.spread != null ? record.spread.toFixed(4) : '--' }}</span>
            </template>
            <template v-else-if="column.key === 'action'">
              <a-popconfirm
                title="确定从分组移除该债券？"
                ok-text="移除"
                cancel-text="取消"
                @confirm="handleRemoveBond(record.id)"
              >
                <a-button type="link" danger size="small">移除</a-button>
              </a-popconfirm>
            </template>
          </template>
        </a-table>
      </a-spin>
    </a-card>

    <a-modal
      v-model:open="renameModalOpen"
      title="重命名分组"
      ok-text="确定"
      cancel-text="取消"
      @ok="handleRenameConfirm"
      @cancel="renameModalOpen = false"
    >
      <a-input
        v-model:value="renameInput"
        placeholder="请输入分组名称"
        :maxlength="100"
        show-count
      />
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  FolderOutlined, EditOutlined, DeleteOutlined, UpOutlined, DownOutlined } from '@ant-design/icons-vue'
import api from '../api'
import { bondTypeColor, formatVolume } from '../utils/format'
import { useWatchlistStore } from '../stores/watchlist'
import { useWebSocketStore, type BondQuoteUpdate } from '../stores/websocket'
import { usePriceFlash } from '../composables/usePriceFlash'

interface SearchBond {
  id: string
  code: string
  name: string
  bond_type: string
  credit_rating?: string
}

const route = useRoute()
const router = useRouter()
const watchlistStore = useWatchlistStore()
const wsStore = useWebSocketStore()
const { compareAndFlash, getFlashClass, clearAll } = usePriceFlash()

const searchKeyword = ref('')
const searchResults = ref<SearchBond[]>([])
const renameModalOpen = ref(false)
const renameInput = ref('')

const groupId = computed(() => route.params.groupId as string)
const loading = computed(() => watchlistStore.currentGroupLoading)
const currentGroup = computed(() => watchlistStore.currentGroup)
const groupName = computed(() => currentGroup.value?.name || '分组')

const searchColumns = [
  { title: '代码', key: 'code', dataIndex: 'code', width: 120 },
  { title: '名称', key: 'name', dataIndex: 'name', width: 200 },
  { title: '品种', key: 'bond_type', dataIndex: 'bond_type', width: 100 },
  { title: '评级', key: 'credit_rating', dataIndex: 'credit_rating', width: 80 },
  { title: '操作', key: 'action', width: 100, fixed: 'right' },
]

const bondColumns = [
  { title: '排序', key: 'order', width: 80, fixed: 'left' },
  { title: '代码', key: 'code', dataIndex: 'code', width: 120 },
  { title: '简称', key: 'name', dataIndex: 'name', width: 180 },
  { title: '品种', key: 'bond_type', dataIndex: 'bond_type', width: 100 },
  { title: '票面利率', key: 'coupon_rate', dataIndex: 'coupon_rate', width: 100 },
  { title: '剩余期限', key: 'remaining_term', dataIndex: 'remaining_term', width: 100 },
  { title: '评级', dataIndex: 'credit_rating', key: 'credit_rating', width: 80 },
  { title: '最优买价', key: 'best_bid_price', width: 100 },
  { title: '最优卖价', key: 'best_ask_price', width: 100 },
  { title: '最优买收益率', key: 'best_bid_yield', width: 120 },
  { title: '最优卖收益率', key: 'best_ask_yield', width: 120 },
  { title: '最新成交价', key: 'latest_trade_price', width: 110 },
  { title: '最新成交收益率', key: 'latest_trade_yield', width: 130 },
  { title: '近7日成交量', key: 'volume_7d', width: 120 },
  { title: '买卖价差', key: 'spread', width: 100 },
  { title: '操作', key: 'action', width: 100, fixed: 'right' },
]

function isInGroup(bondId: string): boolean {
  if (!currentGroup.value) return false
  return currentGroup.value.bonds.some(b => b.id === bondId)
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
  try {
    const res = await api.get<{ items: SearchBond[] }>('/api/bonds', {
      params: {
        keyword: searchKeyword.value,
        page_size: 10,
      },
    })
    searchResults.value = res.data.items ?? []
  } catch {
    searchResults.value = []
  }
}

async function handleAddBond(bond: SearchBond) {
  if (!groupId.value) return
  try {
    await watchlistStore.addBondToGroup(groupId.value, bond.id)
    message.success(`已添加「${bond.name}」到分组`)
    searchResults.value = searchResults.value.filter(b => b.id !== bond.id)
  } catch {
  }
}

async function handleRemoveBond(bondId: string) {
  if (!groupId.value) return
  try {
    await watchlistStore.removeBondFromGroup(groupId.value, bondId)
    message.success('已从分组移除')
  } catch {
  }
}

async function moveBond(index: number, direction: number) {
  if (!currentGroup.value || !groupId.value) return
  const bonds = [...currentGroup.value.bonds]
  const newIndex = index + direction
  if (newIndex < 0 || newIndex >= bonds.length) return
  ;[bonds[index], bonds[newIndex]] = [bonds[newIndex], bonds[index]]
  const bondIds = bonds.map(b => b.id)
  try {
    await watchlistStore.reorderBonds(groupId.value, bondIds)
  } catch {
  }
}

function openRenameModal() {
  renameInput.value = currentGroup.value?.name || ''
  renameModalOpen.value = true
}

async function handleRenameConfirm() {
  if (!renameInput.value.trim() || !groupId.value) return
  try {
    await watchlistStore.updateGroup(groupId.value, renameInput.value.trim())
    message.success('分组已重命名')
    renameModalOpen.value = false
  } catch {
  }
}

async function handleDeleteGroup() {
  if (!groupId.value) return
  try {
    await watchlistStore.deleteGroup(groupId.value)
    message.success('分组已删除')
    router.push('/favorites')
  } catch {
  }
}

const prevPrices = new Map<string, { best_bid?: number; best_ask?: number; best_bid_yield?: number; best_ask_yield?: number }>()

function handleQuoteUpdate(update: BondQuoteUpdate) {
  if (!currentGroup.value) return

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

  const bond = currentGroup.value.bonds.find(b => b.id === update.bond_id)
  if (bond) {
    ;(bond as any).best_bid_price = update.best_bid_price
    ;(bond as any).best_ask_price = update.best_ask_price
    ;(bond as any).best_bid_yield = update.best_bid_yield
    ;(bond as any).best_ask_yield = update.best_ask_yield
    ;(bond as any).spread = update.spread
  }
}

function subscribeGroupBonds() {
  if (!currentGroup.value || currentGroup.value.bonds.length === 0) return
  const bondIds = currentGroup.value.bonds.map(b => b.id)
  wsStore.subscribeBonds(bondIds, handleQuoteUpdate)
}

function unsubscribeGroupBonds() {
  if (!currentGroup.value || currentGroup.value.bonds.length === 0) return
  const bondIds = currentGroup.value.bonds.map(b => b.id)
  wsStore.unsubscribeBonds(bondIds, handleQuoteUpdate)
}

watch(
  () => currentGroup.value?.bonds?.length,
  () => {
    unsubscribeGroupBonds()
    subscribeGroupBonds()
  }
)

onMounted(() => {
  if (groupId.value) {
    watchlistStore.fetchGroupDetail(groupId.value).then(() => {
      subscribeGroupBonds()
    })
  }
  watchlistStore.fetchGroups()
})

onUnmounted(() => {
  unsubscribeGroupBonds()
  watchlistStore.clearCurrentGroup()
  clearAll()
  prevPrices.clear()
})
</script>

<style scoped>
.search-results {
  border-top: 1px solid #f0f0f0;
  padding-top: 16px;
}

.bond-table :deep(.ant-table-tbody > tr:hover > td) {
  background-color: rgb(239 246 255) !important;
}
</style>
