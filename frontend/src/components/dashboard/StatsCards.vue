<template>
  <a-card class="rounded-lg stats-card" :bordered="false" :body-style="{ padding: 0 }">
    <a-row :gutter="[16, 16]" style="padding: 16px 16px 0 16px; margin-bottom: -16px;">
      <a-col :xs="12" :sm="8" :md="6" :lg="4" class="mb-4">
        <div class="rounded-lg bg-blue-50/80 p-4 h-full">
          <a-statistic
            title="债券总数"
            :value="overview?.bond_count ?? 0"
            class="tabular-nums"
          >
            <template #prefix>
              <FileOutlined class="text-blue-500" />
            </template>
          </a-statistic>
        </div>
      </a-col>
      <a-col :xs="12" :sm="8" :md="6" :lg="4" class="mb-4">
        <div class="rounded-lg bg-green-50/80 p-4 h-full">
          <a-statistic
            title="在线行情源"
            :value="overview?.online_source_count ?? 0"
            class="tabular-nums"
          >
            <template #prefix>
              <ApiOutlined class="text-green-500" />
            </template>
          </a-statistic>
        </div>
      </a-col>
      <a-col :xs="12" :sm="8" :md="6" :lg="4" class="mb-4">
        <div class="rounded-lg bg-amber-50/80 p-4 h-full">
          <a-statistic
            title="报价总数"
            :value="overview?.total_quotes ?? 0"
            class="tabular-nums"
          >
            <template #prefix>
              <BarChartOutlined class="text-amber-500" />
            </template>
          </a-statistic>
        </div>
      </a-col>
      <a-col :xs="12" :sm="8" :md="6" :lg="4" class="mb-4">
        <div class="rounded-lg bg-purple-50/80 p-4 h-full">
          <a-statistic
            title="成交笔数"
            :value="overview?.total_trades ?? 0"
            class="tabular-nums"
          >
            <template #prefix>
              <TransactionOutlined class="text-purple-500" />
            </template>
          </a-statistic>
        </div>
      </a-col>
      <a-col :xs="12" :sm="8" :md="6" :lg="4" class="mb-4">
        <div class="rounded-lg bg-cyan-50/80 p-4 h-full">
          <a-statistic
            title="成交量(亿)"
            :value="formatVolume(overview?.total_volume)"
            class="tabular-nums"
          >
            <template #prefix>
              <RiseOutlined class="text-cyan-500" />
            </template>
          </a-statistic>
        </div>
      </a-col>
      <a-col :xs="12" :sm="8" :md="6" :lg="4" class="mb-4">
        <div class="rounded-lg bg-orange-50/80 p-4 h-full">
          <a-statistic
            title="成交额(亿)"
            :value="formatAmount(overview?.total_amount)"
            class="tabular-nums"
          >
            <template #prefix>
              <DollarOutlined class="text-orange-500" />
            </template>
          </a-statistic>
        </div>
      </a-col>
    </a-row>
  </a-card>
</template>

<script setup lang="ts">
import {
  FileOutlined,
  ApiOutlined,
  BarChartOutlined,
  TransactionOutlined,
  RiseOutlined,
  DollarOutlined,
} from '@ant-design/icons-vue'
import { formatVolume, formatAmount } from '../../utils/format'

export interface StatsOverview {
  bond_count?: number
  online_source_count?: number
  total_quotes?: number
  total_trades?: number
  total_volume?: number
  total_amount?: number
}

defineProps<{
  overview: StatsOverview | null
}>()
</script>

<style scoped>
.stats-card {
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.03), 0 1px 6px -1px rgba(0, 0, 0, 0.02), 0 2px 4px 0 rgba(0, 0, 0, 0.02);
}
</style>
