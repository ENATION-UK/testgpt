<template>
  <div class="execution-detail">
    <div class="page-header">
      <h2>{{ $t('execution.detail') }}</h2>
      <el-button @click="goBack" type="primary">
        <el-icon><ArrowLeft /></el-icon>
        {{ $t('common.back') }}
      </el-button>
    </div>

    <div v-loading="loading" class="main-content">
      <!-- 左侧步骤列表面板 -->
      <div class="left-panel">
        <el-card class="steps-panel">
          
          <div v-if="steps.length > 0" class="steps-list">
            <div class="steps-summary">
              <span>{{ steps.length }} {{ $t('execution.completedSteps') }}</span>

            </div>
            
            <div class="steps-container">
              <div
                v-for="(step, index) in steps"
                :key="step.id"
                class="step-item"
                :class="{ 
                  'active': selectedStepIndex === index,
                  'completed': step.status === 'PASSED',
                  'failed': step.status === 'FAILED',
                  'skipped': step.status === 'SKIPPED'
                }"
                @click="selectStep(index)"
              >
                <div class="step-status">
                  <el-icon v-if="step.status === 'PASSED'" class="status-icon success">
                    <Check />
                  </el-icon>
                  <el-icon v-else-if="step.status === 'FAILED'" class="status-icon error">
                    <Close />
                  </el-icon>
                  <el-icon v-else-if="step.status === 'SKIPPED'" class="status-icon warning">
                    <Minus />
                  </el-icon>
                  <el-icon v-else class="status-icon info">
                    <Clock />
                  </el-icon>
                </div>
                <div class="step-content">
                  <div class="step-name">{{ step.step_name }}</div>
                  <div v-if="step.description" class="step-description">{{ step.description }}</div>
                  <div v-if="step.duration_seconds" class="step-duration">
                    耗时: {{ step.duration_seconds }}s
                  </div>
                </div>
              </div>
            </div>
            

          </div>
          
          <el-empty v-else-if="!loading" description="暂无执行步骤信息" />
        </el-card>
      </div>

      <!-- 右侧截图显示面板 -->
      <div class="right-panel">
        <el-card class="screenshot-panel">
          <div v-if="selectedStep" class="screenshot-container">
            <div v-if="selectedStep.screenshot_data || selectedStep.screenshot_path" class="screenshot-wrapper">
              <img 
                :src="getScreenshotUrl(selectedStep.screenshot_data || selectedStep.screenshot_path)" 
                :alt="`步骤 ${selectedStepIndex + 1} 截图`"
                class="screenshot-image"
              />
            </div>
            <div v-else class="no-screenshot">
              <el-empty description="该步骤没有截图" />
            </div>
            
            <!-- 导航控制 -->
            <div class="navigation-controls">
              <el-button 
                :disabled="selectedStepIndex === 0"
                @click="previousStep"
                size="small"
              >
                <el-icon><ArrowLeft /></el-icon>
                上一步
              </el-button>
              <el-button 
                :disabled="selectedStepIndex === steps.length - 1"
                @click="nextStep"
                size="small"
              >
                下一步
                <el-icon><ArrowRight /></el-icon>
              </el-button>
            </div>
          </div>
          
          <div v-else class="no-step-selected">
            <el-empty description="请选择一个步骤查看截图" />
          </div>
        </el-card>
      </div>
    </div>

    <!-- 执行信息弹窗 -->
    <el-dialog v-model="showExecutionInfo" title="执行信息" width="800px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="执行名称">{{ execution?.execution_name }}</el-descriptions-item>
        <el-descriptions-item label="测试用例ID">{{ execution?.test_case_id }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ execution?.status }}</el-descriptions-item>
        <el-descriptions-item label="总耗时">{{ formatDuration(execution?.total_duration || 0) }}</el-descriptions-item>
        <el-descriptions-item label="总步骤数">{{ execution?.total_steps }}</el-descriptions-item>
        <el-descriptions-item label="通过步骤">{{ execution?.passed_steps }}</el-descriptions-item>
        <el-descriptions-item label="失败步骤">{{ execution?.failed_steps }}</el-descriptions-item>
        <el-descriptions-item label="跳过步骤">{{ execution?.skipped_steps }}</el-descriptions-item>
        <el-descriptions-item label="开始时间">{{ formatDate(execution?.started_at || '') }}</el-descriptions-item>
        <el-descriptions-item label="完成时间">{{ execution?.completed_at ? formatDate(execution.completed_at) : '' }}</el-descriptions-item>
      </el-descriptions>

      <div v-if="execution?.summary" class="summary-section">
        <h3>执行摘要</h3>
        <p>{{ execution.summary }}</p>
      </div>

      <div v-if="execution?.recommendations" class="recommendations-section">
        <h3>建议</h3>
        <p>{{ execution.recommendations }}</p>
      </div>

      <div v-if="execution?.error_message" class="error-section">
        <h3>错误信息</h3>
        <el-alert :title="execution.error_message" type="error" show-icon />
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { ArrowLeft, ArrowRight, ArrowUp, Check, Close, Minus, Clock } from '@element-plus/icons-vue'
import { testExecutionApi } from '@/services/api'
import type { TestExecution } from '@/types/api'

