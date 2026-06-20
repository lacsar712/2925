import { useMessageCenter } from './useMessageCenter'

export function useMessageExamples() {
  const {
    sendAnnouncement,
    sendMarketMovement,
    sendPriceAlert,
    sendAdminBroadcast,
  } = useMessageCenter()

  function exampleSendAnnouncement() {
    return sendAnnouncement(
      '系统维护通知',
      '系统将于本周末（6月22日）凌晨2:00-4:00进行例行维护，届时部分功能可能暂时无法使用，请提前做好相关安排。',
      { priority: 'high', maintenance_type: 'routine' }
    )
  }

  function exampleSendMarketMovement(bondId: string, bondName: string, changePercent: number) {
    const direction = changePercent > 0 ? '上涨' : '下跌'
    return sendMarketMovement(
      `行情异动：${bondName} ${direction} ${Math.abs(changePercent).toFixed(2)}%`,
      `${bondName} 价格出现大幅${direction}，当前变动幅度为 ${changePercent.toFixed(2)}%，请关注。`,
      bondId,
      { change_percent: changePercent, bond_id: bondId }
    )
  }

  function exampleSendPriceAlert(
    bondId: string,
    bondName: string,
    alertType: 'yield' | 'net_price',
    condition: 'above' | 'below',
    actualValue: number,
    threshold: number
  ) {
    const typeLabel = alertType === 'yield' ? '收益率' : '净价'
    const conditionLabel = condition === 'above' ? '高于' : '低于'
    const unit = alertType === 'yield' ? '%' : '元'

    return sendPriceAlert(
      `价格预警：${bondName} ${typeLabel}${conditionLabel}阈值`,
      `${bondName} 的${typeLabel}当前为 ${actualValue.toFixed(4)}${unit}，已${conditionLabel}设定阈值 ${threshold.toFixed(4)}${unit}。`,
      bondId,
      {
        alert_type: alertType,
        condition,
        actual_value: actualValue,
        threshold,
        bond_id: bondId,
      }
    )
  }

  function exampleSendAdminBroadcast() {
    return sendAdminBroadcast(
      '重要通知：新增功能上线',
      '债券对比分析功能已正式上线，支持最多5只债券的多维度对比分析。访问「债券对比」页面体验新功能。',
      { feature: 'bond_compare', version: 'v2.1.0' }
    )
  }

  return {
    exampleSendAnnouncement,
    exampleSendMarketMovement,
    exampleSendPriceAlert,
    exampleSendAdminBroadcast,
  }
}
