<template>
  <a-card title="国债收益率曲线" class="rounded-lg h-full">
    <template #extra>
      <span class="text-xs text-gray-400">更新于 {{ formatTime(updatedAt) }}</span>
    </template>
    <v-chart
      v-if="chartOption"
      :option="chartOption"
      class="h-[320px]"
      autoresize
    />
    <a-empty v-else description="暂无数据" />
  </a-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, TitleComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { formatTime } from '../../utils/format'

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, TitleComponent])

export interface YieldPoint {
  term: number
  yield: number
}

const props = defineProps<{
  data: YieldPoint[]
  updatedAt: string
}>()

const chartOption = computed(() => {
  const data = props.data
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
</script>
