# AutoTest 项目重构说明

## 重构概述

原始的 `main.py` 文件包含了所有功能模块，代码量过大（898行），不够优雅。本次重构将其按模块拆分，提高了代码的可维护性和可读性。

## 重构后的项目结构

```
backend/src/autotest/
├── main.py                    # 主应用文件（74行，大幅精简）
├── models.py                  # 数据模型定义
├── routers/                   # 路由模块
│   ├── __init__.py
│   ├── test_cases.py         # 测试用例管理路由
│   ├── test_executions.py    # 测试执行路由
│   ├── statistics.py         # 统计信息路由
│   └── config.py            # 配置管理路由
├── services/                  # 服务层模块
│   ├── __init__.py
│   ├── excel_service.py      # Excel导入服务
│   ├── llm_service.py       # LLM服务
│   ├── execution_service.py  # 测试执行服务
│   └── config_service.py    # 配置管理服务
└── ... (其他原有文件)
```

## 模块说明

### 1. models.py
- 包含所有 Pydantic 数据模型定义
- 测试用例、执行记录、配置等相关模型
- 从 main.py 中提取，便于复用和维护

### 2. routers/ 目录
- **test_cases.py**: 测试用例的 CRUD 操作和 Excel 导入功能
- **test_executions.py**: 测试执行相关的所有端点
- **statistics.py**: 统计信息查询端点
- **config.py**: 模型配置和提示词配置管理

### 3. services/ 目录
- **excel_service.py**: Excel 文件处理和导入逻辑
- **llm_service.py**: 大模型调用和分析逻辑
- **execution_service.py**: 测试执行的后台任务处理
- **config_service.py**: 配置文件的读写和验证

### 4. main.py
- 大幅精简，只保留应用初始化和路由注册
- 从 898 行减少到 74 行
- 更清晰的应用结构

## 重构优势

1. **模块化**: 每个功能模块独立，便于维护和扩展
2. **可读性**: 代码结构清晰，职责分离明确
3. **可维护性**: 修改某个功能时只需要关注对应模块
4. **可测试性**: 每个模块可以独立测试
5. **可复用性**: 服务层可以被多个路由复用

## 使用方式

重构后的使用方式与之前完全相同，所有 API 端点保持不变：

- 测试用例管理: `/test-cases/*`
- 测试执行: `/test-executions/*`
- 统计信息: `/statistics/*`
- 配置管理: `/config/*`

## 迁移说明

1. 所有原有的 API 端点保持不变
2. 数据库模型和业务逻辑完全一致
3. 配置文件格式和位置不变
4. 前端调用方式无需修改

## 后续优化建议

1. 可以考虑进一步拆分服务层，按业务领域划分
2. 添加统一的异常处理和日志记录
3. 增加单元测试覆盖
4. 考虑使用依赖注入容器管理服务实例 