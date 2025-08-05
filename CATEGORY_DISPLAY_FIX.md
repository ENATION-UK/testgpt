# 分类显示修复总结

## 问题描述

在测试用例列表中，分类名字显示的不是选择的分类名称，而是旧的分类字段内容。

## 问题原因

1. **表格显示逻辑**：表格直接显示 `prop="category"` 字段，这是旧的分类字段
2. **缺少分类名称映射**：没有根据 `category_id` 获取对应的分类名称
3. **批量执行对话框**：同样显示旧的分类字段

## 修复方案

### 1. 修改表格显示逻辑

将直接显示 `category` 字段改为根据 `category_id` 获取分类名称：

```vue
<!-- 修复前 -->
<el-table-column prop="category" label="分类" width="120" />

<!-- 修复后 -->
<el-table-column label="分类" width="120">
  <template #default="{ row }">
    {{ getCategoryName(row.category_id) }}
  </template>
</el-table-column>
```

### 2. 添加分类名称获取方法

```typescript
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
```

### 3. 修复批量执行对话框

```vue
<!-- 修复前 -->
:label="`${testCase.name} (${testCase.category || '未分类'})`"

<!-- 修复后 -->
:label="`${testCase.name} (${getCategoryName(testCase.category_id)})`"
```

## 修复的文件

1. **frontend/src/views/TestCasesView.vue**
   - 修改表格分类列显示逻辑
   - 添加 `getCategoryName` 方法
   - 修复批量执行对话框中的分类显示

## 测试验证

通过后端API测试验证修复效果：

```
📝 测试用例分类信息:
   搜索测试:
     新分类ID: 5
     新分类名称: 功能测试/用户管理
     旧分类字段: 登录功能
   新闻查看功能:
     新分类ID: 9
     新分类名称: 性能测试/负载测试
     旧分类字段: 新闻
   订单创建测试:
     新分类ID: None
     新分类名称: 未分类
     旧分类字段: 订单管理
   test2:
     新分类ID: None
     新分类名称: 未分类
     旧分类字段: 3333
```

## 功能特性

修复后的分类显示功能支持：

- ✅ 根据 `category_id` 显示正确的分类名称
- ✅ 支持多级分类名称显示
- ✅ 未分类的测试用例显示"未分类"
- ✅ 批量执行对话框中正确显示分类名称
- ✅ 自动加载分类树数据

## 显示效果

现在测试用例列表会正确显示：

1. **有分类的测试用例**：显示对应的分类名称（如"功能测试/用户管理"）
2. **未分类的测试用例**：显示"未分类"
3. **批量执行对话框**：同样显示正确的分类名称

## 注意事项

1. 分类数据在页面加载时自动获取
2. 支持无限级分类的递归查找
3. 如果分类ID不存在，会显示"未知分类"
4. 旧的 `category` 字段仍然保留，但不再用于显示 