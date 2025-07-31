<template>
  <div class="executions">
    <div class="page-header">
      <h2>{{ pageTitle }}</h2>
      <el-button v-if="testCaseId" @click="goBack" type="primary">
        <el-icon><ArrowLeft /></el-icon>
        返回测试用例
      </el-button>
    </div>

    <el-card>
      <el-table
        v-loading="loading"
        :data="executions"
        style="width: 100%"
      >
        <el-table-column prop="execution_name" label="执行名称" min-width="200" />
        <el-table-column prop="test_case_id" label="测试用例ID" width="120" />
        <el-table-column prop="overall_status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.overall_status)">
              {{ row.overall_status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="步骤统计" width="150">
          <template #default="{ row }">
            <div class="step-stats">
              <span class="passed">{{ row.passed_steps }}</span>
              /
              <span class="total">{{ row.total_steps }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="total_duration" label="耗时" width="100">
          <template #default="{ row }">
            {{ formatDuration(row.total_duration) }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewExecution(row)">查看详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { testExecutionApi } from '@/services/api'
import type { TestExecution } from '@/types/api'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const executions = ref<TestExecution[]>([])

const testCaseId = computed(() => {
  const id = route.params.testCaseId
  return id ? parseInt(id as string) : null
})

const pageTitle = computed(() => {
  return testCaseId.value ? `测试用例 ${testCaseId.value} 的执行记录` : '执行记录'
})

const loadExecutions = async () => {
  loading.value = true
  try {
    if (testCaseId.value) {
      const data = await testExecutionApi.getByTestCaseId(testCaseId.value)
      executions.value = data
    } else {
      const data = await testExecutionApi.getList()
      executions.value = data
    }
  } catch (error) {
    ElMessage.error('加载执行记录失败')
  } finally {
    loading.value = false
  }
}

const goBack = () => {
  router.push({ name: 'test-cases' })
}

const viewExecution = (execution: TestExecution) => {
  router.push({ name: 'execution-detail', params: { executionId: execution.id } })
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

onMounted(() => {
  loadExecutions()
})

// 监听路由参数变化
watch(() => route.params.testCaseId, () => {
  loadExecutions()
})
</script>

<style scoped>
.executions {
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

.step-stats {
  font-weight: 500;
}

.step-stats .passed {
  color: #67C23A;
}

.step-stats .total {
  color: #909399;
}
</style> 