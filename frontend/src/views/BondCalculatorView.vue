<template>
  <div class="bond-calculator-view">
    <a-card class="rounded-lg mb-6">
      <template #title>
        <div class="flex items-center gap-2">
          <CalculatorOutlined class="text-blue-500" />
          <span class="text-lg font-semibold">债券计算器</span>
        </div>
      </template>

      <a-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        layout="vertical"
        @finish="handleCalculate"
      >
        <a-row :gutter="24">
          <a-col :xs="24" :sm="12" :lg="8">
            <a-form-item label="面值 (元)" name="face_value">
              <a-input-number
                v-model:value="formData.face_value"
                :min="0.01"
                :precision="4"
                placeholder="请输入面值"
                style="width: 100%"
                @blur="validateField('face_value')"
              />
            </a-form-item>
          </a-col>

          <a-col :xs="24" :sm="12" :lg="8">
            <a-form-item label="票息率 (%)" name="coupon_rate">
              <a-input-number
                v-model:value="formData.coupon_rate"
                :min="0"
                :max="100"
                :precision="4"
                placeholder="请输入票息率"
                style="width: 100%"
                @blur="validateField('coupon_rate')"
              />
            </a-form-item>
          </a-col>

          <a-col :xs="24" :sm="12" :lg="8">
            <a-form-item label="付息频率" name="payment_frequency">
              <a-select
                v-model:value="formData.payment_frequency"
                placeholder="请选择付息频率"
                style="width: 100%"
              >
                <a-select-option :value="1">每年付息 (1次/年)</a-select-option>
                <a-select-option :value="2">半年付息 (2次/年)</a-select-option>
                <a-select-option :value="4">每季付息 (4次/年)</a-select-option>
                <a-select-option :value="12">每月付息 (12次/年)</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>

          <a-col :xs="24" :sm="12" :lg="8">
            <a-form-item label="结算日" name="settlement_date">
              <a-date-picker
                v-model:value="formData.settlement_date"
                :disabled-date="disabledSettlementDate"
                placeholder="请选择结算日"
                style="width: 100%"
                @change="handleDateChange"
              />
            </a-form-item>
          </a-col>

          <a-col :xs="24" :sm="12" :lg="8">
            <a-form-item label="到期日" name="maturity_date">
              <a-date-picker
                v-model:value="formData.maturity_date"
                :disabled-date="disabledMaturityDate"
                placeholder="请选择到期日"
                style="width: 100%"
                @change="handleDateChange"
              />
            </a-form-item>
          </a-col>

          <a-col :xs="24" :sm="12" :lg="8">
            <a-form-item label="计算模式">
              <a-radio-group v-model:value="calcMode" button-style="solid" style="width: 100%">
                <a-radio-button value="price" style="width: 50%">指定净价求收益</a-radio-button>
                <a-radio-button value="yield" style="width: 50%">指定收益求净价</a-radio-button>
              </a-radio-group>
            </a-form-item>
          </a-col>

          <a-col :xs="24" :sm="12" :lg="8" v-if="calcMode === 'price'">
            <a-form-item label="净价 (元)" name="clean_price">
              <a-input-number
                v-model:value="formData.clean_price"
                :min="0.01"
                :precision="4"
                placeholder="请输入净价"
                style="width: 100%"
                @blur="validateField('clean_price')"
              />
            </a-form-item>
          </a-col>

          <a-col :xs="24" :sm="12" :lg="8" v-if="calcMode === 'yield'">
            <a-form-item label="收益率 (%)" name="yield_rate">
              <a-input-number
                v-model:value="formData.yield_rate"
                :min="-99"
                :max="1000"
                :precision="4"
                placeholder="请输入收益率"
                style="width: 100%"
                @blur="validateField('yield_rate')"
              />
            </a-form-item>
          </a-col>
        </a-row>

        <a-form-item>
          <a-space>
            <a-button type="primary" html-type="submit" :loading="loading">
              <template #icon><CalculatorOutlined /></template>
              开始计算
            </a-button>
            <a-button @click="handleReset">
              <template #icon><ReloadOutlined /></template>
              重置
            </a-button>
          </a-space>
        </a-form-item>
      </a-form>
    </a-card>

    <a-card v-if="result" class="rounded-lg mb-6">
      <template #title>
        <div class="flex items-center gap-2">
          <LineChartOutlined class="text-green-500" />
          <span class="text-lg font-semibold">计算结果</span>
        </div>
      </template>

      <a-row :gutter="24">
        <a-col :xs="12" :sm="8" :lg="4">
          <div class="result-item">
            <div class="result-label">净价</div>
            <div class="result-value text-blue-600">{{ formatPrice(result.clean_price) }}</div>
          </div>
        </a-col>
        <a-col :xs="12" :sm="8" :lg="4">
          <div class="result-item">
            <div class="result-label">到期收益率</div>
            <div class="result-value text-blue-600">{{ formatYield(result.yield_rate * 100) }}</div>
          </div>
        </a-col>
        <a-col :xs="12" :sm="8" :lg="4">
          <div class="result-item">
            <div class="result-label">应计利息</div>
            <div class="result-value text-orange-500">{{ formatPrice(result.accrued_interest) }}</div>
          </div>
        </a-col>
        <a-col :xs="12" :sm="8" :lg="4">
          <div class="result-item">
            <div class="result-label">全价</div>
            <div class="result-value text-green-600">{{ formatPrice(result.dirty_price) }}</div>
          </div>
        </a-col>
        <a-col :xs="12" :sm="8" :lg="4">
          <div class="result-item">
            <div class="result-label">麦考利久期</div>
            <div class="result-value tabular-nums">{{ formatPrice(result.macaulay_duration) }} 年</div>
          </div>
        </a-col>
        <a-col :xs="12" :sm="8" :lg="4">
          <div class="result-item">
            <div class="result-label">修正久期</div>
            <div class="result-value tabular-nums">{{ formatPrice(result.modified_duration) }}</div>
          </div>
        </a-col>
      </a-row>

      <a-divider />

      <a-row :gutter="24">
        <a-col :xs="12" :sm="8">
          <div class="result-item-secondary">
            <div class="result-label">剩余期限</div>
            <div class="result-value-secondary">{{ formatPrice(result.years_to_maturity) }} 年</div>
          </div>
        </a-col>
        <a-col :xs="12" :sm="8">
          <div class="result-item-secondary">
            <div class="result-label">面值</div>
            <div class="result-value-secondary">{{ formatPrice(result.face_value) }}</div>
          </div>
        </a-col>
        <a-col :xs="12" :sm="8">
          <div class="result-item-secondary">
            <div class="result-label">票面利率</div>
            <div class="result-value-secondary">{{ formatYield(result.coupon_rate * 100) }}</div>
          </div>
        </a-col>
      </a-row>
    </a-card>

    <a-card v-if="result && result.cash_flows && result.cash_flows.length > 0" class="rounded-lg">
      <template #title>
        <div class="flex items-center gap-2">
          <TableOutlined class="text-purple-500" />
          <span class="text-lg font-semibold">现金流明细</span>
          <a-tag color="blue" class="ml-2">共 {{ result.cash_flows.length }} 期</a-tag>
        </div>
      </template>

      <a-table
        :data-source="result.cash_flows"
        :columns="cashFlowColumns"
        :pagination="{ pageSize: 10, showSizeChanger: true }"
        :scroll="{ x: 'max-content' }"
        :row-key="(_, index) => index"
        size="middle"
      >
        <template #bodyCell="{ column, record, index }">
          <template v-if="column.key === 'period'">
            <span class="font-medium">第 {{ index + 1 }} 期</span>
          </template>
          <template v-else-if="column.key === 'date'">
            {{ formatDate(record.date) }}
          </template>
          <template v-else-if="column.key === 'coupon'">
            <span class="tabular-nums text-orange-500">{{ formatPrice(record.coupon) }}</span>
          </template>
          <template v-else-if="column.key === 'principal'">
            <span class="tabular-nums text-blue-500">{{ formatPrice(record.principal) }}</span>
          </template>
          <template v-else-if="column.key === 'total'">
            <span class="tabular-nums font-semibold text-green-600">{{ formatPrice(record.total) }}</span>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { message } from 'ant-design-vue'
