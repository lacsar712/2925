import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { useAuthStore } from './auth'

export type DashboardBlockKey = 'stats' | 'yieldCurve' | 'hotBonds' | 'alerts'

export interface DashboardBlockConfig {
  key: DashboardBlockKey
  title: string
  visible: boolean
  order: number
}

export const DEFAULT_BLOCK_ORDER: DashboardBlockKey[] = ['stats', 'yieldCurve', 'hotBonds', 'alerts']

export const BLOCK_TITLE_MAP: Record<DashboardBlockKey, string> = {
  stats: '统计卡片',
  yieldCurve: '收益率曲线',
  hotBonds: '热门债券',
  alerts: '异动提醒',
}

export const BLOCK_SPAN_MAP: Record<DashboardBlockKey, { xs: number; lg: number }> = {
  stats: { xs: 24, lg: 24 },
  yieldCurve: { xs: 24, lg: 16 },
  hotBonds: { xs: 24, lg: 8 },
  alerts: { xs: 24, lg: 24 },
}

function getStorageKey(userId: string | null | undefined): string {
  return `bondview_dashboard_layout_${userId ?? 'guest'}`
}

function createDefaultBlocks(): DashboardBlockConfig[] {
  return DEFAULT_BLOCK_ORDER.map((key, index) => ({
    key,
    title: BLOCK_TITLE_MAP[key],
    visible: true,
    order: index,
  }))
}

function loadFromStorage(userId: string | null | undefined): DashboardBlockConfig[] | null {
  const raw = localStorage.getItem(getStorageKey(userId))
  if (!raw) return null
  try {
    const parsed = JSON.parse(raw) as DashboardBlockConfig[]
    const validKeys = new Set<DashboardBlockKey>(DEFAULT_BLOCK_ORDER)
    const filtered = parsed.filter(b => validKeys.has(b.key))
    if (filtered.length === 0) return null
    const existingKeys = new Set(filtered.map(b => b.key))
    DEFAULT_BLOCK_ORDER.forEach(key => {
      if (!existingKeys.has(key)) {
        filtered.push({ key, title: BLOCK_TITLE_MAP[key], visible: true, order: filtered.length })
      }
    })
    return filtered.sort((a, b) => a.order - b.order)
  } catch {
    return null
  }
}

export const useDashboardLayoutStore = defineStore('dashboardLayout', () => {
  const authStore = useAuthStore()

  const blocks = ref<DashboardBlockConfig[]>(createDefaultBlocks())
  const editMode = ref(false)

  const sortedVisibleBlocks = computed(() =>
    blocks.value
      .filter(b => b.visible)
      .sort((a, b) => a.order - b.order)
  )

  const sortedAllBlocks = computed(() =>
    [...blocks.value].sort((a, b) => a.order - b.order)
  )

  function initForUser() {
    const saved = loadFromStorage(authStore.user?.id)
    if (saved) {
      blocks.value = saved
    } else {
      blocks.value = createDefaultBlocks()
    }
  }

  function saveToStorage() {
    const userId = authStore.user?.id
    if (!userId) return
    const toSave = [...blocks.value].sort((a, b) => a.order - b.order)
    localStorage.setItem(getStorageKey(userId), JSON.stringify(toSave))
  }

  function enterEditMode() {
    editMode.value = true
  }

  function exitEditMode() {
    editMode.value = false
    saveToStorage()
  }

  function toggleBlockVisibility(key: DashboardBlockKey) {
    const block = blocks.value.find(b => b.key === key)
    if (block) {
      block.visible = !block.visible
    }
  }

  function setBlockVisibility(key: DashboardBlockKey, visible: boolean) {
    const block = blocks.value.find(b => b.key === key)
    if (block) {
      block.visible = visible
    }
  }

  function reorderBlocks(newOrder: DashboardBlockKey[]) {
    newOrder.forEach((key, index) => {
      const block = blocks.value.find(b => b.key === key)
      if (block) {
        block.order = index
      }
    })
  }

  function resetToDefault() {
    blocks.value = createDefaultBlocks()
    saveToStorage()
  }

  watch(
    () => authStore.user?.id,
    (newId, oldId) => {
      if (newId !== oldId) {
        if (editMode.value) {
          editMode.value = false
        }
      }
      initForUser()
    },
    { immediate: true }
  )

  return {
    blocks,
    editMode,
    sortedVisibleBlocks,
    sortedAllBlocks,
    initForUser,
    saveToStorage,
    enterEditMode,
    exitEditMode,
    toggleBlockVisibility,
    setBlockVisibility,
    reorderBlocks,
    resetToDefault,
  }
})
