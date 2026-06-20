<template>
  <div class="spread-analysis-view">
    <a-card class="rounded-lg mb-6">
      <template #title>
        <div class="flex items-center gap-2">
          <DiffOutlined class="text-purple-500" />
          <span class="text-lg font-semibold">利差分析</span>
        </div>
      </template>

      <a-row :gutter="24">
        <a-col :xs="24" :lg="12">
          <a-form-item label="基准债券" required>
            <a-auto-complete
              v-model:value="benchmarkSearchText"
              :options="benchmarkOptions"
              placeholder="输入债券代码或名称搜索基准债"
              allow-clear
              :filter-option="false"
              @search="handleBenchmarkSearch"
              @select="handleBenchmarkSelect"
              @change="handleBenchmarkClear"
            >
              <template #option="{ value, label, bond }">
                <div class="flex items-center justify-between">
                  <span>{{ label }}</span>
                  <a-tag :color="bondTypeColor(bond.bond_type)" size="small">{{ bond.bond_type }}</a-tag>
                </div>
              </template>
            </a-auto-complete>
          </a-form-item>
        </a-col>

        <a-col :xs="24" :lg="12">
          <a-form-item label="目标债券 (最多5只)">
            <a-select
              v-model:value="targetBondIds"
              mode="multiple"
              :max-tag-count="5"
              placeholder="输入债券代码或名称搜索目标债"
              :filter-option="false"
              :dropdown-match-select-width="true"
              @search="handleTargetSearch"
              @deselect="handleTargetDeselect"
              style="width: 100%"
            >
              <a-select-option
                v-for="opt in targetOptions"
                :key="opt.value"
                :value="opt.value"
                :disabled="isTargetDisabled(opt.value)"
              >
                <div class="flex items-center justify-between">
                  <span>{{ opt.label }}</span>
                  <span class="flex items-center gap-2">
                    <a-tag :color="bondTypeColor(opt.bond.bond_type)" size="small">{{ opt.bond.bond_type }}</a-tag>
                    <span v-if="isTargetDisabled(opt.value)" class="text-gray-400 text-xs">已添加</span>
                  </span>
                </div>
              </a-select-option>
            </a-select>
          </a-form-item>
        </a-col>

        <a-col :xs="24" :md="8">
          <a-form-item label="利差口径">
            <a-radio-group v-model:value="spreadType" button-style="solid" style="width: 100%">
              <a-radio-button value="yield" style="width: 50%">收益率利差</a-radio-button>
              <a-radio-button value="price" style="width: 50%">净价利差</a-radio-button>
            </a-radio-group>
          </a-form-item>
        </a-col>

        <a-col :xs="24" :md="8">
          <a-form-item label="时间范围">
            <a-range-picker
              v-model:value="dateRange"
              :disabled-date="disabledDate"
              style="width: 100%"
              @change="handleDateChange"
            />
          </a-form-item>
        </a-col>

        <a-col :xs="24" :md="8">
          <a-form-item label="操作">
            <a-space>
              <a-button type="primary" @click="handleAnalyze" :loading="loading" :disabled="!canAnalyze">
                <template #icon><LineChartOutlined /></template>
                开始分析
              </a-button>
              <a-button @click="handleReset">
                <template #icon><ReloadOutlined /></template>
                重置
              </a-button>
            </a-space>
          </a-form-item>
        </a-col>
      </a-row>

      <a-alert
        v-if="!benchmarkBond"
        type="info"
        show-icon
        message="请选择基准债券"
        class="mb-0"
      />
      <a-alert
        v-else-if="targetBondIds.length === 0"
        type="info"
        show-icon
        message="请至少添加一只目标债券"
        class="mb-0"
      />
    </a-card>

    <a-card v-if="analysisResult" class="rounded-lg mb-6">
      <template #title>
        <div class="flex items-center gap-2">
          <BarChartOutlined class="text-blue-500" />
          <span class="text-lg font-semibold">利差统计指标</span>
          <span class="text-sm text-gray-400 font-normal ml-2">
            (基准: {{ benchmarkBond?.code }} {{ benchmarkBond?.name }})
          </span>
        </div>
      </template>

      <a-row :gutter="[16, 16]">
        <a-col
          v-for="stats in analysisResult.targetStats"
          :key="stats.bond_id"
          :xs="24"
          :sm="12"
          :xl="6"
        >
          <div class="stats-card border rounded-lg p-4" :style="{ borderColor: stats.color + '40' }">
            <div class="flex items-center gap-2 mb-3">
              <div class="w-3 h-3 rounded-full" :style="{ backgroundColor: stats.color }"></div>
              <div class="min-w-0 flex-1">
                <div class="font-semibold text-gray-800 truncate">{{ stats.code }}</div>
                <div class="text-xs text-gray-500 truncate">{{ stats.name }}</div>
              </div>
            </div>
            <a-row :gutter="8">
              <a-col :span="12" class="mb-2">
                <div class="text-xs text-gray-500">当前利差</div>
                <div class="text-lg font-bold tabular-nums" :class="getSpreadClass(stats.current_spread)">
                  {{ formatSpread(stats.current_spread) }}
                </div>
              </a-col>
              <a-col :span="12" class="mb-2">
                <div class="text-xs text-gray-500">历史均值</div>
                <div class="text-lg font-semibold tabular-nums text-gray-700">
                  {{ formatSpread(stats.mean) }}
                </div>
              </a-col>
              <a-col :span="12">
                <div class="text-xs text-gray-500">标准差</div>
                <div class="text-base font-semibold tabular-nums text-gray-600">
                  {{ formatSpread(stats.std_dev) }}
                </div>
              </a-col>
              <a-col :span="12">
                <div class="text-xs text-gray-500">Z 分数</div>
                <div class="text-base font-semibold tabular-nums" :class="getZScoreClass(stats.z_score)">
                  {{ stats.z_score != null ? stats.z_score.toFixed(2) : '--' }}
                </div>
              </a-col>
            </a-row>
          </div>
        </a-col>
      </a-row>
    </a-card>

    <a-card v-if="analysisResult" class="rounded-lg mb-6">
      <template #title>
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <LineChartOutlined class="text-green-500" />
            <span class="text-lg font-semibold">利差走势</span>
            <a-tag class="ml-2">{{ spreadTypeLabel }}</a-tag>
          </div>
          <div class="flex items-center gap-2">
            <a-space size="small">
              <span class="text-xs text-gray-500">图例：</span>
              <span
                v-for="stats in analysisResult.targetStats"
                :key="stats.bond_id"
                class="inline-flex items-center gap-1 text-xs"
              >
                <span class="w-2 h-2 rounded-full" :style="{ backgroundColor: stats.color }"></span>
                {{ stats.code }}
              </span>
            </a-space>
          </div>
        </div>
      </template>

      <v-chart
        class="chart-container"
        :option="chartOption"
        :autoresize="true"
      />
    </a-card>

    <a-card v-if="analysisResult && analysisResult.dailyData.length > 0" class="rounded-lg">
      <template #title>
        <div class="flex items-center gap-2">
          <TableOutlined class="text-orange-500" />
          <span class="text-lg font-semibold">利查明细</span>
          <a-tag color="blue" class="ml-2">共 {{ analysisResult.dailyData.length }} 条记录</a-tag>
        </div>
      </template>

      <a-table
        :data-source="analysisResult.dailyData"
        :columns="detailColumns"
        :pagination="{ pageSize: 20, showSizeChanger: true, pageSizeOptions: ['10', '20', '50', '100'] }"
        :scroll="{ x: 'max-content' }"
        :row-key="record => record.date"
        size="middle"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'date'">
            {{ formatDate(record.date) }}
          </template>
          <template v-else-if="column.key.startsWith('spread_')">
            <span class="tabular-nums" :class="getSpreadClass(record[column.key])">
              {{ formatSpread(record[column.key]) }}
            </span>
          </template>
        </template>
      </a-table>
    </a-card>

    <a-empty
      v-else-if="!loading && !analysisResult"
      description="选择债券后点击「开始分析」查看利差走势"
      class="mt-12"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, h } from 'vue'
