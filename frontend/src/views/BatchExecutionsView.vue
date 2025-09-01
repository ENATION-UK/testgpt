<template>
  <div class="batch-executions">
    <div class="page-header">
      <h2>批量执行任务</h2>
      <div class="header-actions">
        <el-tag 
          :type="websocketService.isConnected() ? 'success' : 'danger'"
          size="small"
          style="margin-right: 10px;"
        >
          {{ websocketService.isConnected() ? '实时连接' : '连接断开' }}
        </el-tag>
        <el-button type="primary" @click="refreshBatchExecutions">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <el-card>
      <el-table
        v-loading="loading"
        :data="batchExecutions"
        style="width: 100%"
      >
        <el-table-column prop="name" label="任务名称" min-width="200" />
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getBatchStatusType(row.status)">
              {{ getBatchStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="进度" width="150">
          <template #default="{ row }">
            <el-progress
              :percentage="calculateProgress(row)"
              :status="getProgressStatus(row.status)"
              :show-text="true"
            />
          </template>
        </el-table-column>
        <el-table-column label="统计信息" width="200">
          <template #default="{ row }">
            <div class="stats-info">
              <span class="stat-item">
                <el-tag type="success">{{ row.success_count }}</el-tag>
                <span>成功</span>
              </span>
              <span class="stat-item">
                <el-tag type="danger">{{ row.failed_count }}</el-tag>
                <span>失败</span>
              </span>
              <span class="stat-item">
                <el-tag type="info">{{ row.total_count }}</el-tag>
                <span>总计</span>
              </span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="started_at" label="开始时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.started_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="completed_at" label="完成时间" width="180">
          <template #default="{ row }">
            {{ row.completed_at ? formatDate(row.completed_at) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <!-- 执行按钮 - 只在pending状态显示 -->
              <el-button 
                v-if="row.status === 'pending'" 
                size="small" 
                type="success" 
                @click="startBatchExecution(row)"
                :loading="(row as any)[`starting_${row.id}`]"
              >
                <el-icon><VideoPlay /></el-icon>
                执行
              </el-button>
              
              <!-- 停止按钮 - 只在running状态显示 -->
              <el-button 
                v-if="row.status === 'running'" 
                size="small" 
                type="danger" 
                @click="stopBatchExecution(row)"
                :loading="(row as any)[`stopping_${row.id}`]"
              >
                <el-icon><VideoPause /></el-icon>
                停止
              </el-button>
              
              <!-- 查看详情按钮 -->
              <el-button size="small" type="primary" @click="viewBatchExecution(row)">
                查看详情
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页组件 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 批量执行任务详情对话框 -->
    <el-dialog
      v-model="showDetailDialog"
      :title="`批量执行任务详情 - ${selectedBatchExecution?.name || ''}`"
      width="80%"
      :before-close="handleDetailDialogClose"
    >
      <div v-if="selectedBatchExecution" class="batch-execution-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="任务名称">{{ selectedBatchExecution.name }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getBatchStatusType(selectedBatchExecution.status)">
              {{ getBatchStatusLabel(selectedBatchExecution.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="开始时间">{{ formatDate(selectedBatchExecution.started_at) }}</el-descriptions-item>
          <el-descriptions-item label="完成时间">{{ selectedBatchExecution.completed_at ? formatDate(selectedBatchExecution.completed_at) : '-' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatDate(selectedBatchExecution.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ formatDate(selectedBatchExecution.updated_at) }}</el-descriptions-item>
          <el-descriptions-item label="总用例数">{{ selectedBatchExecution.total_count }}</el-descriptions-item>
          <el-descriptions-item label="成功数">{{ selectedBatchExecution.success_count }}</el-descriptions-item>
          <el-descriptions-item label="失败数">{{ selectedBatchExecution.failed_count }}</el-descriptions-item>
          <el-descriptions-item label="运行中">{{ selectedBatchExecution.running_count }}</el-descriptions-item>
          <el-descriptions-item label="待执行">{{ selectedBatchExecution.pending_count }}</el-descriptions-item>
          <el-descriptions-item label="总耗时">{{ formatDuration(selectedBatchExecution.total_duration) }}</el-descriptions-item>
          <el-descriptions-item label="浏览器模式">
            <el-tag :type="selectedBatchExecution.headless ? 'info' : 'warning'">
              {{ selectedBatchExecution.headless ? '无头模式' : '有头模式' }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <h3 style="margin-top: 20px;">测试用例执行详情</h3>
        <el-table
          :data="selectedBatchExecution.test_cases"
          style="width: 100%"
          max-height="400"
        >
          <el-table-column prop="test_case_name" label="测试用例" min-width="200" />
          <el-table-column prop="status" label="状态" width="120">
            <template #default="{ row }">
              <el-tag :type="getTestCaseStatusType(row.status)">
                {{ getTestCaseStatusLabel(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="overall_status" label="整体状态" width="120">
            <template #default="{ row }">
              <el-tag v-if="row.overall_status" :type="getOverallStatusType(row.overall_status)">
                {{ row.overall_status }}
              </el-tag>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="started_at" label="开始时间" width="180">
            <template #default="{ row }">
              {{ row.started_at ? formatDate(row.started_at) : '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="completed_at" label="完成时间" width="180">
            <template #default="{ row }">
              {{ row.completed_at ? formatDate(row.completed_at) : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button 
                size="small" 
                type="primary" 
                @click="viewTestCaseExecution(row.execution_id)"
              >
                查看详情
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh, VideoPlay, VideoPause } from '@element-plus/icons-vue'
import { batchExecutionApi } from '@/services/api'
import { websocketService } from '@/services/websocket'
import type { BatchExecution } from '@/types/api'

const router = useRouter()
const loading = ref(false)
const batchExecutions = ref<BatchExecution[]>([])
const showDetailDialog = ref(false)
const selectedBatchExecution = ref<BatchExecution | null>(null)

// 分页相关
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// WebSocket 消息处理器
let batchUpdateHandler: ((message: any) => void) | null = null

const loadBatchExecutions = async () => {
  loading.value = true
  try {
    // 正确传递查询参数
    const params = {
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value
    }
    
    const data = await batchExecutionApi.getList(params)
    batchExecutions.value = data
    
    // 注意：由于后端API没有返回总数，这里暂时使用当前页数据长度
    // 在实际项目中，后端应该返回包含总数的分页响应
    total.value = data.length + params.skip
    
    // 订阅所有运行中的批量执行任务
    data.forEach(task => {
      if (task.status === 'running') {
        websocketService.subscribeToBatch(task.id)
      }
    })
  } catch (error) {
    ElMessage.error('加载批量执行任务失败')
  } finally {
    loading.value = false
  }
}

const refreshBatchExecutions = () => {
  currentPage.value = 1
  loadBatchExecutions()
}

const handleSizeChange = (newSize: number) => {
  pageSize.value = newSize
  currentPage.value = 1
  loadBatchExecutions()
}

const handleCurrentChange = (newPage: number) => {
  currentPage.value = newPage
  loadBatchExecutions()
}

const viewBatchExecution = (batchExecution: BatchExecution) => {
  router.push({
    name: 'batch-execution-detail',
    params: { id: batchExecution.id.toString() }
  })
}

const viewTestCaseExecution = (executionId: number) => {
  router.push({
    name: 'execution-detail',
    params: { executionId: executionId.toString() }
  })
}

const startBatchExecution = async (batchExecution: BatchExecution) => {
  try {
    // 使用Vue的响应式系统设置loading状态
    const loadingKey = `starting_${batchExecution.id}`
    if (!(loadingKey in batchExecution)) {
      (batchExecution as any)[loadingKey] = false
    }
    ;(batchExecution as any)[loadingKey] = true
    
    const response = await batchExecutionApi.start(batchExecution.id)
    if (response.success) {
      ElMessage.success('批量执行任务已启动')
      // 刷新列表
      await loadBatchExecutions()
    } else {
      ElMessage.error(response.message || '启动失败')
    }
  } catch (error) {
    ElMessage.error('启动批量执行任务失败')
  } finally {
    const loadingKey = `starting_${batchExecution.id}`
    ;(batchExecution as any)[loadingKey] = false
  }
}

const stopBatchExecution = async (batchExecution: BatchExecution) => {
  try {
    // 使用Vue的响应式系统设置loading状态
    const loadingKey = `stopping_${batchExecution.id}`
    if (!(loadingKey in batchExecution)) {
      (batchExecution as any)[loadingKey] = false
    }
    ;(batchExecution as any)[loadingKey] = true
    
    const response = await batchExecutionApi.stop(batchExecution.id)
    if (response.success) {
      ElMessage.success('批量执行任务已停止')
      // 刷新列表
      await loadBatchExecutions()
    } else {
      ElMessage.error(response.message || '停止失败')
    }
  } catch (error) {
    ElMessage.error('停止批量执行任务失败')
  } finally {
    const loadingKey = `stopping_${batchExecution.id}`
    ;(batchExecution as any)[loadingKey] = false
  }
}

const handleDetailDialogClose = () => {
  showDetailDialog.value = false
  // 取消订阅当前查看的批量执行任务
  if (selectedBatchExecution.value) {
    websocketService.unsubscribeFromBatch(selectedBatchExecution.value.id)
  }
  selectedBatchExecution.value = null
}

// WebSocket 消息处理函数
const handleBatchExecutionUpdate = (message: any) => {
  const { batch_execution_id, data } = message
  
  // 更新列表中的批量执行任务
  const index = batchExecutions.value.findIndex(task => task.id === batch_execution_id)
  if (index !== -1) {
    batchExecutions.value[index] = { ...batchExecutions.value[index], ...data }
  }
  
  // 如果当前查看的详情对话框是该任务，也更新详情
  if (selectedBatchExecution.value && selectedBatchExecution.value.id === batch_execution_id) {
    selectedBatchExecution.value = { ...selectedBatchExecution.value, ...data }
    
    // 如果任务已完成，取消订阅
    if (data.status !== 'running') {
      websocketService.unsubscribeFromBatch(batch_execution_id)
    }
  }
  
  // 如果任务已完成，从列表中移除订阅
  if (data.status !== 'running') {
    websocketService.unsubscribeFromBatch(batch_execution_id)
  }
}

const calculateProgress = (batchExecution: BatchExecution): number => {
  // 如果是pending状态，返回0进度
  if (batchExecution.status === 'pending') {
    return 0
  }
  
  const completed = batchExecution.success_count + batchExecution.failed_count
  const total = batchExecution.total_count
  if (total === 0) return 0
  return Math.round((completed / total) * 100)
}

const getBatchStatusType = (status: string): string => {
  const types: Record<string, string> = {
    pending: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'danger',
    cancelled: 'info'
  }
  return types[status] || 'info'
}

const getBatchStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    pending: '待执行',
    running: '运行中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消'
  }
  return labels[status] || status
}

const getProgressStatus = (status: string): string | undefined => {
  const statuses: Record<string, string | undefined> = {
    pending: undefined,
    completed: 'success',
    failed: 'exception',
    cancelled: 'warning'
  }
  return statuses[status]
}

const getTestCaseStatusType = (status: string): string => {
  const types: Record<string, string> = {
    pending: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'danger',
    cancelled: 'info'
  }
  return types[status] || 'info'
}

const getTestCaseStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    pending: '待执行',
    running: '运行中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消'
  }
  return labels[status] || status
}

const getOverallStatusType = (status: string): string => {
  const types: Record<string, string> = {
    PASSED: 'success',
    FAILED: 'danger',
    PARTIAL: 'warning'
  }
  return types[status] || 'info'
}

const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleString('zh-CN')
}

const formatDuration = (seconds: number): string => {
  if (seconds < 60) {
    return `${seconds.toFixed(1)}s`
  }
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return `${minutes}m ${remainingSeconds.toFixed(1)}s`
}

onMounted(() => {
  loadBatchExecutions()
  
  // 注册 WebSocket 消息处理器
  batchUpdateHandler = handleBatchExecutionUpdate
  websocketService.onMessage('batch_execution_update', batchUpdateHandler)
})

onUnmounted(() => {
  // 取消所有订阅
  batchExecutions.value.forEach(task => {
    if (task.status === 'running') {
      websocketService.unsubscribeFromBatch(task.id)
    }
  })
  
  // 移除 WebSocket 消息处理器
  if (batchUpdateHandler) {
    websocketService.offMessage('batch_execution_update', batchUpdateHandler)
  }
})
</script>

<style scoped>
.batch-executions {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
  padding: 20px 0;
}

.stats-info {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 5px;
}

.batch-execution-detail {
  max-height: 80vh;
  overflow-y: auto;
}

.action-buttons {
  display: flex;
  gap: 8px;
  align-items: center;
}

.action-buttons .el-button {
  flex-shrink: 0;
}
</style>