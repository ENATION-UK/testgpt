<template>
  <div class="excel-import-page">
    <div class="page-header">
      <h2>{{ $t('excelImport.title') }}</h2>
      <p>{{ $t('excelImport.description') }}</p>
    </div>

    <!-- 导入表单区域 -->
    <el-card v-if="!hasRunningTask" class="import-form-card">
      <template #header>
        <span>{{ $t('excelImport.selectFile') }}</span>
      </template>
      
      <!-- 导入模式选择 -->
      <div class="import-mode-section">
        <h3>{{ $t('excelImport.importMode') }}</h3>
        <el-radio-group v-model="importMode" class="mode-selector">
          <el-radio label="smart" size="large">
            <div class="mode-option">
              <div class="mode-title">🤖 {{ $t('excelImport.smartMode') }}</div>
              <div class="mode-desc">{{ $t('excelImport.smartModeDesc') }}</div>
            </div>
          </el-radio>
          <el-radio label="standard" size="large">
            <div class="mode-option">
              <div class="mode-title">📄 {{ $t('excelImport.standardMode') }}</div>
              <div class="mode-desc">{{ $t('excelImport.standardModeDesc') }}</div>
            </div>
          </el-radio>
        </el-radio-group>
        
        <!-- 模版下载区域 -->
        <div v-if="importMode === 'standard'" class="template-download">
          <el-alert
            :title="$t('excelImport.useStandardTemplate')"
            type="info"
            :description="$t('excelImport.templateDescription')"
            show-icon
            :closable="false"
          />
          <div class="template-actions">
            <el-button type="primary" @click="downloadTemplate" :loading="downloadingTemplate">
              <el-icon><Download /></el-icon>
              {{ $t('excelImport.downloadTemplate') }}
            </el-button>
            <el-button type="info" @click="viewTemplateSample">
              <el-icon><View /></el-icon>
              {{ $t('excelImport.viewSample') }}
            </el-button>
          </div>
        </div>
        
        <div v-else class="smart-mode-info">
          <el-alert
            :title="$t('excelImport.smartMode')"
            type="success"
            :description="$t('excelImport.smartModeDescription')"
            show-icon
            :closable="false"
          />
        </div>
      </div>

      <div class="upload-section">
        <el-upload
          ref="uploadRef"
          :auto-upload="false"
          :show-file-list="true"
          :limit="1"
          accept=".xlsx,.xls"
          :on-change="handleFileChange"
          :on-remove="handleFileRemove"
          drag
          class="upload-area"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            {{ $t('excelImport.dragFile') }}<em>{{ $t('excelImport.clickUpload') }}</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              {{ $t('excelImport.uploadTip') }}
            </div>
          </template>
        </el-upload>
      </div>

      <!-- 导入配置 -->
      <div v-if="selectedFile" class="import-config">
        <h3>{{ $t('excelImport.importConfig') }}</h3>
        <el-form :model="importOptions" label-width="120px">
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item :label="$t('excelImport.taskName')">
                <el-input v-model="taskName" :placeholder="$t('excelImport.taskNamePlaceholder')" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item :label="$t('excelImport.batchSize')">
                <el-input-number 
                  v-model="batchSize" 
                  :min="1" 
                  :max="100" 
                  :placeholder="$t('excelImport.batchSizePlaceholder')"
                />
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item :label="$t('excelImport.defaultStatus')">
                <el-select v-model="importOptions.defaultStatus" :placeholder="$t('excelImport.selectDefaultStatus')">
                  <el-option :label="$t('common.active')" value="active" />
                  <el-option :label="$t('common.inactive')" value="inactive" />
                  <el-option :label="$t('common.draft')" value="draft" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item :label="$t('excelImport.defaultPriority')">
                <el-select v-model="importOptions.defaultPriority" :placeholder="$t('excelImport.selectDefaultPriority')">
                  <el-option :label="$t('common.low')" value="low" />
                  <el-option :label="$t('common.medium')" value="medium" />
                  <el-option :label="$t('common.high')" value="high" />
                  <el-option :label="$t('common.critical')" value="critical" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item :label="$t('excelImport.defaultCategory')">
                <el-cascader
                  v-model="selectedCategoryId"
                  :options="categoryOptions"
                  :props="cascaderProps"
                  :placeholder="$t('excelImport.selectDefaultCategory')"
                  clearable
                  filterable
                  :loading="loadingCategories"
                />
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>

        <div class="action-buttons">
          <el-button type="primary" @click="startImport" :loading="starting">
            <el-icon><Upload /></el-icon>
            {{ $t('excelImport.startImport') }}
          </el-button>
          <el-button @click="clearFile">
            <el-icon><Delete /></el-icon>
            {{ $t('excelImport.clearFile') }}
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 正在运行任务提示 -->
    <el-card v-if="hasRunningTask && !currentTask" class="warning-card">
      <el-alert
        :title="$t('excelImport.taskInProgress')"
        :description="$t('excelImport.taskInProgressDescription')"
        type="warning"
        show-icon
        :closable="false"
      />
    </el-card>

    <!-- 进度显示区域 -->
    <el-card v-if="currentTask" class="progress-card">
      <template #header>
        <div class="task-header">
          <span>{{ $t('excelImport.importTask') }}: {{ currentTask.name }}</span>
          <el-tag :type="getStatusTagType(currentTask.status)">
            {{ getStatusText(currentTask.status) }}
          </el-tag>
        </div>
      </template>

      <!-- 总体进度 -->
      <div class="progress-section">
        <div class="progress-info">
          <h4>{{ $t('excelImport.overallProgress') }}</h4>
          <el-progress 
            :percentage="currentTask.progress_percentage" 
            :status="getProgressStatus(currentTask.status)"
            :stroke-width="20"
          />
          <div class="progress-text">
            {{ currentTask.processed_rows }} / {{ currentTask.total_rows }} {{ $t('excelImport.rows') }}
            ({{ Math.round(currentTask.progress_percentage) }}%)
          </div>
        </div>

        <!-- 批次进度 -->
        <div class="batch-info">
          <h4>{{ $t('excelImport.batchProgress') }}</h4>
          <el-progress 
            :percentage="getBatchProgress" 
            :stroke-width="15"
            :show-text="false"
          />
          <div class="batch-text">
            {{ $t('excelImport.batch') }} {{ currentTask.current_batch }} / {{ currentTask.total_batches }}
          </div>
        </div>
      </div>

      <!-- 统计信息 -->
      <div class="stats-section">
        <el-row :gutter="20">
          <el-col :span="6">
            <div class="stat-item success">
              <div class="stat-value">{{ currentTask.success_rows }}</div>
              <div class="stat-label">{{ $t('excelImport.successImport') }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-item error">
              <div class="stat-value">{{ currentTask.failed_rows }}</div>
              <div class="stat-label">{{ $t('excelImport.failedImport') }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-item">
              <div class="stat-value">{{ currentTask.total_rows }}</div>
              <div class="stat-label">{{ $t('excelImport.totalRows') }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-item">
              <div class="stat-value">{{ batchSize }}</div>
              <div class="stat-label">{{ $t('excelImport.batchSize') }}</div>
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- 错误信息 -->
      <div v-if="errorMessages.length > 0" class="error-section">
        <h4>{{ $t('excelImport.recentErrors') }}</h4>
        <div class="error-messages">
          <div v-for="(error, index) in errorMessages" :key="index" class="error-item">
            <el-icon><Warning /></el-icon>
            <span>{{ error }}</span>
          </div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="task-actions">
        <el-button 
          v-if="currentTask.status === 'running'" 
          type="danger" 
          @click="cancelTask"
          :loading="cancelling"
        >
          <el-icon><Close /></el-icon>
          {{ $t('excelImport.cancelTask') }}
        </el-button>
        <el-button 
          v-if="currentTask.status === 'completed'" 
          type="success" 
          @click="viewResults"
        >
          <el-icon><View /></el-icon>
          {{ $t('excelImport.viewResults') }}
        </el-button>
        <el-button @click="refreshTask">
          <el-icon><Refresh /></el-icon>
          {{ $t('common.refresh') }}
        </el-button>
      </div>
    </el-card>

    <!-- 历史任务列表 -->
    <el-card class="history-card">
      <template #header>
        <div class="history-header">
          <span>{{ $t('excelImport.importHistory') }}</span>
          <el-button type="primary" text @click="loadTasks">
            <el-icon><Refresh /></el-icon>
            {{ $t('common.refresh') }}
          </el-button>
        </div>
      </template>

      <el-table :data="taskHistory" v-loading="loadingHistory">
        <el-table-column prop="name" :label="$t('excelImport.taskName')" />
        <el-table-column prop="file_name" :label="$t('excelImport.fileName')" />
        <el-table-column prop="total_rows" :label="$t('excelImport.totalRows')" width="100" />
        <el-table-column prop="success_rows" :label="$t('common.success')" width="80" />
        <el-table-column prop="failed_rows" :label="$t('common.failed')" width="80" />
        <el-table-column prop="status" :label="$t('common.status')" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" :label="$t('common.created_at')" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column :label="$t('common.operation')" width="150">
          <template #default="{ row }">
            <el-button type="primary" text @click="viewTaskDetail(row)">
              {{ $t('excelImport.viewDetails') }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  UploadFilled, 
  Upload, 
  Delete, 
  Warning, 
  Close, 
  View, 
  Refresh,
  Download 
} from '@element-plus/icons-vue'

const { t } = useI18n()

// 导入API服务
import { importTaskApi, categoryApi } from '@/services/api'
import api from '@/services/api'
import { useWebSocket } from '@/services/websocket'
import type { Category } from '@/types/api'

// 接口定义
interface ImportOptions {
  defaultStatus: string
  defaultPriority: string
  defaultCategory: string
  selectedCategoryId?: number | null
}

interface ImportTask {
  id: number
  name: string
  file_name: string
  status: string
  total_rows: number
  processed_rows: number
  success_rows: number
  failed_rows: number
  current_batch: number
  total_batches: number
  progress_percentage: number
  created_at: string
}

// 响应式数据
const uploadRef = ref()
const selectedFile = ref<File | null>(null)
const starting = ref(false)
const cancelling = ref(false)
const loadingHistory = ref(false)
const hasRunningTask = ref(false)
const currentTask = ref<ImportTask | null>(null)
const taskHistory = ref<ImportTask[]>([])
const errorMessages = ref<string[]>([])
const importMode = ref('smart') // 导入模式：smart 或 standard
const downloadingTemplate = ref(false) // 下载模版状态
const categoryOptions = ref<Category[]>([]) // 分类选项
const loadingCategories = ref(false) // 加载分类状态

// 表单数据
const taskName = ref('')
const batchSize = ref(10)
const importOptions = ref<ImportOptions>({
  defaultStatus: 'active',
  defaultPriority: 'medium',
  defaultCategory: '导入'
})

// 分类选择
const selectedCategoryId = ref<number | null>(null)

// WebSocket连接
const { connect, disconnect, onMessage } = useWebSocket()

// 级联选择器配置
const cascaderProps = {
  value: 'id',
  label: 'name',
  children: 'children',
  checkStrictly: true, // 允许选择父分类
  emitPath: false
}

// 计算属性
const getBatchProgress = computed(() => {
  if (!currentTask.value || currentTask.value.total_batches === 0) return 0
  return (currentTask.value.current_batch / currentTask.value.total_batches) * 100
})

// 文件处理
const handleFileChange = (file: any) => {
  selectedFile.value = file.raw
  if (!taskName.value) {
    taskName.value = `导入任务_${file.name}_${new Date().toLocaleString()}`
  }
}

const handleFileRemove = () => {
  selectedFile.value = null
  taskName.value = ''
}

const clearFile = () => {
  selectedFile.value = null
  taskName.value = ''
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
}

// 导入操作
const startImport = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择Excel文件')
    return
  }

  if (!taskName.value.trim()) {
    ElMessage.warning('请输入任务名称')
    return
  }

  starting.value = true
  try {
    // 准备导入选项，包括选择的分类
    const finalImportOptions = {
      ...importOptions.value,
      selectedCategoryId: selectedCategoryId.value
    }
    
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    formData.append('name', taskName.value)
    formData.append('import_mode', importMode.value)
    formData.append('import_options', JSON.stringify(finalImportOptions))
    formData.append('batch_size', batchSize.value.toString())

    const result = await importTaskApi.create(formData)
    ElMessage.success('导入任务已创建，开始处理...')
    
    // 设置当前任务
    currentTask.value = result
    clearFile()
    
    // 开始监听进度
    startProgressMonitoring()
  } catch (error: any) {
    const errorMessage = error.response?.data?.detail || error.message || '创建导入任务失败'
    ElMessage.error(errorMessage)
    console.error('Import error:', error)
  } finally {
    starting.value = false
  }
}

// 进度监控
const startProgressMonitoring = () => {
  // WebSocket消息处理
  onMessage((data) => {
    if (data.type === 'import_progress' && currentTask.value && data.task_id === currentTask.value.id) {
      // 更新任务状态
      currentTask.value.status = data.status
      currentTask.value.progress_percentage = data.progress_percentage
      currentTask.value.current_batch = data.current_batch
      currentTask.value.processed_rows = data.processed_rows
      currentTask.value.success_rows = data.success_rows
      currentTask.value.failed_rows = data.failed_rows

      // 处理完成或失败
      if (data.status === 'completed') {
        ElMessage.success(`导入完成！成功 ${data.success_rows} 行，失败 ${data.failed_rows} 行`)
        loadTasks() // 刷新历史列表
      } else if (data.status === 'failed') {
        ElMessage.error('导入任务失败')
      } else if (data.status === 'cancelled') {
        ElMessage.info('导入任务已取消')
      }
    }
  })
}

// 任务操作
const cancelTask = async () => {
  if (!currentTask.value) return

  try {
    await ElMessageBox.confirm('确定要取消当前导入任务吗？', '确认取消', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    cancelling.value = true
    await importTaskApi.cancel(currentTask.value.id)
    ElMessage.success('任务已取消')
  } catch (error: any) {
    // 检查是否是用户取消的操作
    if (error !== 'cancel') {
      const errorMessage = error.response?.data?.detail || error.message || '取消任务失败'
      ElMessage.error(errorMessage)
    }
  } finally {
    cancelling.value = false
  }
}

const refreshTask = async () => {
  if (!currentTask.value) return

  try {
    const status = await importTaskApi.getStatus(currentTask.value.id)
    // 更新当前任务状态
    Object.assign(currentTask.value, status)
    errorMessages.value = status.error_messages || []
  } catch (error) {
    console.error('刷新任务状态失败:', error)
  }
}

const viewResults = () => {
  // 跳转到测试用例列表页面查看导入结果
  ElMessage.success('导入完成，即将跳转到测试用例列表')
  // 这里可以添加路由跳转逻辑
}

const viewTaskDetail = (task: ImportTask) => {
  currentTask.value = task
  refreshTask()
}

// 任务列表
const loadTasks = async () => {
  loadingHistory.value = true
  try {
    const result = await importTaskApi.getList()
    taskHistory.value = result.tasks
    hasRunningTask.value = result.has_running_task

    // 如果有正在运行的任务，找到它并设置为当前任务
    if (hasRunningTask.value && !currentTask.value) {
      const runningTask = taskHistory.value.find(task => 
        task.status === 'running' || task.status === 'pending'
      )
      if (runningTask) {
        currentTask.value = runningTask
        startProgressMonitoring()
      }
    }
  } catch (error) {
    console.error('加载任务列表失败:', error)
  } finally {
    loadingHistory.value = false
  }
}

// 工具函数
const getStatusTagType = (status: string) => {
  switch (status) {
    case 'completed': return 'success'
    case 'failed': return 'danger'
    case 'running': return 'primary'
    case 'pending': return 'warning'
    case 'cancelled': return 'info'
    default: return ''
  }
}

const getStatusText = (status: string) => {
  switch (status) {
    case 'pending': return '等待中'
    case 'running': return '进行中'
    case 'completed': return '已完成'
    case 'failed': return '失败'
    case 'cancelled': return '已取消'
    default: return status
  }
}

const getProgressStatus = (status: string) => {
  switch (status) {
    case 'completed': return 'success'
    case 'failed': return 'exception'
    default: return undefined
  }
}

const formatDateTime = (dateStr: string) => {
  return new Date(dateStr).toLocaleString()
}

// 模版相关功能
const downloadTemplate = async () => {
  downloadingTemplate.value = true
  try {
    // 使用axios实例获取配置的基础URL
    const baseURL = (api as any).defaults.baseURL || '/api'
    const downloadUrl = `${baseURL}/import-tasks/template/download`
    
    const response = await fetch(downloadUrl)
    if (response.ok) {
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = '测试用例导入模版.xlsx'
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      ElMessage.success('模版下载成功')
    } else {
      ElMessage.error('模版下载失败')
    }
  } catch (error) {
    ElMessage.error('模版下载失败')
    console.error('Download error:', error)
  } finally {
    downloadingTemplate.value = false
  }
}

const viewTemplateSample = () => {
  ElMessage.info('模版中包含详细的使用说明和示例数据，请下载后查看')
}

// 分类相关功能
const loadCategories = async () => {
  loadingCategories.value = true
  try {
    categoryOptions.value = await categoryApi.getTree(false)
  } catch (error) {
    console.error('加载分类失败:', error)
    ElMessage.error('加载分类失败')
  } finally {
    loadingCategories.value = false
  }
}

// 生命周期
onMounted(() => {
  loadTasks()
  loadCategories()
  connect()
})

onUnmounted(() => {
  disconnect()
})
</script>

<style scoped>
.excel-import-page {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
  text-align: center;
}

.page-header h2 {
  margin: 0 0 8px 0;
  color: #303133;
}

.page-header p {
  margin: 0;
  color: #606266;
}

.import-form-card,
.progress-card,
.warning-card,
.history-card {
  margin-bottom: 24px;
}

.upload-area {
  margin-bottom: 24px;
}

.import-config h3 {
  margin: 0 0 16px 0;
  color: #303133;
}

.action-buttons {
  text-align: center;
  margin-top: 24px;
}

.action-buttons .el-button {
  margin: 0 8px;
}

.warning-card .el-alert {
  border: none;
  background-color: #fdf6ec;
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.progress-section {
  margin-bottom: 24px;
}

.progress-info,
.batch-info {
  margin-bottom: 16px;
}

.progress-info h4,
.batch-info h4 {
  margin: 0 0 8px 0;
  color: #303133;
}

.progress-text,
.batch-text {
  text-align: center;
  margin-top: 8px;
  color: #606266;
  font-size: 14px;
}

.stats-section {
  margin: 24px 0;
}

.stat-item {
  text-align: center;
  padding: 16px;
  border-radius: 8px;
  background-color: #f8f9fa;
}

.stat-item.success {
  background-color: #f0f9ff;
  color: #067f23;
}

.stat-item.error {
  background-color: #fef2f2;
  color: #dc2626;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #666;
}

.error-section {
  margin: 24px 0;
  padding: 16px;
  background-color: #fef2f2;
  border-radius: 8px;
}

.error-section h4 {
  margin: 0 0 12px 0;
  color: #dc2626;
}

.error-messages {
  max-height: 200px;
  overflow-y: auto;
}

.error-item {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  color: #dc2626;
}

.error-item .el-icon {
  margin-right: 8px;
}

.task-actions {
  text-align: center;
  margin-top: 24px;
}

.task-actions .el-button {
  margin: 0 8px;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.import-mode-section {
  margin-bottom: 24px;
}

.import-mode-section h3 {
  margin: 0 0 16px 0;
  color: #303133;
}

.mode-selector {
  width: 100%;
  display: flex;
  gap: 16px;
}

.mode-selector .el-radio {
  flex: 1;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  margin-right: 0;
  transition: all 0.3s;
  min-width: 0; /* 防止内容溢出 */
}

.mode-selector .el-radio:hover {
  border-color: #409eff;
  background-color: #f0f9ff;
}

.mode-selector .el-radio.is-checked {
  border-color: #409eff;
  background-color: #ecf5ff;
}

.mode-option {
  margin-left: 8px;
}

.mode-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.mode-desc {
  font-size: 14px;
  color: #606266;
  line-height: 1.4;
  word-wrap: break-word;
  white-space: normal;
}

.template-download {
  margin-top: 16px;
  padding: 16px;
  background-color: #f8f9fa;
  border-radius: 8px;
}

.template-actions {
  margin-top: 12px;
  text-align: center;
}

.template-actions .el-button {
  margin: 0 8px;
}

.smart-mode-info {
  margin-top: 16px;
}
</style>