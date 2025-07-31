# 模型设置功能使用指南

## 概述

AutoTest项目现在支持通过Web界面配置大语言模型的参数，包括API密钥、模型类型、温度参数等。这个功能让用户可以方便地管理和切换不同的AI模型配置。

## 功能特性

### 🎯 支持的模型类型
- **DeepSeek**: 支持DeepSeek Chat模型
- **OpenAI**: 支持GPT系列模型

### ⚙️ 可配置参数
- **模型类型**: 选择使用DeepSeek或OpenAI
- **API密钥**: 安全的密钥管理
- **基础URL**: API服务地址
- **模型名称**: 具体的模型标识
- **温度参数**: 控制输出随机性 (0-2)
- **最大Token数**: 限制输出长度

### 🔧 功能特性
- **实时配置**: 无需重启服务即可生效
- **配置验证**: 内置配置有效性检查
- **配置测试**: 一键测试配置是否正确
- **安全存储**: API密钥加密存储
- **配置持久化**: 配置自动保存到文件

## 使用方法

### 1. 访问设置页面

在AutoTest Web界面中，点击导航栏的"模型设置"选项，进入配置页面。

### 2. 配置模型参数

#### DeepSeek配置示例
```
模型类型: DeepSeek
API密钥: sk-your-deepseek-api-key
基础URL: https://api.deepseek.com/v1
模型名称: deepseek-chat
温度参数: 0.7
最大Token数: 2000
```

#### OpenAI配置示例
```
模型类型: OpenAI
API密钥: sk-your-openai-api-key
基础URL: https://api.openai.com/v1
模型名称: gpt-4o
温度参数: 0.7
最大Token数: 2000
```

### 3. 测试配置

点击"测试配置"按钮验证配置是否正确：
- ✅ 配置正确：显示"配置测试成功"
- ❌ 配置错误：显示具体错误信息

### 4. 保存配置

点击"保存配置"按钮将配置保存到系统：
- 配置会自动保存到 `backend/model_config.json` 文件
- 所有组件会自动使用新的配置

## 技术实现

### 后端架构

#### API接口
- `GET /model-config`: 获取当前配置
- `PUT /model-config`: 更新配置
- `POST /model-config/test`: 测试配置

#### 配置管理
- 配置文件：`backend/model_config.json`
- 自动加载：`BrowserAgent` 和 `TestExecutor` 自动读取配置
- 配置验证：内置有效性检查

#### 支持的组件
- `BrowserAgent`: 浏览器自动化代理
- `TestExecutor`: 测试执行器
- 所有使用LLM的组件

### 前端架构

#### 页面组件
- `ModelSettingsView.vue`: 模型设置页面
- 响应式表单：实时验证和反馈
- 状态显示：配置状态和测试结果

#### API服务
- `modelConfigApi`: 模型配置相关API
- 类型安全：完整的TypeScript类型定义

## 配置优先级

系统按以下优先级使用配置：

1. **构造函数参数**: 直接传入的参数
2. **配置文件**: `model_config.json` 中的设置
3. **环境变量**: `DEEPSEEK_API_KEY` 等环境变量
4. **默认值**: 代码中的硬编码默认值

## 安全考虑

### API密钥安全
- 前端使用密码输入框，不显示明文
- 后端安全存储到配置文件
- 建议将配置文件添加到 `.gitignore`

### 配置验证
- 内置配置有效性检查
- 测试功能验证API连接
- 错误信息友好提示

## 故障排除

### 常见问题

#### 1. 配置测试失败
**可能原因**:
- API密钥错误或过期
- 网络连接问题
- 模型名称不正确

**解决方案**:
- 检查API密钥是否正确
- 确认网络连接正常
- 验证模型名称和基础URL

#### 2. 配置不生效
**可能原因**:
- 配置文件权限问题
- 服务未重启
- 配置格式错误

**解决方案**:
- 检查文件权限
- 重启后端服务
- 验证JSON格式

#### 3. 前端无法访问
**可能原因**:
- 后端服务未启动
- 跨域配置问题
- 路由配置错误

**解决方案**:
- 启动后端服务
- 检查CORS配置
- 验证路由设置

### 调试方法

#### 1. 查看配置文件
```bash
cat backend/model_config.json
```

#### 2. 检查API响应
```bash
curl http://localhost:8000/model-config
```

#### 3. 查看日志
```bash
# 后端日志
tail -f backend/logs/autotest.log

# 前端控制台
# 打开浏览器开发者工具查看Console
```

## 开发扩展

### 添加新的模型类型

1. **后端扩展**:
   ```python
   # 在 browser_agent.py 中添加新的模型类型
   elif self.model_type == "new_model":
       return NewModelLLM(
           base_url=self.base_url,
           model=self.model,
           api_key=self.api_key,
           temperature=self.temperature,
           max_tokens=self.max_tokens
       )
   ```

2. **前端扩展**:
   ```vue
   <!-- 在 ModelSettingsView.vue 中添加选项 -->
   <el-option label="New Model" value="new_model" />
   ```

### 添加新的配置参数

1. **更新数据模型**:
   ```python
   class ModelConfig(BaseModel):
       # 添加新参数
       new_parameter: Optional[str] = Field(default=None)
   ```

2. **更新前端表单**:
   ```vue
   <el-form-item label="新参数" prop="new_parameter">
       <el-input v-model="form.new_parameter" />
   </el-form-item>
   ```

## 总结

模型设置功能为AutoTest项目提供了灵活的AI模型配置能力，用户可以通过友好的Web界面轻松管理和切换不同的模型配置，大大提升了系统的易用性和可维护性。

通过这个功能，用户可以：
- 快速配置和切换不同的AI模型
- 实时调整模型参数
- 安全管理API密钥
- 验证配置的正确性

这为AutoTest项目的AI能力提供了强有力的支持。 