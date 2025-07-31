# AutoTest - Web自动化测试工具

基于Browser Use的智能Web自动化测试工具，支持语义化测试用例编写和详细的测试结果记录。现在包含完整的Vue.js前端界面。

## 🚀 功能特性

- **智能测试执行**: 基于自然语言描述执行Web自动化测试
- **详细测试报告**: 记录每个测试步骤的执行结果和截图
- **REST API**: 完整的API接口，支持测试用例管理和执行
- **现代化UI**: 基于Vue 3 + Element Plus的现代化用户界面
- **数据库存储**: 使用SQLite/MySQL存储测试用例和执行记录
- **批量执行**: 支持批量执行多个测试用例
- **实时监控**: 实时查看测试执行状态和进度
- **统计图表**: 直观的测试统计和趋势分析

## 📋 系统要求

- Node.js 18+
- Python 3.11+
- Playwright
- FastAPI
- SQLAlchemy

## 🛠️ 快速开始

### 1. 克隆项目
```bash
git clone <repository-url>
cd autotest
```

### 2. 一键启动（推荐）
```bash
# 安装所有依赖并启动服务
npm run setup

# 或者使用脚本
./scripts/dev.sh
```

### 3. 手动安装（可选）

#### 安装前端依赖
```bash
cd frontend
npm install
```

#### 安装后端依赖
```bash
cd backend
# 使用uv安装（推荐）
uv sync

# 或使用pip
pip install -r requirements.txt
```

#### 安装Playwright浏览器
```bash
cd backend
playwright install chromium
```

#### 配置环境变量
```bash
cp env.example .env
# 编辑.env文件，配置数据库和API密钥
```

### 4. 启动服务

#### 开发模式（同时启动前后端）
```bash
npm run dev
```

#### 分别启动
```bash
# 启动后端API服务
npm run dev:backend

# 启动前端开发服务器
npm run dev:frontend
```

## 🌐 访问应用

- **前端界面**: http://localhost:3000
- **API文档**: http://localhost:8000/docs
- **ReDoc文档**: http://localhost:8000/redoc

## 📁 项目结构

```
autotest/
├── backend/                    # Python后端
│   ├── src/autotest/          # 后端源码
│   ├── pyproject.toml         # Python依赖配置
│   └── run.py                 # 后端启动脚本
├── frontend/                   # Vue前端
│   ├── src/                   # 前端源码
│   │   ├── components/        # Vue组件
│   │   ├── views/             # 页面组件
│   │   ├── services/          # API服务
│   │   ├── types/             # TypeScript类型定义
│   │   └── router/            # 路由配置
│   ├── package.json           # 前端依赖配置
│   └── vite.config.ts         # Vite配置
├── shared/                     # 共享配置和类型
├── scripts/                    # 构建和部署脚本
├── docker/                     # Docker配置
├── docs/                       # 文档
└── package.json               # 根目录项目管理
```

## 🎯 主要功能

### 测试用例管理
- 创建、编辑、删除测试用例
- 支持标签和分类管理
- 优先级和状态管理
- 批量操作支持

### 测试执行
- 单个测试用例执行
- 批量测试执行
- 实时执行状态监控
- 详细的执行步骤记录

### 结果分析
- 执行结果统计
- 成功率分析
- 执行时间统计
- 分类和优先级统计

### 用户界面
- 响应式设计
- 现代化UI组件
- 直观的数据展示
- 友好的用户交互

## 🔧 开发指南

### 前端开发
```bash
cd frontend
npm run dev          # 启动开发服务器
npm run build        # 构建生产版本
npm run lint         # 代码检查
npm run format       # 代码格式化
```

### 后端开发
```bash
cd backend
python run.py        # 启动API服务
```

### API开发
后端API基于FastAPI构建，支持：
- 自动生成API文档
- 请求/响应验证
- 异步处理
- 后台任务

## 🐳 Docker部署

### 使用Docker Compose
```bash
cd docker
docker-compose up -d
```

### 构建镜像
```bash
# 构建后端镜像
docker build -f docker/Dockerfile.backend -t autotest-backend .

# 构建前端镜像
docker build -f docker/Dockerfile.frontend -t autotest-frontend .
```

## 📚 API接口说明

详细的API文档请访问：http://localhost:8000/docs

### 主要接口

#### 测试用例管理
- `GET /test-cases` - 获取测试用例列表
- `POST /test-cases` - 创建测试用例
- `PUT /test-cases/{id}` - 更新测试用例
- `DELETE /test-cases/{id}` - 删除测试用例

#### 测试执行
- `POST /test-executions` - 执行单个测试
- `POST /test-executions/batch` - 批量执行测试
- `GET /test-executions` - 获取执行记录
- `GET /test-executions/{id}/steps` - 获取执行步骤

#### 统计信息
- `GET /statistics` - 获取统计信息

## 🔍 故障排除

### 常见问题

1. **前端无法连接后端API**
   - 检查后端服务是否正常运行
   - 确认端口8000未被占用
   - 检查CORS配置

2. **浏览器启动失败**
   - 确保已安装Playwright: `playwright install chromium`
   - 检查系统权限

3. **依赖安装失败**
   - 检查Node.js和Python版本
   - 清除缓存后重新安装

### 日志查看

```bash
# 查看前端日志
cd frontend && npm run dev

# 查看后端日志
cd backend && python run.py
```

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue
- 发送邮件
- 参与讨论

---

**注意**: 请确保在使用前配置正确的API密钥和数据库连接信息。 