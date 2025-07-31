# AutoTest API 接口文档

## 基础信息
- 基础URL: `http://localhost:8000`
- 文档地址: `http://localhost:8000/docs`
- 内容类型: `application/json`

## 接口列表

### 1. 健康检查
- **路径**: `GET /health`
- **响应**:
```json
{
  "status": "healthy",
  "service": "autotest-api",
  "timestamp": "2025-07-31T04:47:09.220812"
}
```

### 2. 测试用例管理

#### 2.1 获取测试用例列表
- **路径**: `GET /test-cases`
- **查询参数**:
  - `skip` (int, 可选): 跳过数量，默认0
  - `limit` (int, 可选): 限制数量，默认100
  - `status` (string, 可选): 状态筛选
  - `category` (string, 可选): 分类筛选
  - `priority` (string, 可选): 优先级筛选
- **响应**: `TestCaseResponse[]`

#### 2.2 获取特定测试用例
- **路径**: `GET /test-cases/{test_case_id}`
- **路径参数**: `test_case_id` (int)
- **响应**: `TestCaseResponse`

#### 2.3 创建测试用例
- **路径**: `POST /test-cases`
- **请求体**: `TestCaseCreate`
- **响应**: `TestCaseResponse`

#### 2.4 更新测试用例
- **路径**: `PUT /test-cases/{test_case_id}`
- **路径参数**: `test_case_id` (int)
- **请求体**: `TestCaseUpdate`
- **响应**: `TestCaseResponse`

#### 2.5 删除测试用例
- **路径**: `DELETE /test-cases/{test_case_id}`
- **路径参数**: `test_case_id` (int)
- **响应**:
```json
{
  "message": "测试用例 xxx 已删除"
}
```

#### 2.6 按状态获取测试用例
- **路径**: `GET /test-cases/status/{status}`
- **路径参数**: `status` (string)
- **响应**: `TestCaseResponse[]`

#### 2.7 按分类获取测试用例
- **路径**: `GET /test-cases/category/{category}`
- **路径参数**: `category` (string)
- **响应**: `TestCaseResponse[]`

### 3. 测试执行

#### 3.1 执行单个测试用例
- **路径**: `POST /test-executions`
- **请求体**: `TestExecutionRequest`
- **响应**: `TestExecutionResponse`

#### 3.2 批量执行测试用例
- **路径**: `POST /test-executions/batch`
- **请求体**: `BatchExecutionRequest`
- **响应**: `BatchExecutionResponse`

#### 3.3 获取执行记录列表
- **路径**: `GET /test-executions`
- **查询参数**:
  - `skip` (int, 可选): 跳过数量，默认0
  - `limit` (int, 可选): 限制数量，默认100
  - `test_case_id` (int, 可选): 测试用例ID筛选
  - `status` (string, 可选): 状态筛选
- **响应**: `TestExecutionResponse[]`

#### 3.4 获取特定执行记录
- **路径**: `GET /test-executions/{execution_id}`
- **路径参数**: `execution_id` (int)
- **响应**: `TestExecutionResponse`

#### 3.5 获取执行步骤详情
- **路径**: `GET /test-executions/{execution_id}/steps`
- **路径参数**: `execution_id` (int)
- **响应**: `TestStepResponse[]`

#### 3.6 获取测试用例执行历史
- **路径**: `GET /test-cases/{test_case_id}/executions`
- **路径参数**: `test_case_id` (int)
- **查询参数**:
  - `skip` (int, 可选): 跳过数量，默认0
  - `limit` (int, 可选): 限制数量，默认50
- **响应**: `TestExecutionResponse[]`

### 4. 统计信息

#### 4.1 获取测试统计
- **路径**: `GET /statistics`
- **响应**: `TestStatistics`

## 数据模型

### TestCaseCreate
```json
{
  "name": "string",
  "description": "string (可选)",
  "task_content": "string",
  "status": "string (默认: active)",
  "priority": "string (默认: medium)",
  "category": "string (可选)",
  "tags": "string[] (可选)",
  "expected_result": "string (可选)"
}
```

### TestCaseUpdate
```json
{
  "name": "string (可选)",
  "description": "string (可选)",
  "task_content": "string (可选)",
  "status": "string (可选)",
  "priority": "string (可选)",
  "category": "string (可选)",
  "tags": "string[] (可选)",
  "expected_result": "string (可选)"
}
```

### TestCaseResponse
```json
{
  "id": "integer",
  "name": "string",
  "description": "string (可选)",
  "task_content": "string",
  "status": "string",
  "priority": "string",
  "category": "string (可选)",
  "tags": "string[] (可选)",
  "expected_result": "string (可选)",
  "created_at": "datetime (可选)",
  "updated_at": "datetime (可选)"
}
```

### TestExecutionRequest
```json
{
  "test_case_id": "integer",
  "headless": "boolean (默认: false)"
}
```

### TestExecutionResponse
```json
{
  "id": "integer",
  "test_case_id": "integer",
  "execution_name": "string",
  "status": "string",
  "overall_status": "string (可选)",
  "total_steps": "integer",
  "passed_steps": "integer",
  "failed_steps": "integer",
  "skipped_steps": "integer",
  "total_duration": "float (可选)",
  "summary": "string (可选)",
  "recommendations": "string (可选)",
  "error_message": "string (可选)",
  "started_at": "datetime",
  "completed_at": "datetime (可选)",
  "created_at": "datetime"
}
```

### TestStepResponse
```json
{
  "id": "integer",
  "execution_id": "integer",
  "step_name": "string",
  "step_order": "integer",
  "status": "string",
  "description": "string (可选)",
  "error_message": "string (可选)",
  "screenshot_path": "string (可选)",
  "duration_seconds": "float (可选)",
  "started_at": "datetime",
  "completed_at": "datetime (可选)"
}
```

### BatchExecutionRequest
```json
{
  "test_case_ids": "integer[]",
  "headless": "boolean (默认: false)"
}
```

### BatchExecutionResponse
```json
{
  "success": "boolean",
  "total_count": "integer",
  "passed_count": "integer",
  "failed_count": "integer",
  "results": "object[]"
}
```

### TestStatistics
```json
{
  "total_test_cases": "integer",
  "active_test_cases": "integer",
  "total_executions": "integer",
  "passed_executions": "integer",
  "failed_executions": "integer",
  "success_rate": "float"
}
```

## 状态枚举

### 测试用例状态
- `active`: 活跃
- `inactive`: 非活跃
- `draft`: 草稿

### 优先级
- `low`: 低
- `medium`: 中
- `high`: 高
- `critical`: 紧急

### 执行状态
- `running`: 执行中
- `passed`: 通过
- `failed`: 失败
- `error`: 错误
- `cancelled`: 已取消

### 步骤状态
- `PASSED`: 通过
- `FAILED`: 失败
- `SKIPPED`: 跳过

### 整体状态
- `PASSED`: 通过
- `FAILED`: 失败
- `PARTIAL`: 部分通过 