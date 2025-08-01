// 测试用例类型定义
export interface TestCase {
  id: number
  name: string
  description: string
  task_content: string
  status: 'active' | 'inactive' | 'draft'
  priority: 'low' | 'medium' | 'high' | 'critical'
  category: string
  tags: string[]
  expected_result: string
  created_at: string
  updated_at: string
}

// 测试执行记录类型定义
export interface TestExecution {
  id: number
  test_case_id: number
  execution_name: string
  status: 'running' | 'passed' | 'failed' | 'error'
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
  description: string
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