<template>
  <div class="home">
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card class="welcome-card">
          <template #header>
            <div class="card-header">
              <h2>欢迎使用 AutoTest</h2>
            </div>
          </template>
          <div class="welcome-content">
            <p>基于Browser Use的智能Web自动化测试工具，支持语义化测试用例编写和详细的测试结果记录。</p>
            <el-button type="primary" @click="$router.push('/test-cases')">
              <el-icon><Plus /></el-icon>
              创建测试用例
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon" color="#409EFF"><Document /></el-icon>
            <div class="stat-info">
              <div class="stat-number">{{ statistics.total_test_cases }}</div>
              <div class="stat-label">测试用例</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon" color="#67C23A"><VideoPlay /></el-icon>
            <div class="stat-info">
              <div class="stat-number">{{ statistics.total_executions }}</div>
              <div class="stat-label">执行次数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon" color="#E6A23C"><TrendCharts /></el-icon>
            <div class="stat-info">
              <div class="stat-number">{{ statistics.success_rate }}%</div>
              <div class="stat-label">成功率</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon" color="#F56C6C"><Clock /></el-icon>
            <div class="stat-info">
              <div class="stat-number">{{ formatDuration(statistics.average_duration) }}</div>
              <div class="stat-label">平均耗时</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <h3>最近执行记录</h3>
            </div>
          </template>
          <div v-if="statistics.recent_executions.length === 0" class="empty-state">
            <el-empty description="暂无执行记录" />
          </div>
          <div v-else class="execution-list">
            <div 
              v-for="execution in statistics.recent_executions.slice(0, 5)" 
              :key="execution.id"
              class="execution-item"
            >
              <div class="execution-info">
                <div class="execution-name">{{ execution.execution_name }}</div>
                <div class="execution-status">
                  <el-tag :type="getStatusType(execution.overall_status)">
                    {{ execution.overall_status }}
                  </el-tag>
                </div>
              </div>
              <div class="execution-meta">
                <span>{{ formatDate(execution.created_at) }}</span>
                <span>{{ formatDuration(execution.total_duration) }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <h3>快速操作</h3>
            </div>
          </template>
          <div class="quick-actions">
            <el-button type="primary" @click="$router.push('/test-cases')" class="action-btn">
              <el-icon><Document /></el-icon>
              管理测试用例
            </el-button>
            <el-button type="success" @click="$router.push('/executions')" class="action-btn">
              <el-icon><VideoPlay /></el-icon>
              查看执行记录
            </el-button>
            <el-button type="warning" @click="$router.push('/statistics')" class="action-btn">
              <el-icon><TrendCharts /></el-icon>
              查看统计信息
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Plus, Document, VideoPlay, TrendCharts, Clock } from '@element-plus/icons-vue'
import { statisticsApi } from '@/services/api'
import type { Statistics } from '@/types/api'

const statistics = ref<Statistics>({
  total_test_cases: 0,
  total_executions: 0,
  passed_executions: 0,
  failed_executions: 0,
  success_rate: 0,
  average_duration: 0,
  recent_executions: [],
  category_stats: [],
  priority_stats: []
})

const loadStatistics = async () => {
  try {
    const data = await statisticsApi.getStatistics()
    statistics.value = data
  } catch (error) {
    console.error('Failed to load statistics:', error)
  }
}

const formatDuration = (seconds: number): string => {
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

onMounted(() => {
  loadStatistics()
})
</script>

<style scoped>
.home {
  max-width: 1200px;
  margin: 0 auto;
}

.welcome-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-header h2,
.card-header h3 {
  margin: 0;
  color: #303133;
}

.welcome-content {
  text-align: center;
  padding: 20px 0;
}

.welcome-content p {
  font-size: 16px;
  color: #606266;
  margin-bottom: 20px;
  line-height: 1.6;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.stat-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
}

.stat-icon {
  font-size: 32px;
}

.stat-info {
  text-align: left;
}

.stat-number {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.execution-list {
  max-height: 300px;
  overflow-y: auto;
}

.execution-item {
  padding: 12px 0;
  border-bottom: 1px solid #EBEEF5;
}

.execution-item:last-child {
  border-bottom: none;
}

.execution-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.execution-name {
  font-weight: 500;
  color: #303133;
}

.execution-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #909399;
}

.empty-state {
  padding: 40px 0;
}

.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.action-btn {
  width: 100%;
  height: 48px;
  font-size: 16px;
}
</style> 