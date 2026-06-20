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
        :data-source="bonds"
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
import { ref, reactive, onMounted, watch } from 'vue'
import api from '../api'
import { bondTypeColor } from '../utils/format'
import { BOND_TYPES, CREDIT_RATINGS } from '../utils/constants'

interface Bond {
  id: string
  code: string
  name: string
  type: string
  coupon_rate?: number
  remaining_term?: string
  rating?: string
  issuer?: string
}

interface BondsResponse {
  items: Bond[]
  total: number
  page?: number
  page_size?: number
}

const loading = ref(false)
const bonds = ref<Bond[]>([])
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
  { title: '发行人', dataIndex: 'issuer', key: 'issuer', ellipsis: true },
]

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
  } catch {
    bonds.value = []
    pagination.total = 0
  } finally {
    loading.value = false
  }
}

let searchTimer: ReturnType<typeof setTimeout> | null = null
function handleSearch() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    pagination.page = 1
    fetchBonds()
    searchTimer = null
  }, 300)
}

function handlePageChange(page: number, pageSize: number) {
  pagination.page = page
  pagination.pageSize = pageSize
  fetchBonds()
}

watch(
  () => [filters.keyword, filters.bond_type, filters.credit_rating],
  () => {
    pagination.page = 1
  }
)

onMounted(fetchBonds)
</script>

<style scoped>
.bond-table :deep(.ant-table-tbody > tr:hover > td) {
  background-color: rgb(239 246 255) !important;
}
</style>
