import axios from 'axios'
import type { TestCase, TestExecution, Statistics, ModelConfig, ModelConfigResponse, TestConfigResult, PromptConfig, PromptConfigResponse, BatchExecution, Category, CategoryCreate, CategoryUpdate } from '@/types/api'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ? `${import.meta.env.VITE_API_BASE_URL}/api/` : '/api/',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    console.log('API Request:', config.method?.toUpperCase(), config.url)
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

// 测试用例相关API
export const testCaseApi = {
  // 获取测试用例列表
  getList: (params?: { skip?: number; limit?: number; status?: string; category?: string; category_id?: number; priority?: string }) => 
    api.get<TestCase[]>('/test-cases', { params }) as unknown as Promise<TestCase[]>,
  
  // 获取单个测试用例
  getById: (id: number) => api.get<TestCase>(`/test-cases/${id}`) as unknown as Promise<TestCase>,
  
  // 创建测试用例
  create: (data: Partial<TestCase>) => api.post<TestCase>('/test-cases', data) as unknown as Promise<TestCase>,
  
  // 更新测试用例
  update: (id: number, data: Partial<TestCase>) => api.put<TestCase>(`/test-cases/${id}`, data) as unknown as Promise<TestCase>,
  
  // 删除测试用例
  delete: (id: number) => api.delete(`/test-cases/${id}`) as unknown as Promise<void>
}

// 测试执行相关API
export const testExecutionApi = {
  // 获取执行记录列表
  getList: () => api.get<TestExecution[]>('/test-executions') as unknown as Promise<TestExecution[]>,
  
  // 获取单个执行记录
  getById: (id: number) => api.get<TestExecution>(`/test-executions/${id}`) as unknown as Promise<TestExecution>,
  
  // 获取特定测试用例的执行记录
  getByTestCaseId: (testCaseId: number) => api.get<TestExecution[]>(`/test-executions?test_case_id=${testCaseId}`) as unknown as Promise<TestExecution[]>,
  
  // 执行单个测试用例
  execute: (testCaseId: number, headless: boolean = true) => 
    api.post<TestExecution>('/test-executions', { test_case_id: testCaseId, headless }) as unknown as Promise<TestExecution>,
  
  // 批量执行测试用例
  batchExecute: (testCaseIds: number[], headless: boolean = true) =>
    api.post<TestExecution[]>('/test-executions/batch', { test_case_ids: testCaseIds, headless }) as unknown as Promise<TestExecution[]>,
  
  // 获取执行步骤详情
  getSteps: (executionId: number) => api.get(`/test-executions/${executionId}/steps`) as unknown as Promise<any>
}

// 批量执行任务相关API
export const batchExecutionApi = {
  // 创建批量执行任务
  create: (testCaseIds: number[], headless: boolean = true) =>
    api.post<{ success: boolean; batch_execution_id: number; message: string }>('/test-executions/batch-executions', { test_case_ids: testCaseIds, headless }) as unknown as Promise<{ success: boolean; batch_execution_id: number; message: string }>,
  
  // 获取批量执行任务列表
  getList: (params?: { skip?: number; limit?: number; status?: string }) => 
    api.get<BatchExecution[]>('/test-executions/batch-executions', { params }) as unknown as Promise<BatchExecution[]>,
  
  // 获取特定批量执行任务的详细信息
  getById: (id: number) => api.get<BatchExecution>(`/test-executions/batch-executions/${id}`) as unknown as Promise<BatchExecution>,
  
  // 启动批量执行任务
  start: (id: number) => 
    api.post<{ success: boolean; message: string }>(`/test-executions/batch-executions/${id}/start`) as unknown as Promise<{ success: boolean; message: string }>,
  
  // 停止批量执行任务
  stop: (id: number) => 
    api.post<{ success: boolean; message: string }>(`/test-executions/batch-executions/${id}/stop`) as unknown as Promise<{ success: boolean; message: string }>,
  
  // 获取批量执行任务的状态
  getStatus: (id: number) => api.get<BatchExecution>(`/test-executions/batch-executions/${id}/status`) as unknown as Promise<BatchExecution>
}

// 统计信息API
export const statisticsApi = {
  // 获取统计信息
  getStatistics: () => api.get<Statistics>('/statistics') as unknown as Promise<Statistics>
}

// 分类管理相关API
export const categoryApi = {
  // 获取分类列表
  getList: (params?: { parent_id?: number; include_inactive?: boolean }) => 
    api.get<Category[]>('/categories', { params }) as unknown as Promise<Category[]>,
  
  // 获取分类树形结构
  getTree: (include_inactive?: boolean) => 
    api.get<Category[]>('/categories/tree', { params: { include_inactive } }) as unknown as Promise<Category[]>,
  
  // 获取单个分类
  getById: (id: number) => api.get<Category>(`/categories/${id}`) as unknown as Promise<Category>,
  
  // 获取分类及其子分类
  getWithChildren: (id: number, include_inactive?: boolean) => 
    api.get<Category>(`/categories/${id}/with-children`, { params: { include_inactive } }) as unknown as Promise<Category>,
  
  // 创建分类
  create: (data: CategoryCreate) => api.post<Category>('/categories', data) as unknown as Promise<Category>,
  
  // 更新分类
  update: (id: number, data: CategoryUpdate) => api.put<Category>(`/categories/${id}`, data) as unknown as Promise<Category>,
  
  // 删除分类
  delete: (id: number, force?: boolean) => api.delete(`/categories/${id}`, { params: { force } }) as unknown as Promise<void>,
  
  // 获取分类下的测试用例ID列表
  getTestCases: (id: number, include_children?: boolean) => 
    api.get<{ category_id: number; include_children: boolean; test_case_ids: number[]; count: number }>(`/categories/${id}/test-cases`, { params: { include_children } }) as unknown as Promise<{ category_id: number; include_children: boolean; test_case_ids: number[]; count: number }>
}

// 模型配置相关API
export const modelConfigApi = {
  // 获取模型配置
  getConfig: () => api.get<ModelConfigResponse>('/model-config') as unknown as Promise<ModelConfigResponse>,
  
  // 更新模型配置
  updateConfig: (config: ModelConfig) => api.put<ModelConfigResponse>('/model-config', config) as unknown as Promise<ModelConfigResponse>,
  
  // 测试模型配置
  testConfig: (config: ModelConfig) => api.post<TestConfigResult>('/model-config/test', config) as unknown as Promise<TestConfigResult>
}

// 提示词配置相关API
export const promptConfigApi = {
  // 获取提示词配置
  getConfig: () => api.get<PromptConfigResponse>('/prompt-config') as unknown as Promise<PromptConfigResponse>,
  
  // 更新提示词配置
  updateConfig: (config: PromptConfig) => api.put<PromptConfigResponse>('/prompt-config', config) as unknown as Promise<PromptConfigResponse>
}

// 多模型配置相关API
export const multiModelConfigApi = {
  // 获取多模型配置
  getConfig: () => api.get('/multi-model/config') as unknown as Promise<any>,
  
  // 更新多模型配置
  updateConfig: (config: any) => api.put('/multi-model/config', config) as unknown as Promise<any>,
  
  // 获取配置状态
  getStatus: () => api.get('/multi-model/status') as unknown as Promise<any>,
  
  // 测试多模型配置
  testConfig: () => api.post('/multi-model/test') as unknown as Promise<any>
}

export default api