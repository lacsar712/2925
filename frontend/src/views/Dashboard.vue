<template>
  <div class="dashboard p-4">
    <a-spin :spinning="loading" tip="加载中...">
      <!-- 顶部统计卡片 -->
      <a-row :gutter="[16, 16]" class="mb-6">
        <a-col :xs="12" :sm="8" :md="6" :lg="4">
          <a-card class="rounded-lg bg-blue-50/80">
            <a-statistic
              title="债券总数"
              :value="overview?.bond_count ?? 0"
              class="tabular-nums"
            >
              <template #prefix>
                <FileOutlined class="text-blue-500" />
              </template>
            </a-statistic>
          </a-card>
        </a-col>
        <a-col :xs="12" :sm="8" :md="6" :lg="4">
          <a-card class="rounded-lg bg-green-50/80">
            <a-statistic
              title="在线行情源"
              :value="overview?.online_source_count ?? 0"
              class="tabular-nums"
            >
              <template #prefix>
                <ApiOutlined class="text-green-500" />
              </template>
            </a-statistic>
          </a-card>
        </a-col>
        <a-col :xs="12" :sm="8" :md="6" :lg="4">
          <a-card class="rounded-lg bg-amber-50/80">
            <a-statistic
              title="报价总数"
              :value="overview?.total_quotes ?? 0"
              class="tabular-nums"
            >
              <template #prefix>
                <BarChartOutlined class="text-amber-500" />
              </template>
            </a-statistic>
          </a-card>
        </a-col>
        <a-col :xs="12" :sm="8" :md="6" :lg="4">
          <a-card class="rounded-lg bg-purple-50/80">
            <a-statistic
              title="成交笔数"
              :value="overview?.total_trades ?? 0"
              class="tabular-nums"
            >
              <template #prefix>
                <TransactionOutlined class="text-purple-500" />
              </template>
            </a-statistic>
          </a-card>
        </a-col>
        <a-col :xs="12" :sm="8" :md="6" :lg="4">
          <a-card class="rounded-lg bg-cyan-50/80">
            <a-statistic
              title="成交量(亿)"
              :value="formatVolume(overview?.total_volume)"
              class="tabular-nums"
            >
              <template #prefix>
                <RiseOutlined class="text-cyan-500" />
              </template>
            </a-statistic>
          </a-card>
        </a-col>
        <a-col :xs="12" :sm="8" :md="6" :lg="4">
          <a-card class="rounded-lg bg-orange-50/80">
            <a-statistic
              title="成交额(亿)"
              :value="formatAmount(overview?.total_amount)"
              class="tabular-nums"
            >
              <template #prefix>
                <DollarOutlined class="text-orange-500" />
              </template>
            </a-statistic>
          </a-card>
        </a-col>
      </a-row>

      <!-- 中部：收益率曲线 + 热门债券 -->
      <a-row :gutter="[16, 16]" class="mb-6">
        <a-col :xs="24" :lg="16">
          <a-card title="国债收益率曲线" class="rounded-lg">
            <v-chart
              v-if="yieldCurveOption"
              :option="yieldCurveOption"
              class="h-[320px]"
              autoresize
            />
            <a-empty v-else description="暂无数据" />
          </a-card>
        </a-col>
        <a-col :xs="24" :lg="8">
          <a-card title="热门债券排行 Top 10" class="rounded-lg">
            <a-table
              :data-source="hotBonds"
              :columns="hotBondsColumns"
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
        </a-col>
      </a-row>

      <!-- 底部：行情异动提醒 -->
      <a-card title="行情异动提醒" class="rounded-lg">
        <a-list
          :data-source="alerts"
          :loading="loading"
        >
          <template #renderItem="{ item }">
            <a-list-item>
              <a-list-item-meta>
                <template #title>
                  <span class="font-medium">{{ item.name }} ({{ item.code }})</span>
                  <a-tag
                    :color="item.level === 'danger' ? 'red' : item.level === 'warning' ? 'orange' : 'blue'"
                    class="ml-2"
                  >
                    {{ item.type === 'price_spread' ? '价差异动' : '收益率异动' }}
                  </a-tag>
                </template>
                <template #description>
                  {{ item.message }}
                </template>
              </a-list-item-meta>
            </a-list-item>
          </template>
          <template #emptyText>
            <a-empty description="暂无异动提醒" />
          </template>
        </a-list>
      </a-card>
    </a-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  FileOutlined,
  ApiOutlined,
  BarChartOutlined,
  TransactionOutlined,
  RiseOutlined,
  DollarOutlined,
} from '@ant-design/icons-vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, TitleComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import api from '../api'
import { formatVolume, formatAmount, bondTypeColor } from '../utils/format'

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, TitleComponent])

interface Overview {
  bond_count?: number
  online_source_count?: number
  total_quotes?: number
  total_trades?: number
  total_volume?: number
  total_amount?: number
}

interface YieldPoint {
  term: number
  yield: number
}

interface HotBond {
  bond_id?: string
  code: string
  name: string
  bond_type: string
  total_volume?: number
  total_amount?: number
  trade_count?: number
  rank?: number
}

interface Alert {
  bond_id?: string
  code?: string
  name?: string
  type?: string
  message: string
  level: 'info' | 'warning' | 'danger'
}

const loading = ref(true)
const overview = ref<Overview | null>(null)
const yieldCurve = ref<YieldPoint[]>([])
const hotBonds = ref<HotBond[]>([])
const alerts = ref<Alert[]>([])

const hotBondsColumns = [
  { title: '排名', key: 'rank', width: 60 },
  { title: '代码', key: 'code', width: 100 },
  { title: '简称', dataIndex: 'name', key: 'name' },
  { title: '类型', key: 'type', width: 80 },
  { title: '成交量', key: 'volume', width: 90 },
  { title: '成交额', key: 'amount', width: 90 },
]

const yieldCurveOption = computed(() => {
  const data = yieldCurve.value
  if (!data || data.length === 0) return null
  const terms = data.map(p => p.term + '年')
  const yields = data.map(p => p.yield)
  return {
    tooltip: {
      trigger: 'axis',
    },
    xAxis: {
      type: 'category' as const,
      data: terms,
      axisLabel: { rotate: 30 },
    },
    yAxis: {
      type: 'value' as const,
      name: '收益率%',
      axisLabel: { formatter: '{value}%' },
    },
    series: [
      {
        type: 'line' as const,
        data: yields,
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { color: '#1890ff', width: 2 },
        itemStyle: { color: '#1890ff' },
        areaStyle: { color: 'rgba(24,144,255,0.1)' },
      },
    ],
    grid: { left: '3%', right: '4%', bottom: '15%', top: '10%', containLabel: true },
  }
})

async function fetchData() {
  loading.value = true
  try {
    const [overviewRes, curveRes, hotRes, alertsRes] = await Promise.all([
      api.get('/api/dashboard/overview'),
      api.get('/api/dashboard/yield-curve'),
      api.get('/api/dashboard/hot-bonds'),
      api.get('/api/dashboard/alerts'),
    ])
    overview.value = overviewRes.data
    yieldCurve.value = Array.isArray(curveRes.data) ? curveRes.data : []
    hotBonds.value = (Array.isArray(hotRes.data) ? hotRes.data : []).map((b: HotBond, i: number) => ({ ...b, rank: i + 1 }))
    alerts.value = Array.isArray(alertsRes.data) ? alertsRes.data : []
  } catch {
    overview.value = null
    yieldCurve.value = []
    hotBonds.value = []
    alerts.value = []
  } finally {
    loading.value = false
  }
}

onMounted(fetchData)
</script>