import type { FormInstance, Rule } from 'ant-design-vue'
import dayjs from 'dayjs'
import {
  CalculatorOutlined,
  ReloadOutlined,
  LineChartOutlined,
  TableOutlined,
} from '@ant-design/icons-vue'
import api from '../api'
import { formatPrice, formatYield, formatDate } from '../utils/format'

interface BondCalcResult {
  face_value: number
  coupon_rate: number
  payment_frequency: number
  settlement_date: string
  maturity_date: string
  clean_price: number
  yield_rate: number
  accrued_interest: number
  dirty_price: number
  macaulay_duration: number
  modified_duration: number
  years_to_maturity: number
  cash_flows: Array<{
    date: string
    coupon: number
    principal: number
    total: number
  }>
}

const formRef = ref<FormInstance>()
const loading = ref(false)
const calcMode = ref<'price' | 'yield'>('price')
const result = ref<BondCalcResult | null>(null)

const cashFlowColumns = [
  { title: '期数', key: 'period', width: 100, align: 'center' },
  { title: '付息日', key: 'date', width: 140 },
  { title: '票息 (元)', key: 'coupon', width: 140, align: 'right' },
  { title: '本金 (元)', key: 'principal', width: 140, align: 'right' },
  { title: '合计 (元)', key: 'total', width: 160, align: 'right' },
]

