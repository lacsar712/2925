<template>
  <a-card title="热门债券排行 Top 10" class="rounded-lg h-full">
    <a-table
      :data-source="bonds"
      :columns="columns"
      :pagination="false"
      :scroll="{ x: 'max-content' }"
      size="small"
      row-key="code"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'rank'">
          <span class="tabular-nums font-medium">{{ record.rank }}</span>
        </template>
        <template v-else-if="column.key === 'code'">
          <router-link
            :to="`/market/${record.bond_id ?? record.code}`"
            class="text-blue-600 hover:underline tabular-nums"
          >
            {{ record.code }}
          </router-link>
        </template>
        <template v-else-if="column.key === 'type'">
          <a-tag :color="bondTypeColor(record.bond_type)">
            {{ record.bond_type }}
          </a-tag>
        </template>
        <template v-else-if="column.key === 'volume'">
          <span class="tabular-nums">{{ formatVolume(record.total_volume) }}</span>
        </template>
        <template v-else-if="column.key === 'amount'">
          <span class="tabular-nums">{{ formatAmount(record.total_amount) }}</span>
        </template>
      </template>
    </a-table>
  </a-card>
</template>

<script setup lang="ts">
import { formatVolume, formatAmount, bondTypeColor } from '../../utils/format'

export interface HotBond {
  bond_id?: string
  code: string
  name: string
  bond_type: string
  total_volume?: number
  total_amount?: number
  trade_count?: number
  rank?: number
}

defineProps<{
  bonds: HotBond[]
}>()

const columns = [
  { title: '排名', key: 'rank', width: 60 },
  { title: '代码', key: 'code', width: 100 },
  { title: '简称', dataIndex: 'name', key: 'name' },
  { title: '类型', key: 'type', width: 80 },
  { title: '成交量', key: 'volume', width: 90 },
  { title: '成交额', key: 'amount', width: 90 },
]
</script>
