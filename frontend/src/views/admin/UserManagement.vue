<template>
  <div class="user-management p-4">
    <a-card class="rounded-lg">
      <template #extra>
        <a-button type="primary" @click="openCreateModal">
          <template #icon><PlusOutlined /></template>
          新增用户
        </a-button>
      </template>

      <a-table
        :data-source="users"
        :columns="columns"
        :loading="loading"
        :pagination="false"
        :scroll="{ x: 'max-content' }"
        :row-key="(r) => r.id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'role'">
            <a-tag :color="roleColor(record.role)">
              {{ roleLabel(record.role) }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'is_active'">
            <a-badge
              :status="record.is_active ? 'success' : 'default'"
              :text="record.is_active ? '活跃' : '停用'"
            />
          </template>
          <template v-else-if="column.key === 'created_at'">
            <span class="tabular-nums">{{ formatDateTime(record.created_at) }}</span>
          </template>
          <template v-else-if="column.key === 'action'">
            <a-space size="small">
              <a-button size="small" type="link" @click="openEditModal(record)">编辑</a-button>
              <a-popconfirm
                title="确认删除该用户？"
                ok-text="确认"
                cancel-text="取消"
                @confirm="deleteUser(record.id)"
              >
                <a-button size="small" type="link" danger>删除</a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <a-modal
      v-model:open="modalVisible"
      :title="isEdit ? '编辑用户' : '新增用户'"
      ok-text="确认"
      cancel-text="取消"
      :confirm-loading="submitting"
      @ok="handleSubmit"
    >
      <a-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        layout="vertical"
        label-align="left"
      >
        <a-form-item label="用户名" name="username">
          <a-input v-model:value="formData.username" :disabled="isEdit" placeholder="请输入用户名" />
        </a-form-item>
        <a-form-item
          v-if="!isEdit"
          label="密码"
          name="password"
        >
          <a-input-password v-model:value="formData.password" placeholder="请输入密码（至少6位）" />
        </a-form-item>
        <a-form-item
          v-if="isEdit"
          label="新密码"
          name="password"
        >
          <a-input-password v-model:value="formData.password" placeholder="留空则不修改密码" />
        </a-form-item>
        <a-form-item label="显示名称" name="display_name">
          <a-input v-model:value="formData.display_name" placeholder="请输入显示名称" />
        </a-form-item>
        <a-form-item label="角色" name="role">
          <a-select v-model:value="formData.role">
            <a-select-option value="admin">管理员</a-select-option>
            <a-select-option value="trader">交易员</a-select-option>
            <a-select-option value="viewer">查看者</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="部门" name="department">
          <a-input v-model:value="formData.department" placeholder="请输入部门（选填）" />
        </a-form-item>
        <a-form-item v-if="isEdit" label="状态" name="is_active">
          <a-switch v-model:checked="formData.is_active" checked-children="启用" un-checked-children="停用" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import type { FormInstance } from 'ant-design-vue'
import type { RuleObject } from 'ant-design-vue/es/form/interface'
import api from '../../api'
import { formatDateTime } from '../../utils/format'

interface AdminUser {
  id: string
  username: string
  display_name: string
  role: 'admin' | 'trader' | 'viewer'
  department?: string
  is_active: boolean
  created_at?: string
}

const loading = ref(false)
const users = ref<AdminUser[]>([])
const modalVisible = ref(false)
const submitting = ref(false)
const isEdit = ref(false)
const editingId = ref<string | null>(null)
const formRef = ref<FormInstance>()

const formData = reactive({
  username: '',
  password: '',
  display_name: '',
  role: 'trader' as 'admin' | 'trader' | 'viewer',
  department: '',
  is_active: true,
})

const rules: Record<string, RuleObject[]> = {
  username: [{ required: true, message: '请输入用户名', min: 2, max: 50 }],
  password: [
    {
      validator: (_rule, value) => {
        if (!isEdit.value && !value) {
          return Promise.reject('请输入密码')
        }
        if (value && value.length < 6) {
          return Promise.reject('密码至少6位')
        }
        return Promise.resolve()
      },
    },
  ],
  display_name: [{ required: true, message: '请输入显示名称' }],
  role: [{ required: true, message: '请选择角色' }],
}

function roleColor(role: string): string {
  const map: Record<string, string> = {
    admin: 'blue',
    trader: 'green',
    viewer: 'default',
  }
  return map[role] || 'default'
}

function roleLabel(role: string): string {
  const map: Record<string, string> = {
    admin: '管理员',
    trader: '交易员',
    viewer: '查看者',
  }
  return map[role] || role
}

const columns = [
  { title: '用户名', dataIndex: 'username', key: 'username', width: 120 },
  { title: '显示名称', dataIndex: 'display_name', key: 'display_name', width: 120 },
  { title: '角色', key: 'role', dataIndex: 'role', width: 100 },
  { title: '部门', dataIndex: 'department', key: 'department' },
  { title: '状态', key: 'is_active', dataIndex: 'is_active', width: 100 },
  { title: '创建时间', key: 'created_at', dataIndex: 'created_at', width: 180 },
  { title: '操作', key: 'action', width: 140, fixed: 'right' },
]

async function fetchUsers() {
  loading.value = true
  try {
    const res = await api.get<AdminUser[] | { items: AdminUser[] }>('/api/admin/users')
    const data = res.data
    users.value = Array.isArray(data) ? data : (data as { items: AdminUser[] }).items ?? []
  } catch {
    users.value = []
  } finally {
    loading.value = false
  }
}

function resetForm() {
  formData.username = ''
  formData.password = ''
  formData.display_name = ''
  formData.role = 'trader'
  formData.department = ''
  formData.is_active = true
  editingId.value = null
  formRef.value?.resetFields()
}

function openCreateModal() {
  isEdit.value = false
  resetForm()
  modalVisible.value = true
}

function openEditModal(record: AdminUser) {
  isEdit.value = true
  editingId.value = record.id
  formData.username = record.username
  formData.password = ''
  formData.display_name = record.display_name
  formData.role = record.role
  formData.department = record.department || ''
  formData.is_active = record.is_active
  modalVisible.value = true
}

async function handleSubmit() {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }

  submitting.value = true
  try {
    const payload: Record<string, any> = {
      display_name: formData.display_name,
      role: formData.role,
      department: formData.department || undefined,
    }

    if (formData.password) {
      payload.password = formData.password
    }

    if (isEdit.value) {
      payload.is_active = formData.is_active
      await api.put(`/api/admin/users/${editingId.value}`, payload)
      message.success('更新成功')
    } else {
      payload.username = formData.username
      payload.password = formData.password
      await api.post('/api/admin/users', payload)
      message.success('创建成功')
    }

    modalVisible.value = false
    resetForm()
    fetchUsers()
  } catch (e: any) {
    message.error(e?.response?.data?.detail || (isEdit.value ? '更新失败' : '创建失败'))
  } finally {
    submitting.value = false
  }
}

async function deleteUser(id: string) {
  try {
    await api.delete(`/api/admin/users/${id}`)
    message.success('删除成功')
    fetchUsers()
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '删除失败')
  }
}

onMounted(fetchUsers)
</script>
