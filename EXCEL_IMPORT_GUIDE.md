# Excel导入功能使用指南

## 功能概述

AutoTest系统现在支持从Excel文件导入测试用例，支持智能分析和自动转换功能。

## 功能特性

- ✅ **Excel文件支持**: 支持.xlsx和.xls格式
- ✅ **智能预览**: 上传前可预览Excel内容
- ✅ **大模型分析**: 使用AI智能分析Excel内容并转换为测试用例格式
- ✅ **备用转换**: 当AI分析失败时，使用规则引擎进行转换
- ✅ **批量导入**: 支持一次性导入多个测试用例
- ✅ **导入选项**: 可设置默认状态、优先级和分类

## 使用方法

### 1. 前端界面操作

1. 访问测试用例管理页面: http://localhost:3000
2. 点击页面右上角的"导入Excel"按钮
3. 在弹出的对话框中上传Excel文件
4. 设置导入选项（默认状态、优先级、分类）
5. 点击"开始导入"完成导入

### 2. API接口调用

#### 预览Excel文件
```bash
curl -X POST -F "file=@your_file.xlsx" http://localhost:8000/test-cases/preview-excel
```

#### 导入Excel文件
```bash
curl -X POST \
  -F "file=@your_file.xlsx" \
  -F 'options={"defaultStatus":"active","defaultPriority":"medium","defaultCategory":"导入"}' \
  http://localhost:8000/test-cases/import-excel
```

## Excel文件格式

### 支持的列名

系统支持以下列名（中英文均可）：

| 字段 | 支持的列名 |
|------|------------|
| 名称 | name, 名称, Name |
| 描述 | description, 描述, Description |
| 任务内容 | task_content, 任务内容, Task, 内容 |
| 分类 | category, 分类, Category |
| 优先级 | priority, 优先级, Priority |
| 状态 | status, 状态, Status |
| 期望结果 | expected_result, 期望结果, Expected Result |

### 优先级映射

| Excel中的值 | 系统值 |
|-------------|--------|
| 低/low | low |
| 中/medium | medium |
| 高/high | high |
| 紧急/critical | critical |

### 状态映射

| Excel中的值 | 系统值 |
|-------------|--------|
| 激活/active | active |
| 非激活/inactive | inactive |
| 草稿/draft | draft |

## 示例Excel文件

```python
# 生成示例Excel文件的Python脚本
import pandas as pd

test_data = [
    {
        "name": "登录功能测试",
        "description": "测试用户登录功能",
        "task_content": "打开登录页面，输入用户名和密码，点击登录按钮",
        "category": "用户管理",
        "priority": "高",
        "status": "激活",
        "expected_result": "成功登录并跳转到主页"
    },
    {
        "name": "注册功能测试",
        "description": "测试用户注册功能",
        "task_content": "打开注册页面，填写用户信息，点击注册按钮",
        "category": "用户管理",
        "priority": "中",
        "status": "激活",
        "expected_result": "成功注册新用户"
    }
]

df = pd.DataFrame(test_data)
df.to_excel("test_cases.xlsx", index=False)
```

## 智能分析功能

### 大模型分析

系统会尝试使用配置的AI模型分析Excel内容：

1. 将Excel内容转换为文本格式
2. 构建分析提示词
3. 调用AI模型进行分析
4. 解析AI返回的JSON格式测试用例

### 备用转换规则

当AI分析失败时，系统使用以下规则进行转换：

1. **列名匹配**: 自动匹配中英文列名
2. **值映射**: 自动映射优先级和状态值
3. **默认值**: 使用导入选项中设置的默认值
4. **数据清理**: 自动处理空值和格式问题

## 错误处理

### 常见错误及解决方案

1. **文件格式错误**
   - 错误: "只支持Excel文件格式"
   - 解决: 确保文件是.xlsx或.xls格式

2. **文件读取失败**
   - 错误: "读取Excel文件失败"
   - 解决: 检查文件是否损坏，重新生成Excel文件

3. **大模型分析失败**
   - 错误: "大模型分析失败"
   - 解决: 系统会自动使用备用转换规则，不影响导入功能

4. **数据验证失败**
   - 错误: "创建测试用例失败"
   - 解决: 检查Excel数据格式，确保必填字段不为空

## 测试验证

### 运行测试脚本

```bash
# 生成测试Excel文件
python3 test_excel_import.py

# 运行完整测试流程
python3 test_import_workflow.py
```

### 验证导入结果

1. 检查数据库中新增的测试用例
2. 验证字段映射是否正确
3. 确认导入选项是否生效

## 技术实现

### 后端API

- `POST /test-cases/preview-excel`: 预览Excel文件
- `POST /test-cases/import-excel`: 导入Excel文件

### 前端组件

- `ImportExcelDialog.vue`: Excel导入对话框组件
- 支持拖拽上传和文件选择
- 实时预览和数据验证

### 依赖库

- `openpyxl`: Excel文件读取
- `pandas`: 数据处理
- `browser-use`: AI模型调用

## 注意事项

1. **文件大小限制**: 建议Excel文件不超过10MB
2. **数据格式**: 确保Excel数据格式规范
3. **网络连接**: AI分析功能需要网络连接
4. **模型配置**: 确保AI模型配置正确

## 更新日志

- **v1.0.0**: 初始版本，支持基本的Excel导入功能
- 支持AI智能分析和备用转换规则
- 完整的前端界面和API接口 