import { message } from 'ant-design-vue'
import dayjs from 'dayjs'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent,
} from 'echarts/components'
import VChart from 'vue-echarts'
import type { ComposeOption } from 'echarts/core'
import type { LineSeriesOption } from 'echarts/charts'
import type {
  TitleComponentOption,
  TooltipComponentOption,
  LegendComponentOption,
  GridComponentOption,
  DataZoomComponentOption,
} from 'echarts/components'
import {
  DiffOutlined,
  LineChartOutlined,
  BarChartOutlined,
  TableOutlined,
  ReloadOutlined,
} from '@ant-design/icons-vue'
import api from '../api'
import { formatDate, bondTypeColor } from '../utils/format'

use([
  CanvasRenderer,
  LineChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent,
])

type ECOption = ComposeOption<
  | LineSeriesOption
  | TitleComponentOption
  | TooltipComponentOption
  | LegendComponentOption
  | GridComponentOption
  | DataZoomComponentOption
>

interface Bond {
  id: string
  code: string
  name: string
  bond_type: string
  credit_rating?: string
}

interface AutoCompleteOption {
  value: string
  label: string
  bond: Bond
}

interface TargetStats {
  bond_id: string
  code: string
  name: string
  color: string
  current_spread: number
  mean: number
  std_dev: number
  z_score: number
}

