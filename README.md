# AutoTest - Web自动化测试工具

基于Browser Use的智能Web自动化测试工具，支持语义化测试用例编写和详细的测试结果记录。

<div align="center">
  <h1>itBuilder</h1>

  <p>扫码加入交流群，与开发者交流，贡献创意。</p>

 <img src="https://www.itbuilder.cn/group" alt="加入交流群">

</div>


## 🚀 功能特性

- **智能测试执行**: 基于自然语言描述执行Web自动化测试
- **详细测试报告**: 记录每个测试步骤的执行结果和截图
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

### 克隆项目
```bash
git clone https://gitee.com/enation-inc/autotest.git
cd autotest
```

#### 安装前端依赖
```bash
npm install
cd frontend
npm install
```

#### 安装后端依赖
推荐使用[uv](https://github.com/astral-sh/uv)进行依赖管理
```bash
uv venv 
source .venv/bin/activate

uv sync --all-extras

# Install the default browser
playwright install chromium --with-deps --no-shell
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


## 🐳 Docker部署

### 构建镜像
在中国大陆需要先配置代理:
编辑[docker/build-optimized.sh](docker/build-optimized.sh)中代理部分

```bash
# 构建所有镜像
sh docker/build-optimized.sh -a

# 构建前端镜像
sh docker/build-optimized.sh -f

# 构建后端镜像
sh docker/build-optimized.sh -b
```


### 使用Docker Compose
配置文件[docker/config.env](docker/config.env)中的
`VITE_API_BASE_URL=http://ip:8000/api`
为后端服务的API地址

```bash
cd docker
docker-compose up -d
```


## 🌐 访问应用

- **前端界面**: http://localhost:3000
- **API文档**: http://localhost:8000/docs
- **ReDoc文档**: http://localhost:8000/redoc


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