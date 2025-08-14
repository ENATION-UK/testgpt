# AutoTest 数据库配置说明

## 概述

本项目已重构数据库配置，实现了SQLite数据库文件的外部化，确保在Docker环境中数据持久化，重启容器后数据不会丢失。

## 配置架构

### 1. 配置管理器 (ConfigManager)

- **配置目录**: 存储配置文件（如模型配置、提示词配置等）
- **数据目录**: 存储数据文件（数据库、截图、历史记录等）
- **智能路径选择**: 自动识别运行环境（本地/Docker）

### 2. 数据库配置 (DatabaseConfig)

- **外部化存储**: 数据库文件存储在宿主机的数据目录中
- **环境变量支持**: 可通过环境变量配置数据库路径
- **权限管理**: 自动确保目录存在和权限正确

## 环境变量配置

### 必需环境变量

```bash
# Docker环境标识
DOCKER_ENV=true

# 数据目录路径
DATA_DIR=/app/data

# 数据库文件名
DB_NAME=autotest.db
```

### 可选环境变量

```bash
# 是否使用MySQL（默认false，使用SQLite）
USE_MYSQL=false

# 是否启用SQL日志
ENABLE_SQL_ECHO=false
```

## 目录结构

```
docker/
├── data/                    # 数据目录（挂载到容器）
│   ├── autotest.db         # SQLite数据库文件
│   ├── screenshots/        # 测试截图
│   ├── history/            # 历史记录
│   └── test_history_cache/ # 测试历史缓存
├── docker-compose.yml      # Docker编排文件
├── Dockerfile.backend      # 后端镜像构建文件
├── start-backend.sh        # 标准启动脚本
└── start-centos.sh         # CentOS专用启动脚本
```

## 启动方式

### 1. 标准启动

```bash
cd docker
./start-backend.sh
```

### 2. CentOS环境启动

```bash
cd docker
./start-centos.sh
```

### 3. 手动启动

```bash
cd docker

# 确保数据目录存在
mkdir -p ./data
chmod 755 ./data

# 启动服务
docker-compose up --build backend
```

## 数据持久化

### 工作原理

1. **数据卷挂载**: `./data:/app/data` 将宿主机的data目录挂载到容器内
2. **外部化存储**: 数据库文件存储在宿主机的data目录中
3. **权限管理**: 容器启动时自动设置正确的目录权限
4. **表结构检查**: 启动时检查表是否存在，不存在则自动创建

### 优势

- ✅ **数据持久化**: 重启容器后数据不丢失
- ✅ **外部访问**: 可以直接访问宿主机的数据库文件
- ✅ **备份方便**: 可以直接备份data目录
- ✅ **开发友好**: 本地开发时可以直接查看数据库内容

## 故障排除

### 常见问题

#### 1. 数据库权限错误

```bash
# 检查数据目录权限
ls -la ./data

# 重新设置权限
chmod 755 ./data
chown -R $USER:$USER ./data
```

#### 2. 数据库文件无法创建

```bash
# 检查目录是否存在
mkdir -p ./data

# 检查磁盘空间
df -h

# 检查SELinux状态（CentOS）
getenforce
```

#### 3. 容器启动失败

```bash
# 查看容器日志
docker-compose logs backend

# 重新构建镜像
docker-compose build --no-cache backend

# 清理并重启
docker-compose down
docker-compose up --build backend
```

### 调试命令

```bash
# 进入容器检查
docker-compose exec backend bash

# 检查数据库文件
ls -la /app/data/

# 检查用户权限
id
whoami

# 检查数据库连接
python -c "from autotest.database import test_connection; test_connection()"
```

## 迁移说明

### 从旧版本升级

1. **备份现有数据**（如果有）
2. **停止现有服务**
3. **使用新配置启动**
4. **验证数据完整性**

### 数据迁移

```bash
# 如果有旧的数据库文件
cp old_autotest.db ./data/autotest.db

# 启动服务，系统会自动检查并创建缺失的表
./start-backend.sh
```

## 最佳实践

1. **定期备份**: 定期备份`./data`目录
2. **权限管理**: 确保数据目录有正确的读写权限
3. **环境隔离**: 不同环境使用不同的数据目录
4. **监控日志**: 关注启动日志中的数据库相关信息

## 技术支持

如果遇到问题，请检查：

1. 数据目录权限
2. 环境变量配置
3. 容器日志输出
4. 宿主机的磁盘空间和权限设置
