<template>
  <a-layout class="app-layout min-h-screen">
    <a-layout-sider
      v-model:collapsed="collapsed"
      :width="220"
      :collapsed-width="0"
      class="app-sider"
    >
      <div class="logo-wrap flex items-center justify-center h-16 px-4 border-b border-white/10">
        <span class="text-white font-bold text-xl tracking-wide">BondView</span>
      </div>
      <a-menu
        v-model:selectedKeys="selectedKeys"
        theme="dark"
        mode="inline"
        class="app-menu"
        @click="handleMenuClick"
      >
        <a-menu-item key="/dashboard">
          <template #icon>
            <DashboardOutlined />
          </template>
          行情看板
        </a-menu-item>
        <a-menu-item key="/market">
          <template #icon>
            <StockOutlined />
          </template>
          聚合行情
        </a-menu-item>
        <a-menu-item key="/trades">
          <template #icon>
            <SwapOutlined />
          </template>
          成交记录
        </a-menu-item>
        <a-menu-item key="/futures">
          <template #icon>
            <FundOutlined />
          </template>
          国债期货
        </a-menu-item>
        <a-menu-item key="/swaps">
          <template #icon>
            <TransactionOutlined />
          </template>
          收益互换
        </a-menu-item>
        <a-menu-item key="/favorites">
          <template #icon>
            <StarOutlined />
          </template>
          我的关注
        </a-menu-item>
        <a-sub-menu v-if="authStore.isAdmin()" key="admin">
          <template #icon>
            <SettingOutlined />
          </template>
          <template #title>系统管理</template>
          <a-menu-item key="/admin/users">用户管理</a-menu-item>
          <a-menu-item key="/admin/sources">行情源管理</a-menu-item>
        </a-sub-menu>
      </a-menu>
    </a-layout-sider>
    <a-layout>
      <a-layout-header class="app-header flex items-center justify-between px-6 bg-white border-b border-gray-200">
        <div class="flex-1" />
        <div class="flex items-center gap-4">
          <span class="text-gray-600">{{ authStore.user?.display_name || authStore.user?.username }}</span>
          <a-tag :color="roleColor">{{ roleLabel }}</a-tag>
          <a-button type="text" danger size="small" @click="handleLogout">
            退出
          </a-button>
        </div>
      </a-layout-header>
      <a-layout-content class="app-content p-6 bg-gray-50">
        <router-view />
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  DashboardOutlined,
  StockOutlined,
  SwapOutlined,
  FundOutlined,
  TransactionOutlined,
  StarOutlined,
  SettingOutlined,
} from '@ant-design/icons-vue'
import { useAuthStore } from '../../stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const collapsed = ref(false)
const selectedKeys = ref<string[]>([route.path])

watch(
  () => route.path,
  (path) => {
    selectedKeys.value = [path]
    // 处理子菜单高亮：若在 admin 子路由，也高亮父级
    if (path.startsWith('/admin/')) {
      selectedKeys.value = [path]
    }
  },
  { immediate: true }
)

const roleLabel = computed(() => {
  const role = authStore.user?.role
  if (role === 'admin') return '管理员'
  if (role === 'trader') return '交易员'
  return role || '用户'
})

const roleColor = computed(() => {
  const role = authStore.user?.role
  if (role === 'admin') return 'red'
  if (role === 'trader') return 'blue'
  return 'default'
})

function handleMenuClick({ key }: { key: string }) {
  router.push(key)
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.app-layout :deep(.ant-layout-sider) {
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%) !important;
}

.app-menu :deep(.ant-menu) {
  background: transparent !important;
}

.app-menu :deep(.ant-menu-item),
.app-menu :deep(.ant-menu-submenu-title) {
  color: rgba(255, 255, 255, 0.85);
}

.app-menu :deep(.ant-menu-item-selected) {
  background: rgba(255, 255, 255, 0.15) !important;
  color: #fff !important;
}

.app-menu :deep(.ant-menu-item:hover),
.app-menu :deep(.ant-menu-submenu-title:hover) {
  color: #fff !important;
}

.app-header {
  height: 56px;
  line-height: 56px;
}
</style>
