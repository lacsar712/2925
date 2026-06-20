import dayjs from 'dayjs'

export function formatPrice(val: number | null | undefined): string {
  if (val == null) return '--'
  return val.toFixed(4)
}

export function formatYield(val: number | null | undefined): string {
  if (val == null) return '--'
  return val.toFixed(4) + '%'
}

export function formatVolume(val: number | null | undefined): string {
  if (val == null) return '--'
  if (val >= 10000) return (val / 10000).toFixed(2) + '亿'
  return val.toFixed(2) + '万'
}

export function formatAmount(val: number | null | undefined): string {
  if (val == null) return '--'
  if (val >= 10000) return (val / 10000).toFixed(2) + '亿'
  return val.toFixed(2) + '万'
}

export function formatTime(val: string | null | undefined): string {
  if (!val) return '--'
  return dayjs(val).format('HH:mm:ss')
}

export function formatDateTime(val: string | null | undefined): string {
  if (!val) return '--'
  return dayjs(val).format('YYYY-MM-DD HH:mm:ss')
}

export function formatDate(val: string | null | undefined): string {
  if (!val) return '--'
  return dayjs(val).format('YYYY-MM-DD')
}

export function sourceTypeLabel(type: string): string {
  const map: Record<string, string> = {
    xbond: '银行间xBond',
    broker: '货币经纪',
    exchange: '交易所',
    swap: '收益互换',
    futures: '国债期货',
  }
  return map[type] || type
}

export function bondTypeColor(type: string): string {
  const map: Record<string, string> = {
    '国债': 'red',
    '政金债': 'blue',
    '企业债': 'orange',
    '公司债': 'purple',
    '可转债': 'green',
    '地方债': 'cyan',
    '同业存单': 'geekblue',
  }
  return map[type] || 'default'
}

export function directionLabel(dir: string): string {
  return dir === 'buy' ? '买入' : '卖出'
}

export function directionColor(dir: string): string {
  return dir === 'buy' ? '#ff4d4f' : '#52c41a'
}
