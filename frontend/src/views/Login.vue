<template>
  <div class="login-page min-h-screen flex items-center justify-center">
    <div class="login-card w-full max-w-[400px] rounded-xl shadow-xl bg-white p-8">
      <div class="text-center mb-8">
        <h1 class="text-2xl font-bold text-gray-800 mb-2">BondView</h1>
        <p class="text-gray-500 text-sm">债券行情聚合系统</p>
      </div>
      <a-form
        :model="formState"
        layout="vertical"
        @finish="handleLogin"
      >
        <a-form-item
          label="用户名"
          name="username"
          :rules="[{ required: true, message: '请输入用户名' }]"
        >
          <a-input
            v-model:value="formState.username"
            placeholder="请输入用户名"
            size="large"
            allow-clear
          />
        </a-form-item>
        <a-form-item
          label="密码"
          name="password"
          :rules="[{ required: true, message: '请输入密码' }]"
        >
          <a-input-password
            v-model:value="formState.password"
            placeholder="请输入密码"
            size="large"
            allow-clear
          />
        </a-form-item>
        <a-form-item class="mb-0">
          <a-button
            type="primary"
            html-type="submit"
            block
            size="large"
            :loading="loading"
            class="mt-2"
          >
            登录
          </a-button>
        </a-form-item>
      </a-form>

    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const formState = reactive({
  username: '',
  password: '',
})

const loading = ref(false)

async function handleLogin() {
  loading.value = true
  try {
    await authStore.login(formState.username, formState.password)
    message.success('登录成功')
    router.push('/dashboard')
  } catch (err) {
    message.error('登录失败，请检查用户名和密码')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
}
</style>