interface DailyData {
  date: string
  [key: string]: number | string
}

interface AnalysisResult {
  targetStats: TargetStats[]
  dailyData: DailyData[]
}

const CHART_COLORS = ['#1890ff', '#f5222d', '#52c41a', '#fa8c16', '#722ed1']

const loading = ref(false)
const benchmarkSearchText = ref('')
const benchmarkBond = ref<Bond | null>(null)
const benchmarkOptions = ref<AutoCompleteOption[]>([])
const targetSearchText = ref('')
const targetBondIds = ref<string[]>([])
const targetBondsMap = reactive<Map<string, Bond>>(new Map())
const targetOptions = ref<AutoCompleteOption[]>([])
const spreadType = ref<'yield' | 'price'>('yield')
const dateRange = ref<[dayjs.Dayjs, dayjs.Dayjs]>([
  dayjs().subtract(3, 'month'),
  dayjs(),
])
const analysisResult = ref<AnalysisResult | null>(null)

let benchmarkSearchTimer: ReturnType<typeof setTimeout> | null = null
let targetSearchTimer: ReturnType<typeof setTimeout> | null = null

const canAnalyze = computed(() => benchmarkBond.value && targetBondIds.value.length > 0)

const spreadTypeLabel = computed(() =>
  spreadType.value === 'yield' ? '收益率利差 (bp)' : '净价利差 (元)'
)

const detailColumns = computed(() => {
  const columns: any[] = [
    { title: '日期', key: 'date', width: 120, fixed: 'left' },
  ]

  if (analysisResult.value) {
    analysisResult.value.targetStats.forEach((stats) => {
      columns.push({
        title: () =>
          h('span', [
            h('span', {
              class: 'inline-block w-2 h-2 rounded-full mr-1',
              style: { backgroundColor: stats.color },
            }),
            `${stats.code} 利差`,
          ]),
        key: `spread_${stats.bond_id}`,
        width: 140,
        align: 'right',
      })
    })
  }

  return columns
})

const chartOption = computed<ECOption>(() => {
  if (!analysisResult.value) return {}

  const dates = analysisResult.value.dailyData.map((d) => d.date)
  const series: LineSeriesOption[] = analysisResult.value.targetStats.map((stats) => ({
    name: `${stats.code} ${stats.name}`,
    type: 'line',
    data: analysisResult.value!.dailyData.map((d) => d[`spread_${stats.bond_id}`]),
    smooth: true,
    symbol: 'circle',
    symbolSize: 6,
    lineStyle: {
      width: 2,
      color: stats.color,
    },
    itemStyle: {
      color: stats.color,
    },
    emphasis: {
      focus: 'series',
    },
  }))

  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e8e8e8',
      borderWidth: 1,
      textStyle: {
        color: '#333',
      },
      formatter: (params: any) => {
        let result = `<div class="font-semibold mb-1">${params[0].axisValue}</div>`
        params.forEach((p: any) => {
          const val = p.value != null ? formatSpread(p.value) : '--'
          result += `
            <div class="flex items-center justify-between gap-4">
              <span class="flex items-center gap-1">
                <span class="w-2 h-2 rounded-full" style="background-color:${p.color}"></span>
                ${p.seriesName.split(' ')[0]}
              </span>
              <span class="font-mono font-semibold">${val}</span>
            </div>
          `
        })
        return result
      },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '10%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: dates,
      axisLabel: {
        rotate: 45,
        fontSize: 11,
      },
    },
    yAxis: {
      type: 'value',
      name: spreadTypeLabel.value,
      nameTextStyle: {
        fontSize: 12,
        color: '#666',
      },
      axisLabel: {
        fontSize: 11,
        formatter: (value: number) => formatSpread(value),
      },
      splitLine: {
        lineStyle: {
          type: 'dashed',
          color: '#f0f0f0',
        },
      },
    },
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100,
      },
      {
        type: 'slider',
        start: 0,
        end: 100,
        height: 24,
        bottom: 10,
      },
    ],
    series,
  }
})

