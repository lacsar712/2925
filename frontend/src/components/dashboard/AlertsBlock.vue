<template>
  <a-card title="行情异动提醒" class="rounded-lg">
    <template #extra>
      <span class="text-xs text-gray-400">更新于 {{ formatTime(updatedAt) }}</span>
    </template>
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
</template>

<script setup lang="ts">
import { formatTime } from '../../utils/format'

export interface AlertItem {
  bond_id?: string
  code?: string
  name?: string
  type?: string
  message: string
  level: 'info' | 'warning' | 'danger'
}

defineProps<{
  alerts: AlertItem[]
  updatedAt: string
  loading?: boolean
}>()
</script>
