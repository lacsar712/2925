import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api'

export interface WatchlistGroup {
  id: string
  name: string
  bond_count: number
  created_at?: string
  updated_at?: string
}

export interface WatchlistBond {
  id: string
  code: string
  name: string
  bond_type: string
  issuer?: string
  coupon_rate?: number
  remaining_term?: number
  credit_rating?: string
  best_bid_price?: number
  best_ask_price?: number
  best_bid_yield?: number
  best_ask_yield?: number
  latest_trade_price?: number
  latest_trade_yield?: number
  spread?: number
  volume_7d?: number
  order_index: number
}

export interface WatchlistGroupDetail {
  id: string
  name: string
  bonds: WatchlistBond[]
  created_at?: string
  updated_at?: string
}

export const useWatchlistStore = defineStore('watchlist', () => {
  const groups = ref<WatchlistGroup[]>([])
  const loading = ref(false)
  const currentGroup = ref<WatchlistGroupDetail | null>(null)
  const currentGroupLoading = ref(false)

  const sortedGroups = computed(() => [...groups.value])

  async function fetchGroups() {
    loading.value = true
    try {
      const res = await api.get<WatchlistGroup[]>('/api/watchlist-groups')
      groups.value = res.data || []
    } catch {
      groups.value = []
    } finally {
      loading.value = false
    }
  }

  async function createGroup(name: string) {
    const res = await api.post<WatchlistGroup>('/api/watchlist-groups', { name })
    await fetchGroups()
    return res.data
  }

  async function updateGroup(groupId: string, name: string) {
    const res = await api.put<WatchlistGroup>(`/api/watchlist-groups/${groupId}`, { name })
    await fetchGroups()
    if (currentGroup.value && currentGroup.value.id === groupId) {
      currentGroup.value.name = name
    }
    return res.data
  }

  async function deleteGroup(groupId: string) {
    await api.delete(`/api/watchlist-groups/${groupId}`)
    if (currentGroup.value && currentGroup.value.id === groupId) {
      currentGroup.value = null
    }
    await fetchGroups()
  }

  async function fetchGroupDetail(groupId: string) {
    currentGroupLoading.value = true
    try {
      const res = await api.get<WatchlistGroupDetail>(`/api/watchlist-groups/${groupId}`)
      currentGroup.value = res.data
    } catch {
      currentGroup.value = null
    } finally {
      currentGroupLoading.value = false
    }
  }

  async function addBondToGroup(groupId: string, bondId: string) {
    await api.post(`/api/watchlist-groups/${groupId}/bonds/${bondId}`)
    await fetchGroups()
    if (currentGroup.value && currentGroup.value.id === groupId) {
      await fetchGroupDetail(groupId)
    }
  }

  async function removeBondFromGroup(groupId: string, bondId: string) {
    await api.delete(`/api/watchlist-groups/${groupId}/bonds/${bondId}`)
    await fetchGroups()
    if (currentGroup.value && currentGroup.value.id === groupId) {
      await fetchGroupDetail(groupId)
    }
  }

  async function reorderBonds(groupId: string, bondIds: string[]) {
    await api.put(`/api/watchlist-groups/${groupId}/bonds/reorder`, { bond_ids: bondIds })
    if (currentGroup.value && currentGroup.value.id === groupId) {
      await fetchGroupDetail(groupId)
    }
  }

  function clearCurrentGroup() {
    currentGroup.value = null
  }

  return {
    groups,
    loading,
    sortedGroups,
    currentGroup,
    currentGroupLoading,
    fetchGroups,
    createGroup,
    updateGroup,
    deleteGroup,
    fetchGroupDetail,
    addBondToGroup,
    removeBondFromGroup,
    reorderBonds,
    clearCurrentGroup,
  }
})