function disabledDate(current: dayjs.Dayjs) {
  return current && current.isAfter(dayjs().endOf('day'))
}

function formatSpread(val: number | null | undefined): string {
  if (val == null) return '--'
  if (spreadType.value === 'yield') {
    return (val * 100).toFixed(2) + ' bp'
  }
  return val.toFixed(4) + ' 元'
}

function getSpreadClass(val: number | null | undefined): string {
  if (val == null) return ''
  if (val > 0) return 'text-red-600'
  if (val < 0) return 'text-green-600'
  return 'text-gray-600'
}

function getZScoreClass(val: number | null | undefined): string {
  if (val == null) return ''
  if (val > 2) return 'text-red-600'
  if (val < -2) return 'text-green-600'
  return 'text-gray-600'
}

function isTargetDisabled(bondId: string): boolean {
  return targetBondIds.value.includes(bondId)
}

async function searchBonds(keyword: string): Promise<Bond[]> {
  if (!keyword.trim()) return []
  try {
    const res = await api.get<{ items: Bond[] }>('/api/bonds', {
      params: { keyword, page_size: 20 },
    })
    return res.data.items ?? []
  } catch {
    return []
  }
}

function handleBenchmarkSearch(value: string) {
  if (benchmarkSearchTimer) clearTimeout(benchmarkSearchTimer)
  benchmarkSearchTimer = setTimeout(async () => {
    const bonds = await searchBonds(value)
    benchmarkOptions.value = bonds.map((b) => ({
      value: b.id,
      label: `${b.code} ${b.name}`,
      bond: b,
    }))
  }, 300)
}

function handleBenchmarkSelect(value: string, option: AutoCompleteOption) {
  benchmarkBond.value = option.bond
  benchmarkSearchText.value = option.label
}

function handleBenchmarkClear() {
  benchmarkBond.value = null
  benchmarkOptions.value = []
}

async function handleTargetSearch(value: string) {
  if (targetSearchTimer) clearTimeout(targetSearchTimer)
  targetSearchTimer = setTimeout(async () => {
    const bonds = await searchBonds(value)
    targetOptions.value = bonds
      .filter((b) => b.id !== benchmarkBond.value?.id)
      .map((b) => ({
        value: b.id,
        label: `${b.code} ${b.name}`,
        bond: b,
      }))
  }, 300)
}

function handleTargetDeselect(bondId: string) {
  targetBondsMap.delete(bondId)
}

function handleDateChange() {
  if (dateRange.value && dateRange.value[0] && dateRange.value[1]) {
    if (dateRange.value[0].isAfter(dateRange.value[1])) {
      ;[dateRange.value[0], dateRange.value[1]] = [dateRange.value[1], dateRange.value[0]]
    }
  }
}

async function handleAnalyze() {
  if (!benchmarkBond.value || targetBondIds.value.length === 0) {
    message.warning('请选择基准债券和目标债券')
    return
  }

  targetBondIds.value.forEach((id) => {
    const opt = targetOptions.value.find((o) => o.value === id)
    if (opt) {
      targetBondsMap.set(id, opt.bond)
    }
  })

  loading.value = true
  try {
    const allBondIds = [benchmarkBond.value.id, ...targetBondIds.value]
    const res = await api.get<any>('/api/bonds/spread/analysis', {
      params: {
        benchmark_bond_id: benchmarkBond.value.id,
        target_bond_ids: targetBondIds.value.join(','),
        spread_type: spreadType.value,
        start_date: dateRange.value[0].format('YYYY-MM-DD'),
        end_date: dateRange.value[1].format('YYYY-MM-DD'),
      },
    })

    analysisResult.value = transformAnalysisData(
      res.data,
      benchmarkBond.value,
      targetBondIds.value.map((id) => targetBondsMap.get(id)!).filter(Boolean)
    )

    message.success('分析完成')
  } catch (err: any) {
    const detail = err.response?.data?.detail
    if (detail) {
      message.error(detail)
    }
    analysisResult.value = null
  } finally {
    loading.value = false
  }
}