const { t } = useI18n()

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const execution = ref<TestExecution | null>(null)
const steps = ref<any[]>([])
const selectedStepIndex = ref(0)
const showExecutionInfo = ref(false)

const executionId = computed(() => {
  const id = route.params.executionId
  return id ? parseInt(id as string) : null
})

const selectedStep = computed(() => {
  return steps.value[selectedStepIndex.value] || null
})

const loadExecutionDetail = async () => {
  if (!executionId.value) return
  
  loading.value = true
  try {
    const [executionData, stepsData] = await Promise.all([
      testExecutionApi.getById(executionId.value),
      testExecutionApi.getSteps(executionId.value)
    ])
    execution.value = executionData
    steps.value = stepsData
    
    // 默认选择第一个有截图的步骤
    const firstStepWithScreenshot = stepsData.findIndex((step: any) => 
      step.screenshot_data || step.screenshot_path
    )
    if (firstStepWithScreenshot !== -1) {
      selectedStepIndex.value = firstStepWithScreenshot
    }
  } catch (error) {
    ElMessage.error('加载执行详情失败')
  } finally {
    loading.value = false
  }
}

const selectStep = (index: number) => {
  selectedStepIndex.value = index
}

const previousStep = () => {
  if (selectedStepIndex.value > 0) {
    selectedStepIndex.value--
  }
}

const nextStep = () => {
  if (selectedStepIndex.value < steps.value.length - 1) {
    selectedStepIndex.value++
  }
}

const goBack = () => {
  router.back()
}


const formatDuration = (seconds: number): string => {
  if (!seconds) return '0s'
  if (seconds < 60) {
    return `${seconds}s`
  }
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return `${minutes}m ${remainingSeconds}s`
}

const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleString('zh-CN')
}

const getScreenshotUrl = (path: string): string => {
  // 检查是否是base64数据
  if (path && path.startsWith('data:image')) {
    // 直接返回base64数据
    return path
  }
  // 如果是文件路径，构建API URL
  return `/api/screenshots/${path}`
}

onMounted(() => {
  loadExecutionDetail()
})
</script>

<style scoped>
.execution-detail {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  flex-shrink: 0;
}

.page-header h2 {
  margin: 0;
  color: #303133;
  font-size: 18px;
  font-weight: 500;
}

.main-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.left-panel {
  width: 400px;
  border-right: 1px solid #e4e7ed;
  background: #f8f9fa;
  overflow-y: auto;
}

.right-panel {
  flex: 1;
  background: #fff;
  overflow-y: auto;
}

.steps-panel {
  height: 100%;
  border: none;
  border-radius: 0;
}

.steps-panel :deep(.el-card__header) {
  padding: 16px 20px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-header span {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}


.steps-list {
  padding: 0 20px 20px;
}

.steps-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #e4e7ed;
  margin-bottom: 16px;
  cursor: pointer;
}

.steps-summary span {
  font-size: 14px;
  color: #606266;
}

.expand-icon {
  color: #909399;
  transition: transform 0.3s;
}

.steps-container {
  max-height: calc(100vh - 200px);
  overflow-y: auto;
}

.step-item {
  display: flex;
  align-items: flex-start;
  padding: 12px 16px;
  margin-bottom: 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  border: 1px solid transparent;
}

.step-item:hover {
  background: #f0f9ff;
  border-color: #b3d8ff;
}

.step-item.active {
  background: #e1f5fe;
  border-color: #4fc3f7;
}

.step-item.completed {
  background: #f0f9ff;
}

.step-item.failed {
  background: #fef2f2;
}

.step-item.skipped {
  background: #fffbeb;
}

.step-status {
  margin-right: 12px;
  margin-top: 2px;
}

.status-icon {
  font-size: 16px;
}

.status-icon.success {
  color: #67c23a;
}

.status-icon.error {
  color: #f56c6c;
}

.status-icon.warning {
  color: #e6a23c;
}

.status-icon.info {
  color: #909399;
}

.step-content {
  flex: 1;
}

.step-name {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
  line-height: 1.4;
}

.step-description {
  font-size: 13px;
  color: #606266;
  margin-bottom: 4px;
  line-height: 1.4;
}

.step-duration {
  font-size: 12px;
  color: #909399;
}

.task-info {
  padding: 12px 0;
  border-top: 1px solid #e4e7ed;
  margin-top: 16px;
  text-align: center;
}

.task-info span {
  font-size: 12px;
  color: #909399;
}

.screenshot-panel {
  height: 100%;
  border: none;
  border-radius: 0;
}

.screenshot-panel :deep(.el-card__body) {
  padding: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.screenshot-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 20px;
}

.screenshot-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f8f9fa;
  border-radius: 8px;
  overflow: hidden;
}

.screenshot-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.no-screenshot,
.no-step-selected {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.navigation-controls {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e4e7ed;
}

.summary-section,
.recommendations-section,
.error-section {
  margin-top: 20px;
}

.summary-section h3,
.recommendations-section h3,
.error-section h3 {
  margin-bottom: 10px;
  color: #303133;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .main-content {
    flex-direction: column;
  }
  
  .left-panel {
    width: 100%;
    height: 300px;
    border-right: none;
    border-bottom: 1px solid #e4e7ed;
  }
  
  .right-panel {
    height: calc(100vh - 300px);
  }
}
</style> 