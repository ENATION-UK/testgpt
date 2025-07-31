<template>
  <div class="statistics">
    <div class="page-header">
      <h2>统计信息</h2>
    </div>

    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon" color="#409EFF"><Document /></el-icon>
            <div class="stat-info">
              <div class="stat-number">{{ statistics.total_test_cases }}</div>
              <div class="stat-label">测试用例总数</div>
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
              <div class="stat-label">执行总次数</div>
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

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <h3>分类统计</h3>
            </div>
          </template>
          <div v-if="statistics.category_stats.length === 0" class="empty-state">
            <el-empty description="暂无分类数据" />
          </div>
          <div v-else class="category-list">
            <div 
              v-for="category in statistics.category_stats" 
              :key="category.category"
              class="category-item"
            >
              <span class="category-name">{{ category.category }}</span>
              <span class="category-count">{{ category.count }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <h3>优先级统计</h3>
            </div>
          </template>
          <div v-if="statistics.priority_stats.length === 0" class="empty-state">
            <el-empty description="暂无优先级数据" />
          </div>
          <div v-else class="priority-list">
            <div 
              v-for="priority in statistics.priority_stats" 
              :key="priority.priority"
              class="priority-item"
            >
              <el-tag :type="getPriorityType(priority.priority)" class="priority-tag">
                {{ getPriorityLabel(priority.priority) }}
              </el-tag>
              <span class="priority-count">{{ priority.count }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Document, VideoPlay, TrendCharts, Clock } from '@element-plus/icons-vue'
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
    ElMessage.error('加载统计信息失败')
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

const getPriorityType = (priority: string): string => {
  const types = {
    low: 'info',
    medium: 'warning',
    high: 'danger',
    critical: 'danger'
  }
  return types[priority as keyof typeof types] || 'info'
}

const getPriorityLabel = (priority: string): string => {
  const labels = {
    low: '低',
    medium: '中',
    high: '高',
    critical: '紧急'
  }
  return labels[priority as keyof typeof labels] || priority
}

onMounted(() => {
  loadStatistics()
})
</script>

<style scoped>
.statistics {
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

.card-header h3 {
  margin: 0;
  color: #303133;
}

.empty-state {
  padding: 40px 0;
}

.category-list,
.priority-list {
  max-height: 300px;
  overflow-y: auto;
}

.category-item,
.priority-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #EBEEF5;
}

.category-item:last-child,
.priority-item:last-child {
  border-bottom: none;
}

.category-name {
  font-weight: 500;
  color: #303133;
}

.category-count,
.priority-count {
  font-weight: bold;
  color: #409EFF;
}

.priority-tag {
  margin-right: 8px;
}
</style> 