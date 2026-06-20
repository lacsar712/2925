import { useMessageCenterStore, type MessageType, type MessageLink } from '../stores/messageCenter'

export function useMessageCenter() {
  const messageStore = useMessageCenterStore()

  function sendMessage(data: {
    type: MessageType
    title: string
    content: string
    link?: MessageLink
    metadata?: Record<string, unknown>
  }) {
    return messageStore.pushMessage(data)
  }

  function sendAnnouncement(title: string, content: string, metadata?: Record<string, unknown>) {
    return sendMessage({
      type: 'announcement',
      title,
      content,
      metadata,
    })
  }

  function sendMarketMovement(
    title: string,
    content: string,
    bondId?: string,
    metadata?: Record<string, unknown>
  ) {
    const link: MessageLink | undefined = bondId
      ? {
          type: 'bond_detail',
          params: { id: bondId },
        }
      : undefined

    return sendMessage({
      type: 'market_movement',
      title,
      content,
      link,
      metadata,
    })
  }

  function sendPriceAlert(
    title: string,
    content: string,
    bondId?: string,
    metadata?: Record<string, unknown>
  ) {
    const link: MessageLink | undefined = bondId
      ? {
          type: 'bond_detail',
          params: { id: bondId },
        }
      : {
          type: 'alert_list',
          params: {},
        }

    return sendMessage({
      type: 'price_alert',
      title,
      content,
      link,
      metadata,
    })
  }

  function sendAdminBroadcast(title: string, content: string, metadata?: Record<string, unknown>) {
    return sendMessage({
      type: 'admin_broadcast',
      title,
      content,
      metadata,
    })
  }

  return {
    sendMessage,
    sendAnnouncement,
    sendMarketMovement,
    sendPriceAlert,
    sendAdminBroadcast,
  }
}
