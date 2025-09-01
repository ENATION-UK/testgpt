// 测试用例类型定义
export interface TestCase {
  id: number
  name: string
  task_content: string
  status: string
  priority: string
  category?: string
  category_id?: number
  tags?: string[]
  expected_result?: string
  created_at?: string
  updated_at?: string
}

// 分类相关类型
export interface Category {
  id: number
  name: string
  description?: string
  parent_id?: number
  level: number
  sort_order: number
  is_active: boolean
  created_at?: string
  updated_at?: string
  children?: Category[]
  test_case_count?: number
}

export interface CategoryCreate {
  name: string
  description?: string
  parent_id?: number
  sort_order?: number
}

export interface CategoryUpdate {
  name?: string
  description?: string
  parent_id?: number
  sort_order?: number
  is_active?: boolean
}

// 测试执行记录类型定义
export interface TestExecution {
  id: number
  test_case_id: number
  execution_name: string
  status: 'running' | 'passed' | 'failed' | 'error' | 'cancelled'
  overall_status: 'PASSED' | 'FAILED' | 'PARTIAL'
  total_steps: number
  passed_steps: number
  failed_steps: number
  skipped_steps: number
  total_duration: number
  summary: string
  recommendations: string
  error_message?: string
  started_at: string
  completed_at?: string
  created_at: string
  test_case?: TestCase
}

// 测试步骤类型定义
export interface TestStep {
  id: number
  execution_id: number
  step_name: string
  step_order: number
  status: 'PASSED' | 'FAILED' | 'SKIPPED'
  description?: string
  error_message?: string
  screenshot_path?: string
  duration_seconds?: number
  started_at: string
  completed_at?: string
}

// 统计信息类型定义
export interface Statistics {
  total_test_cases: number
  total_executions: number
  passed_executions: number
  failed_executions: number
  success_rate: number
  average_duration: number
  recent_executions: TestExecution[]
  category_stats: {
    category: string
    count: number
  }[]
  priority_stats: {
    priority: string
    count: number
  }[]
}

// 创建测试用例请求类型
export interface CreateTestCaseRequest {
  name: string
  task_content: string
  status?: 'active' | 'inactive' | 'draft'
  priority?: 'low' | 'medium' | 'high' | 'critical'
  category?: string
  tags?: string[]
  expected_result?: string
}

// 执行测试请求类型
export interface ExecuteTestRequest {
  test_case_id: number
  headless?: boolean
}

// 批量执行测试请求类型
export interface BatchExecuteRequest {
  test_case_ids: number[]
  headless?: boolean
}

// 模型配置相关类型
export interface ModelConfig {
  model_type: string
  api_key: string
  base_url?: string
  model: string
  temperature: number
  max_tokens?: number
}

export interface ModelConfigResponse extends ModelConfig {
  is_valid: boolean
}

export interface TestConfigResult {
  success: boolean
  message: string
}

// 提示词配置相关类型
export interface PromptConfig {
  custom_prompt: string
}

export interface PromptConfigResponse extends PromptConfig {
  is_valid: boolean
}

// 批量执行任务类型定义
export interface BatchExecution {
  id: number
  name: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  total_count: number
  success_count: number
  failed_count: number
  running_count: number
  pending_count: number
  total_duration: number
  headless: boolean
  started_at: string
  completed_at?: string
  created_at: string
  updated_at: string
  test_cases?: BatchExecutionTestCase[]
}

// 批量执行任务中的测试用例类型定义
export interface BatchExecutionTestCase {
  id: number
  batch_execution_id: number
  test_case_id: number
  execution_id?: number
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  overall_status?: 'PASSED' | 'FAILED' | 'PARTIAL'
  started_at?: string
  completed_at?: string
  error_message?: string
  test_case_name: string
}

// Excel导入任务相关类型定义
export interface ImportTask {
  id: number
  name: string
  file_name: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  total_rows: number
  processed_rows: number
  success_rows: number
  failed_rows: number
  current_batch: number
  total_batches: number
  progress_percentage: number
  import_options?: {
    defaultStatus: string
    defaultPriority: string
    defaultCategory: string
  }
  error_log?: Array<{
    type: string
    message: string
    row?: number
    timestamp: string
  }>
  result_summary?: {
    total_rows: number
    success_rows: number
    failed_rows: number
    success_rate: number
  }
  started_at?: string
  completed_at?: string
  created_at: string
  updated_at: string
}

export interface ImportTaskCreate {
  name: string
  file_name: string
  import_options: {
    defaultStatus: string
    defaultPriority: string
    defaultCategory: string
  }
  batch_size?: number
}

export interface ImportTaskStatus {
  task_id: number
  status: string
  progress_percentage: number
  current_batch: number
  total_batches: number
  processed_rows: number
  total_rows: number
  success_rows: number
  failed_rows: number
  error_messages: string[]
}

export interface ImportTaskListResponse {
  tasks: ImportTask[]
  total: number
  has_running_task: boolean
}