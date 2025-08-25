<template>
  <div class="test-cases">
    <div class="page-header">
      <h2>测试用例管理</h2>
      <div class="header-actions">
        <el-button type="info" @click="goToCategories">
          <el-icon><Folder /></el-icon>
          分类管理
        </el-button>
        <el-button type="success" @click="goToImportPage">
          <el-icon><Upload /></el-icon>
          导入Excel
        </el-button>
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon>
          创建测试用例
        </el-button>
        <el-button type="warning" @click="showBatchExecuteDialog = true">
          <el-icon><Operation /></el-icon>
          批量执行
        </el-button>
      </div>
    </div>

    <!-- 分类筛选 -->
    <el-card style="margin-bottom: 20px;">
      <div class="filter-section">
        <el-form :model="filterForm" inline>
          <el-form-item label="分类筛选">
            <el-cascader
              v-model="filterForm.category_id"
              :options="categoryOptions"
              :props="cascaderProps"
              placeholder="请选择分类"
              clearable
              style="width: 300px"
              @change="handleCategoryChange"
            />
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="filterForm.status" placeholder="请选择状态" clearable>
              <el-option label="激活" value="active" />
              <el-option label="非激活" value="inactive" />
              <el-option label="草稿" value="draft" />
            </el-select>
          </el-form-item>
          <el-form-item label="优先级">
            <el-select v-model="filterForm.priority" placeholder="请选择优先级" clearable>
              <el-option label="低" value="low" />
              <el-option label="中" value="medium" />
              <el-option label="高" value="high" />
              <el-option label="紧急" value="critical" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="applyFilters">筛选</el-button>
            <el-button @click="resetFilters">重置</el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-card>

    <el-card>
      <el-table
        v-loading="loading"
        :data="testCases"
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="name" label="名称" min-width="200" />
        <el-table-column label="分类" width="120">
          <template #default="{ row }">
            {{ getCategoryName(row.category_id) }}
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" width="100">
          <template #default="{ row }">
            <el-tag :type="getPriorityType(row.priority)">
              {{ getPriorityLabel(row.priority) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-dropdown @command="(command: string) => handleCommand(command, row)" style="margin-right: 8px;">
              <el-button size="small" type="primary">
                编辑<el-icon class="el-icon--right"><arrow-down /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="view">查看</el-dropdown-item>
                  <el-dropdown-item command="edit">编辑</el-dropdown-item>
                  <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
            
            <el-dropdown @command="(command: string) => handleCommand(command, row)">
              <el-button size="small" type="success">
                执行<el-icon class="el-icon--right"><arrow-down /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="execute">执行</el-dropdown-item>
                  <el-dropdown-item command="record">记录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
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

    <!-- 创建测试用例对话框 -->
    <CreateTestCaseDialog
      v-model="showCreateDialog"
      @created="handleTestCaseCreated"
    />

    <!-- 查看测试用例对话框 -->
    <ViewTestCaseDialog
      v-model="showViewDialog"
      :test-case="selectedTestCase"
      @edit="handleEditFromView"
    />

    <!-- 编辑测试用例对话框 -->
    <EditTestCaseDialog
      v-model="showEditDialog"
      :test-case="selectedTestCase"
      @updated="handleTestCaseUpdated"
    />

    <!-- 批量执行对话框 -->
    <el-dialog
      v-model="showBatchExecuteDialog"
      title="批量执行测试用例"
      width="700px"
    >
      <el-form :model="batchExecuteForm" label-width="100px">
        <el-form-item label="执行方式">
          <el-radio-group v-model="batchExecuteForm.executionType" @change="handleExecutionTypeChange">
            <el-radio label="manual">手动选择用例</el-radio>
            <el-radio label="category">按分类执行</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <!-- 手动选择用例 -->
        <el-form-item v-if="batchExecuteForm.executionType === 'manual'" label="选择用例">
          <el-select
            v-model="batchExecuteForm.selectedTestCases"
            multiple
            filterable
            placeholder="请选择要执行的测试用例"
            style="width: 100%"
          >
            <el-option
              v-for="testCase in testCases"
              :key="testCase.id"
              :label="`${testCase.name} (${getCategoryName(testCase.category_id)})`"
              :value="testCase.id"
            />
          </el-select>
        </el-form-item>
        
        <!-- 按分类执行 -->
        <el-form-item v-if="batchExecuteForm.executionType === 'category'" label="选择分类">
          <el-cascader
            v-model="batchExecuteForm.selectedCategoryId"
            :options="categoryOptions"
            :props="cascaderProps"
            placeholder="请选择要执行的分类"
            style="width: 100%"
            @change="handleCategorySelectionChange"
          />
          <div v-if="batchExecuteForm.selectedCategoryId" style="margin-top: 10px; color: #666; font-size: 14px;">
            <el-icon><InfoFilled /></el-icon>
            将执行该分类及其所有子分类下的测试用例
          </div>
        </el-form-item>
        
        <el-form-item label="执行模式">
          <el-radio-group v-model="batchExecuteForm.headless">
            <el-radio :label="true">无头模式</el-radio>
            <el-radio :label="false">有头模式</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="closeBatchExecuteDialog">取消</el-button>
          <el-button type="primary" @click="handleBatchExecute" :loading="batchExecuting">
            确定
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, ArrowDown, Upload, Operation, Folder, InfoFilled } from '@element-plus/icons-vue'
import { testCaseApi, testExecutionApi, batchExecutionApi, categoryApi } from '@/services/api'
import type { TestCase, Category } from '@/types/api'
import CreateTestCaseDialog from '@/components/CreateTestCaseDialog.vue'
import ViewTestCaseDialog from '@/components/ViewTestCaseDialog.vue'
import EditTestCaseDialog from '@/components/EditTestCaseDialog.vue'

const router = useRouter()
const loading = ref(false)
const testCases = ref<TestCase[]>([])
const showCreateDialog = ref(false)
const showViewDialog = ref(false)
const showEditDialog = ref(false)
const showBatchExecuteDialog = ref(false) // Added for batch execute dialog
const selectedTestCase = ref<TestCase | null>(null)

// 分类相关
const categoryOptions = ref<Category[]>([])
const filterForm = ref({
  category_id: null as number | null,
  status: '',
  priority: ''
})

// 级联选择器配置
const cascaderProps = {
  value: 'id',
  label: 'name',
  children: 'children',
  checkStrictly: true, // 允许选择父分类
  emitPath: false
}

// 批量执行相关
const batchExecuteForm = ref({
  executionType: 'manual' as 'manual' | 'category',
  selectedTestCases: [] as number[],
  selectedCategoryId: null as number | null,
  headless: true
})
const batchExecuting = ref(false)

// 分页相关
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const loadTestCases = async () => {
  loading.value = true
  try {
    const skip = (currentPage.value - 1) * pageSize.value
    const data = await testCaseApi.getList({
      skip,
      limit: pageSize.value,
      category_id: filterForm.value.category_id || undefined,
      status: filterForm.value.status || undefined,
      priority: filterForm.value.priority || undefined
    })
    testCases.value = data
    // 注意：由于后端API没有返回总数，这里暂时使用当前页数据长度
    // 在实际项目中，后端应该返回包含总数的分页响应
    total.value = data.length + skip
  } catch (error) {
    ElMessage.error('加载测试用例失败')
  } finally {
    loading.value = false
  }
}

// 加载分类树
const loadCategoryTree = async () => {
  try {
    categoryOptions.value = await categoryApi.getTree(false)
  } catch (error) {
    ElMessage.error('加载分类树失败')
  }
}

// 跳转到分类管理页面
const goToCategories = () => {
  router.push('/categories')
}

// 跳转到Excel导入页面
const goToImportPage = () => {
  router.push('/excel-import')
}

// 处理分类变化
const handleCategoryChange = (value: number | number[] | null) => {
  if (Array.isArray(value)) {
    // 当 checkStrictly: true 时，value 可能是数组，取最后一个值
    filterForm.value.category_id = value.length > 0 ? value[value.length - 1] : null
  } else {
    // 当 checkStrictly: true 时，value 也可能是单个值
    filterForm.value.category_id = value
  }
}

// 应用筛选
const applyFilters = () => {
  currentPage.value = 1
  loadTestCases()
}

// 重置筛选
const resetFilters = () => {
  filterForm.value = {
    category_id: null,
    status: '',
    priority: ''
  }
  currentPage.value = 1
  loadTestCases()
}

// 根据分类ID获取分类名称
const getCategoryName = (categoryId: number | undefined): string => {
  if (!categoryId) return '未分类'
  
  // 递归查找分类名称
  const findCategoryName = (categories: Category[], targetId: number): string | null => {
    for (const category of categories) {
      if (category.id === targetId) {
        return category.name
      }
      if (category.children) {
        const found = findCategoryName(category.children, targetId)
        if (found) return found
      }
    }
    return null
  }
  
  const categoryName = findCategoryName(categoryOptions.value, categoryId)
  return categoryName || '未知分类'
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

const handleCommand = (command: string, testCase: TestCase) => {
  switch (command) {
    case 'view':
      viewTestCase(testCase)
      break
    case 'edit':
      editTestCase(testCase)
      break
    case 'delete':
      deleteTestCase(testCase)
      break
    case 'execute':
      executeTestCase(testCase)
      break
    case 'record':
      viewExecutions(testCase)
      break
  }
}

const handleTestCaseCreated = () => {
  currentPage.value = 1
  loadTestCases()
}

const viewTestCase = (testCase: TestCase) => {
  selectedTestCase.value = testCase
  showViewDialog.value = true
}

const editTestCase = (testCase: TestCase) => {
  selectedTestCase.value = testCase
  showEditDialog.value = true
}

const handleEditFromView = (testCase: TestCase) => {
  selectedTestCase.value = testCase
  showViewDialog.value = false
  showEditDialog.value = true
}

const handleTestCaseUpdated = () => {
  loadTestCases()
}

const executeTestCase = async (testCase: TestCase) => {
  try {
    await testExecutionApi.execute(testCase.id, true)
    ElMessage.success('测试用例执行已启动')
  } catch (error) {
    ElMessage.error('执行测试用例失败')
  }
}

const viewExecutions = (testCase: TestCase) => {
  router.push({
    name: 'test-case-executions',
    params: { testCaseId: testCase.id.toString() }
  })
}

const deleteTestCase = async (testCase: TestCase) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除测试用例 "${testCase.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await testCaseApi.delete(testCase.id)
    ElMessage.success('删除成功')
    loadTestCases()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleSelectionChange = (selection: TestCase[]) => {
  // 更新批量执行表单中的选中测试用例
  batchExecuteForm.value.selectedTestCases = selection.map(item => item.id)
}

// 处理执行方式变化
const handleExecutionTypeChange = () => {
  // 重置相关字段
  if (batchExecuteForm.value.executionType === 'manual') {
    batchExecuteForm.value.selectedCategoryId = null
  } else {
    batchExecuteForm.value.selectedTestCases = []
  }
}

// 处理分类选择变化
const handleCategorySelectionChange = (value: number | number[] | null) => {
  if (Array.isArray(value)) {
    // 当 checkStrictly: true 时，value 可能是数组，取最后一个值
    batchExecuteForm.value.selectedCategoryId = value.length > 0 ? value[value.length - 1] : null
  } else {
    // 当 checkStrictly: true 时，value 也可能是单个值
    batchExecuteForm.value.selectedCategoryId = value
  }
}

// 关闭批量执行对话框
const closeBatchExecuteDialog = () => {
  showBatchExecuteDialog.value = false
  // 重置表单
  batchExecuteForm.value = {
    executionType: 'manual',
    selectedTestCases: [],
    selectedCategoryId: null,
    headless: true
  }
}

const handleBatchExecute = async () => {
  let testCaseIds: number[] = []
  
  if (batchExecuteForm.value.executionType === 'manual') {
    if (batchExecuteForm.value.selectedTestCases.length === 0) {
      ElMessage.warning('请至少选择一个测试用例')
      return
    }
    testCaseIds = batchExecuteForm.value.selectedTestCases
  } else {
    if (!batchExecuteForm.value.selectedCategoryId) {
      ElMessage.warning('请选择一个分类')
      return
    }
    
    try {
      // 获取分类下的所有测试用例ID（包括子分类）
      const categoryData = await categoryApi.getTestCases(
        batchExecuteForm.value.selectedCategoryId,
        true // 包含子分类
      )
      
      if (categoryData.test_case_ids.length === 0) {
        ElMessage.warning('该分类下没有测试用例')
        return
      }
      
      testCaseIds = categoryData.test_case_ids
    } catch (error) {
      ElMessage.error('获取分类测试用例失败')
      return
    }
  }
  
  batchExecuting.value = true
  try {
    // 调用批量执行API
    const result = await batchExecutionApi.create(
      testCaseIds,
      batchExecuteForm.value.headless
    )
    
    if (result.success) {
      ElMessage.success('批量执行任务已创建，请在批量执行页面点击执行按钮开始执行')
      showBatchExecuteDialog.value = false
      // 重置表单
      batchExecuteForm.value.selectedTestCases = []
      batchExecuteForm.value.selectedCategoryId = null
      
      // 跳转到批量执行任务页面
      router.push({
        name: 'batch-executions'
      })
    } else {
      ElMessage.error(result.message || '批量执行任务创建失败')
    }
  } catch (error) {
    ElMessage.error('批量执行任务创建失败')
  } finally {
    batchExecuting.value = false
  }
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

const getStatusType = (status: string): string => {
  const types = {
    active: 'success',
    inactive: 'info',
    draft: 'warning'
  }
  return types[status as keyof typeof types] || 'info'
}

const getStatusLabel = (status: string): string => {
  const labels = {
    active: '激活',
    inactive: '非激活',
    draft: '草稿'
  }
  return labels[status as keyof typeof labels] || status
}

const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleString('zh-CN')
}

onMounted(() => {
  loadTestCases()
  loadCategoryTree()
})
</script>

<style scoped>
.test-cases {
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
  gap: 10px; /* Space between buttons */
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
  padding: 20px 0;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>