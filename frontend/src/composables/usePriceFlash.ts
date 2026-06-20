import { ref, watch } from 'vue'

export type PriceDirection = 'up' | 'down' | 'none'

export function usePriceFlash() {
  const flashMap = ref<Map<string, PriceDirection>>(new Map())
  const timers = new Map<string, ReturnType<typeof setTimeout>>()

  function triggerFlash(key: string, direction: PriceDirection) {
    if (direction === 'none') return

    const existingTimer = timers.get(key)
    if (existingTimer) {
      clearTimeout(existingTimer)
    }

    flashMap.value.set(key, direction)

    const timer = setTimeout(() => {
      flashMap.value.delete(key)
      timers.delete(key)
    }, 800)

    timers.set(key, timer)
  }

  function compareAndFlash(
    key: string,
    currentValue: number | undefined | null,
    previousValue: number | undefined | null
  ): PriceDirection {
    if (currentValue == null || previousValue == null || currentValue === previousValue) {
      return 'none'
    }
    const direction: PriceDirection = currentValue > previousValue ? 'up' : 'down'
    triggerFlash(key, direction)
    return direction
  }

  function getFlashClass(key: string): string {
    const dir = flashMap.value.get(key)
    if (dir === 'up') return 'price-flash-up'
    if (dir === 'down') return 'price-flash-down'
    return ''
  }

  function clearAll() {
    timers.forEach((t) => clearTimeout(t))
    timers.clear()
    flashMap.value.clear()
  }

  return {
    flashMap,
    triggerFlash,
    compareAndFlash,
    getFlashClass,
    clearAll,
  }
}
