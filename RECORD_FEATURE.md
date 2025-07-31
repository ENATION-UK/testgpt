# 测试用例记录功能

## 功能概述

在测试用例管理页面中，为每个测试用例添加了"记录"按钮，点击后可以查看该测试用例的所有执行记录历史。

## 功能特性

### 1. 测试用例列表增强
- 在测试用例列表的操作列中添加了"记录"按钮
- 按钮使用蓝色（info）样式，与其他操作按钮区分
- 操作列宽度从200px增加到280px以适应新按钮

### 2. 执行记录页面复用
- 复用了现有的`ExecutionsView.vue`组件
- 支持按测试用例ID过滤显示执行记录
- 动态页面标题：显示"测试用例 {ID} 的执行记录"
- 添加了"返回测试用例"按钮，方便导航

### 3. 路由配置
- 新增路由：`/test-cases/:testCaseId/executions`
- 路由名称：`test-case-executions`
- 支持动态参数传递测试用例ID

### 4. API支持
- 后端已支持按`test_case_id`参数过滤执行记录
- 前端API服务添加了`getByTestCaseId`方法
- 支持两种API调用方式：
  - `/test-executions?test_case_id={id}`
  - `/test-cases/{id}/executions`

## 技术实现

### 前端修改

#### 1. TestCasesView.vue
```vue
<!-- 添加记录按钮 -->
<el-button size="small" type="info" @click="viewExecutions(row)">记录</el-button>

<!-- 添加跳转方法 -->
const viewExecutions = (testCase: TestCase) => {
  router.push({
    name: 'test-case-executions',
    params: { testCaseId: testCase.id.toString() }
  })
}
```

#### 2. ExecutionsView.vue
```vue
<!-- 动态页面标题 -->
<h2>{{ pageTitle }}</h2>

<!-- 返回按钮 -->
<el-button v-if="testCaseId" @click="goBack" type="primary">
  <el-icon><ArrowLeft /></el-icon>
  返回测试用例
</el-button>

<!-- 计算属性 -->
const testCaseId = computed(() => {
  const id = route.params.testCaseId
  return id ? parseInt(id as string) : null
})

const pageTitle = computed(() => {
  return testCaseId.value ? `测试用例 ${testCaseId.value} 的执行记录` : '执行记录'
})
```

#### 3. 路由配置 (router/index.ts)
```typescript
{
  path: '/test-cases/:testCaseId/executions',
  name: 'test-case-executions',
  component: () => import('../views/ExecutionsView.vue')
}
```

#### 4. API服务 (services/api.ts)
```typescript
// 获取特定测试用例的执行记录
getByTestCaseId: (testCaseId: number) => 
  api.get<TestExecution[]>(`/test-executions?test_case_id=${testCaseId}`) as unknown as Promise<TestExecution[]>
```

### 后端支持

后端API已经支持按测试用例ID过滤执行记录：

```python
@app.get("/test-executions", response_model=List[TestExecutionResponse])
async def get_test_executions(
    skip: int = 0,
    limit: int = 100,
    test_case_id: Optional[int] = None,  # 支持按测试用例ID过滤
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(TestExecution)
    
    if test_case_id:
        query = query.filter(TestExecution.test_case_id == test_case_id)
    # ...
```

## 使用流程

1. **访问测试用例列表**
   - 打开前端应用，进入"测试用例管理"页面

2. **查看记录**
   - 在测试用例列表中找到目标测试用例
   - 点击该测试用例的"记录"按钮

3. **查看执行历史**
   - 页面会跳转到该测试用例的执行记录页面
   - 显示该测试用例的所有执行记录
   - 页面标题显示"测试用例 {ID} 的执行记录"

4. **返回列表**
   - 点击"返回测试用例"按钮可以返回到测试用例列表

## 测试验证

运行测试脚本验证功能：

```bash
python3 test_record_feature.py
```

测试脚本会：
1. 获取现有测试用例
2. 执行测试用例生成记录
3. 验证API端点正常工作
4. 确认数据过滤功能正常

## 兼容性

- 完全向后兼容，不影响现有功能
- 复用了现有的执行记录页面组件
- 保持了原有的UI风格和交互模式
- 支持响应式设计

## 未来扩展

可以考虑的扩展功能：
- 在记录页面添加筛选和排序功能
- 添加执行记录的导出功能
- 支持批量查看多个测试用例的记录
- 添加执行记录的统计分析图表 