function transformAnalysisData(
  data: any,
  benchmark: Bond,
  targets: Bond[]
): AnalysisResult {
  if (data && data.target_stats && data.daily_data) {
    const targetStats: TargetStats[] = data.target_stats.map((stats: any, index: number) => ({
      bond_id: stats.bond_id,
      code: stats.code,
      name: stats.name,
      color: CHART_COLORS[index % CHART_COLORS.length],
      current_spread: stats.current_spread,
      mean: stats.mean,
      std_dev: stats.std_dev,
      z_score: stats.z_score,
    }))

    const dailyData: DailyData[] = data.daily_data.map((item: any) => {
      const result: DailyData = { date: item.date }
      item.spreads.forEach((s: any) => {
        result[`spread_${s.bond_id}`] = s.spread
      })
      return result
    })

    return { targetStats, dailyData }
  }

  return generateMockAnalysisData(benchmark, targets)
}

function generateMockAnalysisData(benchmark: Bond, targets: Bond[]): AnalysisResult {
  const startDate = dateRange.value[0]
  const endDate = dateRange.value[1]
  const days = endDate.diff(startDate, 'day') + 1

  const dailyData: DailyData[] = []
  const baseSpreads = targets.map((_, i) => 0.5 + i * 0.3)

  for (let i = 0; i < days; i++) {
    const currentDate = startDate.add(i, 'day')
    if (currentDate.day() === 0 || currentDate.day() === 6) continue

    const item: DailyData = { date: currentDate.format('YYYY-MM-DD') }
    targets.forEach((target, index) => {
      const baseSpread = baseSpreads[index]
      const randomWalk = (Math.random() - 0.5) * 0.1
      const trend = (i / days) * 0.2
      item[`spread_${target.id}`] = Math.max(0.1, baseSpread + randomWalk + trend)
    })
    dailyData.push(item)
  }

  const targetStats: TargetStats[] = targets.map((target, index) => {
    const spreads = dailyData
      .map((d) => d[`spread_${target.id}`] as number)
      .filter((v) => v != null)

    const currentSpread = spreads[spreads.length - 1]
    const mean = spreads.reduce((a, b) => a + b, 0) / spreads.length
    const variance = spreads.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / spreads.length
    const stdDev = Math.sqrt(variance)
    const zScore = stdDev > 0 ? (currentSpread - mean) / stdDev : 0

    return {
      bond_id: target.id,
      code: target.code,
      name: target.name,
      color: CHART_COLORS[index % CHART_COLORS.length],
      current_spread: currentSpread,
      mean,
      std_dev: stdDev,
      z_score: zScore,
    }
  })

  return { targetStats, dailyData }
}

function handleReset() {
  benchmarkSearchText.value = ''
  benchmarkBond.value = null
  benchmarkOptions.value = []
  targetBondIds.value = []
  targetBondsMap.clear()
  targetOptions.value = []
  spreadType.value = 'yield'
  dateRange.value = [dayjs().subtract(3, 'month'), dayjs()]
  analysisResult.value = null
}

watch(
  () => targetBondIds.value,
  (newIds) => {
    newIds.forEach((id) => {
      if (!targetBondsMap.has(id)) {
        const opt = targetOptions.value.find((o) => o.value === id)
        if (opt) {
          targetBondsMap.set(id, opt.bond)
        }
      }
    })
  },
  { deep: true }
)
</script>

<style scoped>
.spread-analysis-view {
  min-height: 100%;
}

.stats-card {
  background: linear-gradient(135deg, #fafafa 0%, #ffffff 100%);
  transition: transform 0.2s, box-shadow 0.2s;
}

.stats-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.chart-container {
  height: 400px;
  width: 100%;
}

:deep(.ant-form-item) {
  margin-bottom: 16px;
}

:deep(.ant-select-selector) {
  min-height: 40px !important;
}
</style>
