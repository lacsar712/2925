<template>
  <div class="configurable-dashboard">
    <div class="flex items-center justify-between mb-4 flex-wrap gap-2">
      <div class="flex items-center gap-2 min-h-[32px]">
        <a-alert
          v-if="layoutStore.editMode"
          type="warning"
          show-icon
          class="!py-1.5 !px-3 text-sm"
          :banner="false"
          message="编辑模式 - 拖拽左侧手柄调整顺序，使用开关控制显示"
        />
      </div>
      <div class="flex items-center gap-2">
        <a-popconfirm
          title="确定恢复默认布局吗？所有自定义排序和显示设置将被重置。"
          ok-text="恢复"
          cancel-text="取消"
          ok-button-props="{ danger: true }"
          @confirm="handleReset"
        >
          <a-button size="small" :type="layoutStore.editMode ? 'dashed' : 'default'" danger>
            <template #icon><ReloadOutlined /></template>
            恢复默认布局
          </a-button>
        </a-popconfirm>
        <a-button
          v-if="layoutStore.editMode"
          size="small"
          type="primary"
          @click="handleExitEditMode"
        >
          <template #icon><CheckOutlined /></template>
          完成编辑
        </a-button>
        <a-button
          v-else
          size="small"
          type="primary"
          ghost
          @click="layoutStore.enterEditMode()"
        >
          <template #icon><SettingOutlined /></template>
          编辑布局
        </a-button>
      </div>
    </div>

    <draggable
      v-model="dragList"
      :disabled="!layoutStore.editMode"
      item-key="key"
      handle=".drag-handle-area"
      ghost-class="drag-ghost"
      chosen-class="drag-chosen"
      :animation="200"
      class="dashboard-grid"
    >
      <template #item="{ element }">
        <div
          class="dashboard-item"
          :class="[
            `span-${getBlockSpan(element.key).lg}`,
            {
              'hidden-in-view': !layoutStore.editMode && !element.visible,
              'block-hidden': layoutStore.editMode && !element.visible,
              'block-visible-edit': layoutStore.editMode,
            },
          ]"
        >
          <div
            v-if="layoutStore.editMode"
            class="edit-header flex items-center justify-between px-3 py-1.5 rounded-t-lg border border-b-0 border-blue-200 bg-gradient-to-r from-blue-50 to-cyan-50"
          >
            <div class="flex items-center gap-2 drag-handle-area cursor-move select-none">
              <div class="flex flex-col items-center gap-0.3 p-1 rounded hover:bg-blue-100/80 transition-colors">
                <div class="flex gap-0.3">
                  <span class="w-1 h-1 rounded-full bg-blue-400 inline-block"></span>
                  <span class="w-1 h-1 rounded-full bg-blue-400 inline-block"></span>
                </div>
                <div class="flex gap-0.3">
                  <span class="w-1 h-1 rounded-full bg-blue-400 inline-block"></span>
                  <span class="w-1 h-1 rounded-full bg-blue-400 inline-block"></span>
                </div>
                <div class="flex gap-0.3">
                  <span class="w-1 h-1 rounded-full bg-blue-400 inline-block"></span>
                  <span class="w-1 h-1 rounded-full bg-blue-400 inline-block"></span>
                </div>
              </div>
              <span class="font-medium text-gray-700 text-sm">{{ element.title }}</span>
            </div>
            <div class="flex items-center gap-2">
              <EyeInvisibleOutlined
                v-if="!element.visible"
                class="text-gray-400"
              />
              <EyeOutlined
                v-else
                class="text-green-500"
              />
              <a-switch
                :checked="element.visible"
                size="small"
                @change="(v: boolean) => handleVisibilityChange(element.key, v)"
              />
            </div>
          </div>
          <div
            class="item-slot-wrap"
            :class="{
              'rounded-b-lg overflow-hidden border border-t-0 border-blue-200': layoutStore.editMode,
              'rounded-lg overflow-hidden border border-blue-200': layoutStore.editMode && !element.visible,
            }"
          >
            <div v-if="layoutStore.editMode && !element.visible" class="p-6 text-center text-gray-400 bg-gray-50">
              <EyeInvisibleOutlined class="text-2xl mb-2" />
              <div class="text-sm">{{ element.title }}（已隐藏）</div>
            </div>
            <template v-else>
              <slot
                :name="`block-${element.key}`"
                :block="element"
              >
                <div class="p-8 text-center text-gray-400">
                  {{ element.title }} - 未提供内容
                </div>
              </slot>
            </template>
          </div>
        </div>
      </template>
    </draggable>
  </div>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue'
import {
  SettingOutlined,
  CheckOutlined,
  ReloadOutlined,
  EyeOutlined,
  EyeInvisibleOutlined,
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import draggable from 'vuedraggable'
import {
  useDashboardLayoutStore,
  DashboardBlockKey,
  DashboardBlockConfig,
  BLOCK_SPAN_MAP,
} from '../../stores/dashboardLayout'

const layoutStore = useDashboardLayoutStore()

const dragList = computed({
  get: () => layoutStore.sortedAllBlocks.map(b => ({ ...b })),
  set: (val: DashboardBlockConfig[]) => {
    const newOrder = val.map(b => b.key)
    layoutStore.reorderBlocks(newOrder)
  },
})

const getBlockSpan = (key: DashboardBlockKey) => BLOCK_SPAN_MAP[key]

function handleVisibilityChange(key: DashboardBlockKey, visible: boolean) {
  layoutStore.setBlockVisibility(key, visible)
}

function handleExitEditMode() {
  layoutStore.exitEditMode()
  message.success('布局偏好已保存')
}

function handleReset() {
  layoutStore.resetToDefault()
  message.success('已恢复默认布局')
}

watch(
  () => layoutStore.editMode,
  (val) => {
    if (val) {
      message.info('进入编辑模式，可拖拽排序或切换显示')
    }
  }
)
</script>

<style scoped>
.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(24, minmax(0, 1fr));
  gap: 16px;
  align-items: start;
}

.dashboard-item {
  grid-column: span 24;
  min-width: 0;
  min-height: 0;
}

.dashboard-item.span-24 {
  grid-column: span 24;
}

.dashboard-item.span-16 {
  grid-column: span 24;
}

.dashboard-item.span-8 {
  grid-column: span 24;
}

@media (min-width: 992px) {
  .dashboard-item.span-16 {
    grid-column: span 16;
  }
  .dashboard-item.span-8 {
    grid-column: span 8;
  }
}

.dashboard-item.hidden-in-view {
  display: none !important;
}

.dashboard-item.block-hidden :deep(.ant-card) {
  opacity: 0;
  pointer-events: none;
  position: absolute;
}

.dashboard-item.block-visible-edit {
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

:deep(.drag-ghost) {
  opacity: 0.3;
  background: linear-gradient(135deg, #e6f7ff 0%, #bae7ff 100%);
  border: 2px dashed #1890ff;
  border-radius: 10px;
  pointer-events: none;
  visibility: visible !important;
}

:deep(.drag-chosen) {
  cursor: grabbing;
}

:deep(.drag-chosen .edit-header) {
  background: linear-gradient(135deg, #bae7ff 0%, #91d5ff 100%);
}

:deep(.sortable-drag) {
  opacity: 0.95;
  box-shadow: 0 12px 32px rgba(24, 144, 255, 0.18);
  border-radius: 10px;
  z-index: 9999 !important;
}

.edit-header {
  position: relative;
  z-index: 1;
}
</style>
