<template>
  <div class="batch-execution-detail">
    <div class="page-header">
      <el-page-header @back="goBack" :content="`批量执行任务详情 - ${batchExecution?.name || ''}`" />
    </div>

    <div v-loading="loading">
      <el-card v-if="batchExecution" class="batch-info">
        <template #header>
          <div class="card-header">
            <span>任务信息</span>
            <el-tag :type="getBatchStatusType(batchExecution.status)">
              {{ getBatchStatusLabel(batchExecution.status) }}
            </el-tag>
          </div>
        </template>
        
        <el-descriptions :column="2" border>
          <el-descriptions-item label="任务名称">{{ batchExecution.name }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getBatchStatusType(batchExecution.status)">
              {{ getBatchStatusLabel(batchExecution.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="开始时间">{{ formatDate(batchExecution.started_at) }}</el-descriptions-item>
          <el-descriptions-item label="完成时间">{{ batchExecution.completed_at ? formatDate(batchExecution.completed_at) : '-' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatDate(batchExecution.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ formatDate(batchExecution.updated_at) }}</el-descriptions-item>
          <el-descriptions-item label="总用例数">{{ batchExecution.total_count }}</el-descriptions-item>
          <el-descriptions-item label="成功数">{{ batchExecution.success_count }}</el-descriptions-item>
          <el-descriptions-item label="失败数">{{ batchExecution.failed_count }}</el-descriptions-item>
          <el-descriptions-item label="运行中">{{ batchExecution.running_count }}</el-descriptions-item>
          <el-descriptions-item label="待执行">{{ batchExecution.pending_count }}</el-descriptions-item>
          <el-descriptions-item label="总耗时">{{ formatDuration(batchExecution.total_duration) }}</el-descriptions-item>
          <el-descriptions-item label="浏览器模式">
            <el-tag :type="batchExecution.headless ? 'info' : 'warning'">
              {{ batchExecution.headless ? '无头模式' : '有头模式' }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <el-card class="test-cases-info">
        <template #header>
          <div class="card-header">
            <span>测试用例执行详情</span>
            <div class="header-actions">
              <el-input
                v-model="searchKeyword"
                placeholder="搜索测试用例..."
                style="width: 200px; margin-right: 10px;"
                clearable
                @clear="handleSearch"
                @keyup.enter="handleSearch"
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
              <el-button type="primary" @click="handleSearch">
                <el-icon><Search /></el-icon>
                搜索
              </el-button>
            </div>
          </div>
        </template>
        
        <el-table
          :data="testCases"
          style="width: 100%"
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
                :disabled="!row.execution_id"
              >
                查看详情
              </el-button>
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
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { batchExecutionApi } from '@/services/api'
import type { BatchExecution, BatchExecutionTestCase } from '@/types/api'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const batchExecution = ref<BatchExecution | null>(null)

// 测试用例分页相关
const testCases = ref<BatchExecutionTestCase[]>([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const searchKeyword = ref('')

const batchExecutionId = computed(() => {
  const id = route.params.id
  return id ? parseInt(id as string) : null
})

const loadBatchExecutionDetail = async () => {
  if (!batchExecutionId.value) return
  
  loading.value = true
  try {
    const data = await batchExecutionApi.getById(batchExecutionId.value)
    batchExecution.value = data
  } catch (error) {
    ElMessage.error('加载批量执行任务详情失败')
  } finally {
    loading.value = false
  }
}

const loadTestCases = async () => {
  if (!batchExecutionId.value) return
  
  loading.value = true
  try {
    const params = {
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value,
      search: searchKeyword.value || undefined
    }
    
    const response = await batchExecutionApi.getTestCases(batchExecutionId.value, params)
    testCases.value = response.test_cases
    total.value = response.total
  } catch (error) {
    ElMessage.error('加载测试用例详情失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  loadTestCases()
}

const handleSizeChange = (newSize: number) => {
  pageSize.value = newSize
  currentPage.value = 1
  loadTestCases()
}

const handleCurrentChange = (newPage: number) => {
  currentPage.value = newPage
  loadTestCases()
}

const goBack = () => {
  router.back()
}

const viewTestCaseExecution = (executionId: number | undefined) => {
  if (executionId) {
    router.push({
      name: 'execution-detail',
      params: { executionId: executionId.toString() }
    })
  } else {
    ElMessage.warning('该测试用例暂无执行记录')
  }
}

// 状态标签相关函数
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
  loadBatchExecutionDetail()
  loadTestCases()
})

// 监听路由参数变化
watch(
  () => route.params.id,
  (newId) => {
    if (newId) {
      loadBatchExecutionDetail()
      loadTestCases()
    }
  }
)
</script>

<script lang="ts">
export default {
  name: 'BatchExecutionDetailView'
}
</script>

<style scoped>
.batch-execution-detail {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  align-items: center;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
  padding: 20px 0;
}
</style>