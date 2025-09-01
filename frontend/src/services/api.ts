import axios from 'axios'
import type { TestCase, TestExecution, Statistics, ModelConfig, ModelConfigResponse, TestConfigResult, PromptConfig, PromptConfigResponse, BatchExecution, Category, CategoryCreate, CategoryUpdate, ImportTask, ImportTaskCreate, ImportTaskStatus, ImportTaskListResponse } from '@/types/api'

// 动态获取API基础URL
function getApiBaseUrl(): string {
  // 优先使用运行时环境变量（通过window对象）
  if (typeof window !== 'undefined' && (window as any).__APP_CONFIG__?.API_BASE_URL) {
    return (window as any).__APP_CONFIG__.API_BASE_URL
  }
  
  // 其次使用构建时环境变量
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL
  }
  
  // 最后使用默认值
  return '/api'
}

// 调试信息
console.log('API Configuration:', {
  runtimeConfig: typeof window !== 'undefined' ? (window as any).__APP_CONFIG__ : 'N/A',
  buildTimeEnv: import.meta.env.VITE_API_BASE_URL,
  finalApiUrl: getApiBaseUrl()
})

const api = axios.create({
  baseURL: getApiBaseUrl(),
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    console.log('API Request:', config.method?.toUpperCase(), config.url, 'Base URL:', config.baseURL)
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

// 定义分页响应类型
export interface PaginatedResponse<T> {
  test_cases: T[];
  total: number;
  skip: number;
  limit: number;
}

// 批量执行任务中的测试用例类型定义（提前定义）
export interface BatchExecutionTestCase {
  id: number;
  batch_execution_id: number;
  test_case_id: number;
  execution_id?: number;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  overall_status?: 'PASSED' | 'FAILED' | 'PARTIAL';
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  test_case_name: string;
}

// 测试用例相关API
export const testCaseApi = {
  // 获取测试用例列表（支持分页）
  getList: (params?: { skip?: number; limit?: number; status?: string; category?: string; category_id?: number; priority?: string }) => 
    api.get<PaginatedResponse<TestCase>>('/test-cases/', { params }) as unknown as Promise<PaginatedResponse<TestCase>>,
  
  // 获取单个测试用例
  getById: (id: number) => api.get<TestCase>(`/test-cases/${id}/`) as unknown as Promise<TestCase>,
  
  // 创建测试用例
  create: (data: Partial<TestCase>) => api.post<TestCase>('/test-cases/', data) as unknown as Promise<TestCase>,
  
  // 更新测试用例
  update: (id: number, data: Partial<TestCase>) => api.put<TestCase>(`/test-cases/${id}/`, data) as unknown as Promise<TestCase>,
  
  // 删除测试用例
  delete: (id: number) => api.delete(`/test-cases/${id}/`) as unknown as Promise<void>,
  
  // 批量删除测试用例
  batchDelete: (ids: number[]) => api.delete('/test-cases/batch/delete/', { data: ids }) as unknown as Promise<{message: string; deleted_count: number; requested_count: number; deleted_names: string[]}>,
  
  // 预览Excel文件
  previewExcel: (formData: FormData) => 
    api.post('/test-cases/preview-excel/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    }) as unknown as Promise<{ preview: any[]; total_rows: number }>,
  
  // 导入Excel文件
  importExcel: (formData: FormData) => 
    api.post('/test-cases/import-excel/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    }) as unknown as Promise<{ success: boolean; imported_count: number; total_rows: number; message: string }>
}

// 测试执行相关API
export const testExecutionApi = {
  // 获取执行记录列表
  getList: () => api.get<TestExecution[]>('/test-executions/') as unknown as Promise<TestExecution[]>,
  
  // 获取单个执行记录
  getById: (id: number) => api.get<TestExecution>(`/test-executions/${id}/`) as unknown as Promise<TestExecution>,
  
  // 获取特定测试用例的执行记录
  getByTestCaseId: (testCaseId: number) => api.get<TestExecution[]>(`/test-executions/?test_case_id=${testCaseId}`) as unknown as Promise<TestExecution[]>,
  
  // 执行单个测试用例
  execute: (testCaseId: number, headless: boolean = true) => 
    api.post<TestExecution>('/test-executions/', { test_case_id: testCaseId, headless }) as unknown as Promise<TestExecution>,
  
  // 批量执行测试用例
  batchExecute: (testCaseIds: number[], headless: boolean = true) =>
    api.post<TestExecution[]>('/test-executions/batch/', { test_case_ids: testCaseIds, headless }) as unknown as Promise<TestExecution[]>,
  
  // 获取执行步骤详情
  getSteps: (executionId: number) => api.get(`/test-executions/${executionId}/steps/`) as unknown as Promise<any>
}

// 批量执行任务相关API
export const batchExecutionApi = {
  // 创建批量执行任务
  create: (testCaseIds: number[], headless: boolean = true) =>
    api.post<{ success: boolean; batch_execution_id: number; message: string }>('/test-executions/batch-executions/', { test_case_ids: testCaseIds, headless }) as unknown as Promise<{ success: boolean; batch_execution_id: number; message: string }>,
  
  // 获取批量执行任务列表
  getList: (params?: { skip?: number; limit?: number; status?: string }) => 
    api.get<BatchExecution[]>('/test-executions/batch-executions/', { params }) as unknown as Promise<BatchExecution[]>,
  
  // 获取特定批量执行任务的详细信息
  getById: (id: number) => api.get<BatchExecution>(`/test-executions/batch-executions/${id}/`) as unknown as Promise<BatchExecution>,
  
  // 获取特定批量执行任务的测试用例详情（支持分页和搜索）
  getTestCases: (id: number, params?: { skip?: number; limit?: number; search?: string }) => 
    api.get(`/test-executions/batch-executions/${id}/test-cases/`, { params }) as unknown as Promise<{ test_cases: BatchExecutionTestCase[]; total: number; skip: number; limit: number }>,
  
  // 启动批量执行任务
  start: (id: number) => 
    api.post<{ success: boolean; message: string }>(`/test-executions/batch-executions/${id}/start/`) as unknown as Promise<{ success: boolean; message: string }>,
  
  // 停止批量执行任务
  stop: (id: number) => 
    api.post<{ success: boolean; message: string }>(`/test-executions/batch-executions/${id}/stop/`) as unknown as Promise<{ success: boolean; message: string }>,
  
  // 获取批量执行任务的状态
  getStatus: (id: number) => api.get<BatchExecution>(`/test-executions/batch-executions/${id}/status/`) as unknown as Promise<BatchExecution>
}

// 统计信息API
export const statisticsApi = {
  // 获取统计信息
  getStatistics: () => api.get<Statistics>('/statistics/') as unknown as Promise<Statistics>
}

// 分类管理相关API
export const categoryApi = {
  // 获取分类列表
  getList: (params?: { parent_id?: number; include_inactive?: boolean }) => 
    api.get<Category[]>('/categories/', { params }) as unknown as Promise<Category[]>,
  
  // 获取分类树形结构
  getTree: (include_inactive?: boolean) => 
    api.get<Category[]>('/categories/tree/', { params: { include_inactive } }) as unknown as Promise<Category[]>,
  
  // 获取单个分类
  getById: (id: number) => api.get<Category>(`/categories/${id}/`) as unknown as Promise<Category>,
  
  // 获取分类及其子分类
  getWithChildren: (id: number, include_inactive?: boolean) => 
    api.get<Category>(`/categories/${id}/with-children/`, { params: { include_inactive } }) as unknown as Promise<Category>,
  
  // 创建分类
  create: (data: CategoryCreate) => api.post<Category>('/categories/', data) as unknown as Promise<Category>,
  
  // 更新分类
  update: (id: number, data: CategoryUpdate) => api.put<Category>(`/categories/${id}/`, data) as unknown as Promise<Category>,
  
  // 删除分类
  delete: (id: number, force?: boolean) => api.delete(`/categories/${id}/`, { params: { force } }) as unknown as Promise<void>,
  
  // 获取分类下的测试用例ID列表
  getTestCases: (id: number, include_children?: boolean) => 
    api.get<{ category_id: number; include_children: boolean; test_case_ids: number[]; count: number }>(`/categories/${id}/test-cases/`, { params: { include_children } }) as unknown as Promise<{ category_id: number; include_children: boolean; test_case_ids: number[]; count: number }>
}

// 模型配置相关API
export const modelConfigApi = {
  // 获取模型配置
  getConfig: () => api.get<ModelConfigResponse>('/model-config/') as unknown as Promise<ModelConfigResponse>,
  
  // 更新模型配置
  updateConfig: (config: ModelConfig) => api.put<ModelConfigResponse>('/model-config/', config) as unknown as Promise<ModelConfigResponse>,
  
  // 测试模型配置
  testConfig: (config: ModelConfig) => api.post<TestConfigResult>('/model-config/test/', config) as unknown as Promise<TestConfigResult>
}

// 提示词配置相关API
export const promptConfigApi = {
  // 获取提示词配置
  getConfig: () => api.get<PromptConfigResponse>('/prompt-config/') as unknown as Promise<PromptConfigResponse>,
  
  // 更新提示词配置
  updateConfig: (config: PromptConfig) => api.put<PromptConfigResponse>('/prompt-config/', config) as unknown as Promise<PromptConfigResponse>
}

// 多模型配置相关API
export const multiModelConfigApi = {
  // 获取多模型配置
  getConfig: () => api.get('/multi-model/config/') as unknown as Promise<any>,
  
  // 更新多模型配置
  updateConfig: (config: any) => api.put('/multi-model/config/', config) as unknown as Promise<any>,
  
  // 获取配置状态
  getStatus: () => api.get('/multi-model/status/') as unknown as Promise<any>,
  
  // 测试多模型配置
  testConfig: () => api.post('/multi-model/test/') as unknown as Promise<any>
}

// Excel导入任务相关API
export const importTaskApi = {
  // 创建导入任务
  create: (formData: FormData) => 
    api.post<ImportTask>('/import-tasks/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    }) as unknown as Promise<ImportTask>,
  
  // 获取导入任务列表
  getList: (limit?: number) => 
    api.get<ImportTaskListResponse>('/import-tasks/', { params: { limit } }) as unknown as Promise<ImportTaskListResponse>,
  
  // 获取单个导入任务
  getById: (id: number) => 
    api.get<ImportTask>(`/import-tasks/${id}/`) as unknown as Promise<ImportTask>,
  
  // 获取任务状态
  getStatus: (id: number) => 
    api.get<ImportTaskStatus>(`/import-tasks/${id}/status/`) as unknown as Promise<ImportTaskStatus>,
  
  // 取消任务
  cancel: (id: number) => 
    api.post<{ success: boolean; message: string }>(`/import-tasks/${id}/cancel/`) as unknown as Promise<{ success: boolean; message: string }>,
  
  // 检查是否有正在运行的任务
  hasRunning: () => 
    api.get<{ has_running_task: boolean }>('/import-tasks/has-running/') as unknown as Promise<{ has_running_task: boolean }>
}

export default api