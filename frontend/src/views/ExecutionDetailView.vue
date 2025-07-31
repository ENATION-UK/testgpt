<template>
  <div class="execution-detail">
    <div class="page-header">
      <h2>执行详情</h2>
      <el-button @click="goBack" type="primary">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
    </div>

    <div v-loading="loading">
      <el-card v-if="execution" class="execution-info">
        <template #header>
          <div class="card-header">
            <span>执行信息</span>
            <el-tag :type="getStatusType(execution.overall_status)">
              {{ execution.overall_status }}
            </el-tag>
          </div>
        </template>
        
        <el-descriptions :column="2" border>
          <el-descriptions-item label="执行名称">{{ execution.execution_name }}</el-descriptions-item>
          <el-descriptions-item label="测试用例ID">{{ execution.test_case_id }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ execution.status }}</el-descriptions-item>
          <el-descriptions-item label="总耗时">{{ formatDuration(execution.total_duration) }}</el-descriptions-item>
          <el-descriptions-item label="总步骤数">{{ execution.total_steps }}</el-descriptions-item>
          <el-descriptions-item label="通过步骤">{{ execution.passed_steps }}</el-descriptions-item>
          <el-descriptions-item label="失败步骤">{{ execution.failed_steps }}</el-descriptions-item>
          <el-descriptions-item label="跳过步骤">{{ execution.skipped_steps }}</el-descriptions-item>
          <el-descriptions-item label="开始时间">{{ formatDate(execution.started_at) }}</el-descriptions-item>
          <el-descriptions-item label="完成时间">{{ formatDate(execution.completed_at) }}</el-descriptions-item>
        </el-descriptions>

        <div v-if="execution.summary" class="summary-section">
          <h3>执行摘要</h3>
          <p>{{ execution.summary }}</p>
        </div>

        <div v-if="execution.recommendations" class="recommendations-section">
          <h3>建议</h3>
          <p>{{ execution.recommendations }}</p>
        </div>

        <div v-if="execution.error_message" class="error-section">
          <h3>错误信息</h3>
          <el-alert :title="execution.error_message" type="error" show-icon />
        </div>
      </el-card>

      <el-card v-if="steps.length > 0" class="steps-info">
        <template #header>
          <span>执行步骤</span>
        </template>
        
        <el-timeline>
          <el-timeline-item
            v-for="step in steps"
            :key="step.id"
            :type="getStepStatusType(step.status)"
            :timestamp="formatDate(step.started_at)"
            placement="top"
          >
            <el-card>
              <template #header>
                <div class="step-header">
                  <span>{{ step.step_name }}</span>
                  <el-tag :type="getStepStatusType(step.status)" size="small">
                    {{ step.status }}
                  </el-tag>
                </div>
              </template>
              
              <div class="step-content">
                <p v-if="step.description">{{ step.description }}</p>
                <p v-if="step.duration_seconds" class="step-duration">
                  耗时: {{ step.duration_seconds }}s
                </p>
                <div v-if="step.error_message" class="step-error">
                  <el-alert :title="step.error_message" type="error" show-icon />
                </div>
                <div v-if="step.screenshot_path" class="step-screenshot">
                  <h4>截图</h4>
                  <img :src="getScreenshotUrl(step.screenshot_path)" alt="步骤截图" />
                </div>
              </div>
            </el-card>
          </el-timeline-item>
        </el-timeline>
      </el-card>

      <el-empty v-else-if="!loading" description="暂无执行步骤信息" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { testExecutionApi } from '@/services/api'
import type { TestExecution } from '@/types/api'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const execution = ref<TestExecution | null>(null)
const steps = ref<any[]>([])

const executionId = computed(() => {
  const id = route.params.executionId
  return id ? parseInt(id as string) : null
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
  } catch (error) {
    ElMessage.error('加载执行详情失败')
  } finally {
    loading.value = false
  }
}

const goBack = () => {
  router.back()
}

const getStatusType = (status: string): string => {
  switch (status) {
    case 'PASSED':
      return 'success'
    case 'FAILED':
      return 'danger'
    case 'PARTIAL':
      return 'warning'
    default:
      return 'info'
  }
}

const getStepStatusType = (status: string): string => {
  switch (status) {
    case 'PASSED':
      return 'success'
    case 'FAILED':
      return 'danger'
    case 'SKIPPED':
      return 'warning'
    default:
      return 'info'
  }
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
  // 这里需要根据实际的后端配置来构建截图URL
  return `/api/screenshots/${path}`
}

onMounted(() => {
  loadExecutionDetail()
})
</script>

<style scoped>
.execution-detail {
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

.execution-info {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
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

.steps-info {
  margin-top: 20px;
}

.step-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.step-content {
  margin-top: 10px;
}

.step-duration {
  color: #909399;
  font-size: 14px;
  margin: 5px 0;
}

.step-error {
  margin-top: 10px;
}

.step-screenshot {
  margin-top: 15px;
}

.step-screenshot h4 {
  margin-bottom: 10px;
  color: #303133;
}

.step-screenshot img {
  max-width: 100%;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
}
</style> 