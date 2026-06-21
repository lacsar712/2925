<template>
  <div class="dashboard p-4">
    <a-spin :spinning="loading" tip="加载中...">
      <ConfigurableDashboardLayout>
        <template #block-stats>
          <StatsCards :overview="overview" :updated-at="overviewUpdatedAt" />
        </template>
        <template #block-yieldCurve>
          <YieldCurveBlock :data="yieldCurve" :updated-at="yieldCurveUpdatedAt" />
        </template>
        <template #block-hotBonds>
          <HotBondsBlock :bonds="hotBonds" :updated-at="hotBondsUpdatedAt" />
        </template>
        <template #block-alerts>
          <AlertsBlock
            :alerts="alerts"
            :updated-at="alertsUpdatedAt"
            :loading="loading"
          />
        </template>
      </ConfigurableDashboardLayout>
    </a-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '../api'
import { formatVolume, formatAmount, formatTime } from '../utils/format'
import ConfigurableDashboardLayout from '../components/dashboard/ConfigurableDashboardLayout.vue'
import StatsCards from '../components/dashboard/StatsCards.vue'
import YieldCurveBlock from '../components/dashboard/YieldCurveBlock.vue'
import HotBondsBlock from '../components/dashboard/HotBondsBlock.vue'
import AlertsBlock from '../components/dashboard/AlertsBlock.vue'
import type { StatsOverview } from '../components/dashboard/StatsCards.vue'
import type { YieldPoint } from '../components/dashboard/YieldCurveBlock.vue'
import type { HotBond } from '../components/dashboard/HotBondsBlock.vue'
import type { AlertItem } from '../components/dashboard/AlertsBlock.vue'
import { useDashboardLayoutStore } from '../stores/dashboardLayout'

const layoutStore = useDashboardLayoutStore()

const loading = ref(true)
const overview = ref<StatsOverview | null>(null)
const yieldCurve = ref<YieldPoint[]>([])
const hotBonds = ref<HotBond[]>([])
const alerts = ref<AlertItem[]>([])
const overviewUpdatedAt = ref<string>('')
const yieldCurveUpdatedAt = ref<string>('')
const hotBondsUpdatedAt = ref<string>('')
const alertsUpdatedAt = ref<string>('')

async function fetchData() {
  loading.value = true
  try {
    const [overviewRes, curveRes, hotRes, alertsRes] = await Promise.all([
      api.get('/api/dashboard/overview'),
      api.get('/api/dashboard/yield-curve'),
      api.get('/api/dashboard/hot-bonds'),
      api.get('/api/dashboard/alerts'),
    ])
    overview.value = overviewRes.data?.data ?? overviewRes.data
    overviewUpdatedAt.value = overviewRes.data?.updated_at ?? ''
    yieldCurve.value = Array.isArray(curveRes.data?.data) ? curveRes.data.data : (Array.isArray(curveRes.data) ? curveRes.data : [])
    yieldCurveUpdatedAt.value = curveRes.data?.updated_at ?? ''
    const hotData = Array.isArray(hotRes.data?.data) ? hotRes.data.data : (Array.isArray(hotRes.data) ? hotRes.data : [])
    hotBonds.value = hotData.map((b: HotBond, i: number) => ({ ...b, rank: i + 1 }))
    hotBondsUpdatedAt.value = hotRes.data?.updated_at ?? ''
    alerts.value = Array.isArray(alertsRes.data?.data) ? alertsRes.data.data : (Array.isArray(alertsRes.data) ? alertsRes.data : [])
    alertsUpdatedAt.value = alertsRes.data?.updated_at ?? ''
  } catch {
    overview.value = null
    yieldCurve.value = []
    hotBonds.value = []
    alerts.value = []
  } finally {
    loading.value = false
  }
}

void formatVolume
void formatAmount

onMounted(() => {
  layoutStore.initForUser()
  fetchData()
})
</script>
