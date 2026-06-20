<template>
  <a-layout class="app-layout min-h-screen">
    <a-layout-sider
      v-model:collapsed="collapsed"
      :width="240"
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
        <a-menu-item key="/compare">
          <template #icon>
            <BarChartOutlined />
          </template>
          债券对比
        </a-menu-item>

        <a-sub-menu key="watchlist-groups">
          <template #icon>
            <FolderOutlined />
          </template>
          <template #title>
            <div class="flex items-center justify-between w-full pr-2">
              <span>自定义分组</span>
              <a-button
                type="text"
                size="small"
                class="ml-2 !text-white/80 hover:!text-white"
                @click.stop="openCreateModal"
              >
                <template #icon><PlusOutlined /></template>
              </a-button>
            </div>
          </template>
          <a-menu-item
            v-for="group in watchlistStore.sortedGroups"
            :key="`/watchlist/${group.id}`"
          >
            <div class="flex items-center justify-between w-full group-item-wrap">
              <div class="flex items-center gap-2 flex-1 min-w-0">
                <FolderOpenOutlined class="text-blue-300 flex-shrink-0" />
                <span class="truncate">{{ group.name }}</span>
                <a-tag color="blue" class="flex-shrink-0" :bordered="false" style="background: rgba(59,130,246,0.25); color: #bfdbfe;">
                  {{ group.bond_count }}
                </a-tag>
              </div>
              <div class="flex items-center gap-0 ml-1 flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity group-actions">
                <a-button
                  type="text"
                  size="small"
                  class="!text-white/70 hover:!text-white"
                  @click.stop="openRenameModal(group)"
                >
                  <template #icon><EditOutlined /></template>
                </a-button>
                <a-popconfirm
                  :title="`确定删除分组「${group.name}」吗？`"
                  ok-text="删除"
                  cancel-text="取消"
                  ok-button-props="{ danger: true }"
                  @confirm.stop="handleDeleteGroup(group.id)"
                >
                  <a-button
                    type="text"
                    size="small"
                    danger
                    class="!text-red-300 hover:!text-red-200"
                    @click.stop
                  >
                    <template #icon><DeleteOutlined /></template>
                  </a-button>
                </a-popconfirm>
              </div>
            </div>
          </a-menu-item>
          <a-menu-item
            v-if="watchlistStore.loading"
            key="watchlist-loading"
            disabled
          >
            <span class="text-white/50">加载中...</span>
          </a-menu-item>
          <a-menu-item
            v-else-if="watchlistStore.sortedGroups.length === 0"
            key="watchlist-empty"
            disabled
          >
            <span class="text-white/50">暂无分组，点击 + 创建</span>
          </a-menu-item>
        </a-sub-menu>

        <a-sub-menu key="alerts">
          <template #icon>
            <BellOutlined />
          </template>
          <template #title>价格预警</template>
          <a-menu-item key="/alerts/rules">预警规则</a-menu-item>
          <a-menu-item key="/alerts/history">触发历史</a-menu-item>
        </a-sub-menu>
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
          <ConnectionStatus />
          <AlertBell />
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

    <a-modal
      v-model:open="createModalOpen"
      title="创建自定义分组"
      ok-text="创建"
      cancel-text="取消"
      @ok="handleCreateGroup"
      @cancel="createModalOpen = false"
    >
      <a-input
        v-model:value="createGroupName"
        placeholder="请输入分组名称，例如：持仓关注、新发债跟踪"
        :maxlength="100"
        show-count
      />
    </a-modal>

    <a-modal
      v-model:open="renameModalOpen"
      title="重命名分组"
      ok-text="确定"
      cancel-text="取消"
      @ok="handleRenameGroup"
      @cancel="renameModalOpen = false"
    >
      <a-input
        v-model:value="renameGroupName"
        placeholder="请输入新的分组名称"
        :maxlength="100"
        show-count
      />
    </a-modal>
  </a-layout>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  DashboardOutlined,
  StockOutlined,
  SwapOutlined,
  FundOutlined,
  TransactionOutlined,
  StarOutlined,
  BarChartOutlined,
  BellOutlined,
  SettingOutlined,
  FolderOutlined,
  FolderOpenOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
} from '@ant-design/icons-vue'
import { useAuthStore } from '../../stores/auth'
import { useWatchlistStore } from '../../stores/watchlist'
import AlertBell from './AlertBell.vue'
import ConnectionStatus from './ConnectionStatus.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const watchlistStore = useWatchlistStore()

const collapsed = ref(false)
const selectedKeys = ref<string[]>([route.path])
const createModalOpen = ref(false)
const createGroupName = ref('')
const renameModalOpen = ref(false)
const renameGroupName = ref('')
const renameGroupId = ref<string | null>(null)

watch(
  () => route.path,
  (path) => {
    if (path.startsWith('/watchlist/')) {
      selectedKeys.value = [path, 'watchlist-groups']
    } else {
      selectedKeys.value = [path]
    }
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
  if (key === 'watchlist-groups') return
  router.push(key)
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}

function openCreateModal() {
  createGroupName.value = ''
  createModalOpen.value = true
}

async function handleCreateGroup() {
  if (!createGroupName.value.trim()) return
  try {
    const group = await watchlistStore.createGroup(createGroupName.value.trim())
    message.success(`分组「${group.name}」创建成功`)
    createModalOpen.value = false
    router.push(`/watchlist/${group.id}`)
  } catch {
  }
}

function openRenameModal(group: { id: string; name: string }) {
  renameGroupId.value = group.id
  renameGroupName.value = group.name
  renameModalOpen.value = true
}

async function handleRenameGroup() {
  if (!renameGroupName.value.trim() || !renameGroupId.value) return
  try {
    await watchlistStore.updateGroup(renameGroupId.value, renameGroupName.value.trim())
    message.success('分组已重命名')
    renameModalOpen.value = false
    renameGroupId.value = null
  } catch {
  }
}

async function handleDeleteGroup(groupId: string) {
  try {
    await watchlistStore.deleteGroup(groupId)
    message.success('分组已删除')
    if (route.path.startsWith('/watchlist/')) {
      router.push('/favorites')
    }
  } catch {
  }
}

onMounted(() => {
  if (authStore.token) {
    watchlistStore.fetchGroups()
  }
})
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

.group-item-wrap {
  position: relative;
}

.group-actions {
  position: absolute;
  right: 4px;
  top: 50%;
  transform: translateY(-50%);
}

.app-menu :deep(.ant-menu-item:hover .group-actions) {
  opacity: 1 !important;
}
</style>