const formData = reactive({
  face_value: 100,
  coupon_rate: 3,
  payment_frequency: 1,
  settlement_date: dayjs() as dayjs.Dayjs | null,
  maturity_date: dayjs().add(5, 'year') as dayjs.Dayjs | null,
  clean_price: 100 as number | null,
  yield_rate: 3 as number | null,
})

const rules: Record<string, Rule[]> = {
  face_value: [
    { required: true, message: '请输入面值', trigger: 'blur' },
    { type: 'number', min: 0.01, message: '面值必须大于0', trigger: 'blur' },
  ],
  coupon_rate: [
    { required: true, message: '请输入票息率', trigger: 'blur' },
    { type: 'number', min: 0, max: 100, message: '票息率必须在0-100之间', trigger: 'blur' },
  ],
  payment_frequency: [
    { required: true, message: '请选择付息频率', trigger: 'change' },
  ],
  settlement_date: [
    { required: true, message: '请选择结算日', trigger: 'change' },
  ],
  maturity_date: [
    { required: true, message: '请选择到期日', trigger: 'change' },
  ],
  clean_price: [
    {
      required: computed(() => calcMode.value === 'price'),
      message: '请输入净价',
      trigger: 'blur',
    },
    { type: 'number', min: 0.01, message: '净价必须大于0', trigger: 'blur' },
  ],
  yield_rate: [
    {
      required: computed(() => calcMode.value === 'yield'),
      message: '请输入收益率',
      trigger: 'blur',
    },
    { type: 'number', min: -99, message: '收益率不能小于-99%', trigger: 'blur' },
  ],
}

function disabledSettlementDate(current: dayjs.Dayjs) {
  if (!current) return false
  if (formData.maturity_date) {
    return current.isAfter(formData.maturity_date, 'day')
  }
  return false
}

function disabledMaturityDate(current: dayjs.Dayjs) {
  if (!current) return false
  if (formData.settlement_date) {
    return current.isBefore(formData.settlement_date, 'day')
  }
  return false
}

function handleDateChange() {
  if (formData.settlement_date && formData.maturity_date) {
    if (formData.settlement_date.isAfter(formData.maturity_date, 'day')) {
      formData.maturity_date = formData.settlement_date.add(1, 'day')
    }
  }
}

function validateField(field: string) {
  formRef.value?.validateFields([field]).catch(() => {})
}

async function handleCalculate() {
  try {
    await formRef.value?.validate()
  } catch {
    message.error('请检查表单输入是否正确')
    return
  }

  if (!formData.settlement_date || !formData.maturity_date) {
    message.error('请选择结算日和到期日')
    return
  }

  loading.value = true
  try {
    const requestData = {
      face_value: formData.face_value,
      coupon_rate: formData.coupon_rate / 100,
      payment_frequency: formData.payment_frequency,
      settlement_date: formData.settlement_date.format('YYYY-MM-DD'),
      maturity_date: formData.maturity_date.format('YYYY-MM-DD'),
      clean_price: calcMode.value === 'price' ? formData.clean_price : null,
      yield_rate: calcMode.value === 'yield' ? (formData.yield_rate ?? 0) / 100 : null,
    }

    const res = await api.post<BondCalcResult>('/api/bonds/calculate', requestData)
    result.value = res.data
    message.success('计算成功')
  } catch (err: any) {
    const detail = err.response?.data?.detail
    if (detail) {
      message.error(detail)
    }
  } finally {
    loading.value = false
  }
}

function handleReset() {
  formData.face_value = 100
  formData.coupon_rate = 3
  formData.payment_frequency = 1
  formData.settlement_date = dayjs()
  formData.maturity_date = dayjs().add(5, 'year')
  formData.clean_price = 100
  formData.yield_rate = 3
  calcMode.value = 'price'
  result.value = null
  formRef.value?.clearValidate()
}
</script>

<style scoped>
.result-item {
  @apply p-4 bg-gray-50 rounded-lg text-center;
}

.result-item + .result-item {
  @apply mt-4 lg:mt-0;
}

.result-label {
  @apply text-sm text-gray-500 mb-1;
}

.result-value {
  @apply text-2xl font-bold tabular-nums;
}

.result-item-secondary {
  @apply p-3 bg-white rounded-lg text-center border border-gray-100;
}

.result-value-secondary {
  @apply text-lg font-semibold tabular-nums text-gray-700;
}

:deep(.ant-form-item) {
  margin-bottom: 16px;
}
</style>
