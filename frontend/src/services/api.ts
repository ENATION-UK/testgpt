import axios from 'axios'
import type { TestCase, TestExecution, Statistics, ModelConfig, ModelConfigResponse, TestConfigResult, PromptConfig, PromptConfigResponse } from '@/types/api'

const api = axios.create({
  baseURL: '/api',
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
  getList: (params?: { skip?: number; limit?: number; status?: string; category?: string; priority?: string }) => 
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

// 统计信息API
export const statisticsApi = {
  // 获取统计信息
  getStatistics: () => api.get<Statistics>('/statistics') as unknown as Promise<Statistics>
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

export default api 