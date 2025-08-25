/**
 * WebSocket 服务，用于接收实时进度更新
 */

export interface WebSocketMessage {
  type: string
  batch_execution_id?: number
  data?: any
  timestamp?: string
  message?: string
}

export interface BatchExecutionUpdate {
  status: string
  success_count: number
  failed_count: number
  running_count: number
  pending_count: number
  total_count: number
  completed_at?: string
  updated_at?: string
}

class WebSocketService {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private heartbeatInterval: number | null = null
  private messageHandlers: Map<string, ((data: any) => void)[]> = new Map()
  private subscriptions: Set<number> = new Set()

  constructor() {
    this.connect()
  }

  /**
   * 连接到 WebSocket 服务器
   */
  private connect() {
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const host = window.location.hostname
      const port = '8000' // 后端端口
      const wsUrl = `${protocol}//${host}:${port}/ws`
      
      this.ws = new WebSocket(wsUrl)
      
      this.ws.onopen = () => {
        console.log('WebSocket 连接已建立')
        this.reconnectAttempts = 0
        this.startHeartbeat()
        
        // 重新订阅之前的批量执行任务
        this.subscriptions.forEach(batchId => {
          this.subscribeToBatch(batchId)
        })
      }
      
      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          this.handleMessage(message)
        } catch (error) {
          console.error('解析 WebSocket 消息失败:', error)
        }
      }
      
      this.ws.onclose = () => {
        console.log('WebSocket 连接已关闭')
        this.stopHeartbeat()
        this.attemptReconnect()
      }
      
      this.ws.onerror = (error) => {
        console.error('WebSocket 连接错误:', error)
      }
      
    } catch (error) {
      console.error('创建 WebSocket 连接失败:', error)
      this.attemptReconnect()
    }
  }

  /**
   * 尝试重新连接
   */
  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      console.log(`尝试重新连接 WebSocket (${this.reconnectAttempts}/${this.maxReconnectAttempts})`)
      
      setTimeout(() => {
        this.connect()
      }, this.reconnectDelay * this.reconnectAttempts)
    } else {
      console.error('WebSocket 重连失败，已达到最大重试次数')
    }
  }

  /**
   * 开始心跳检测
   */
  private startHeartbeat() {
    this.heartbeatInterval = window.setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping' }))
      }
    }, 30000) // 每30秒发送一次心跳
  }

  /**
   * 停止心跳检测
   */
  private stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval)
      this.heartbeatInterval = null
    }
  }

  /**
   * 处理接收到的消息
   */
  private handleMessage(message: WebSocketMessage) {
    console.log('收到 WebSocket 消息:', message)
    
    const handlers = this.messageHandlers.get(message.type)
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(message)
        } catch (error) {
          console.error('处理 WebSocket 消息失败:', error)
        }
      })
    }
  }

  /**
   * 订阅特定批量执行任务的进度更新
   */
  subscribeToBatch(batchExecutionId: number) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'subscribe_batch',
        batch_execution_id: batchExecutionId
      }))
      this.subscriptions.add(batchExecutionId)
    }
  }

  /**
   * 取消订阅特定批量执行任务
   */
  unsubscribeFromBatch(batchExecutionId: number) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'unsubscribe_batch',
        batch_execution_id: batchExecutionId
      }))
      this.subscriptions.delete(batchExecutionId)
    }
  }

  /**
   * 注册消息处理器
   */
  onMessage(type: string, handler: (data: any) => void) {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, [])
    }
    this.messageHandlers.get(type)!.push(handler)
  }

  /**
   * 移除消息处理器
   */
  offMessage(type: string, handler: (data: any) => void) {
    const handlers = this.messageHandlers.get(type)
    if (handlers) {
      const index = handlers.indexOf(handler)
      if (index > -1) {
        handlers.splice(index, 1)
      }
    }
  }

  /**
   * 断开连接
   */
  disconnect() {
    this.stopHeartbeat()
    this.subscriptions.clear()
    this.messageHandlers.clear()
    
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  /**
   * 检查连接状态
   */
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN
  }
}

// 创建全局 WebSocket 服务实例
export const websocketService = new WebSocketService()

// 在页面卸载时断开连接
window.addEventListener('beforeunload', () => {
  websocketService.disconnect()
})

// Vue 3 Composition API Hook
import { ref, onUnmounted } from 'vue'

export function useWebSocket() {
  const isConnected = ref(false)
  const messageHandlers = new Map<string, (data: any) => void>()

  // 连接状态监听
  const checkConnection = () => {
    isConnected.value = websocketService.isConnected()
  }

  // 定期检查连接状态
  const connectionChecker = setInterval(checkConnection, 1000)

  const connect = () => {
    checkConnection()
  }

  const disconnect = () => {
    websocketService.disconnect()
    isConnected.value = false
  }

  const onMessage = (handler: (data: any) => void) => {
    // 监听所有类型的消息
    const messageHandler = (message: WebSocketMessage) => {
      handler(message)
    }
    
    websocketService.onMessage('import_progress', messageHandler)
    websocketService.onMessage('batch_execution_update', messageHandler)
    websocketService.onMessage('batch_execution_list_update', messageHandler)
    
    // 保存处理器引用以便清理
    messageHandlers.set('all', messageHandler)
  }

  const subscribeToBatch = (batchId: number) => {
    websocketService.subscribeToBatch(batchId)
  }

  const unsubscribeFromBatch = (batchId: number) => {
    websocketService.unsubscribeFromBatch(batchId)
  }

  // 组件卸载时清理
  onUnmounted(() => {
    clearInterval(connectionChecker)
    
    // 清理消息处理器
    messageHandlers.forEach((handler, type) => {
      websocketService.offMessage('import_progress', handler)
      websocketService.offMessage('batch_execution_update', handler)
      websocketService.offMessage('batch_execution_list_update', handler)
    })
    messageHandlers.clear()
  })

  return {
    isConnected,
    connect,
    disconnect,
    onMessage,
    subscribeToBatch,
    unsubscribeFromBatch
  }
} 