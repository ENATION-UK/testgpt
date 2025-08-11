# Docker构建优化总结

## 问题背景
在构建Docker镜像时遇到以下问题：
1. 每次构建都需要重新安装系统依赖，耗时很长（800+秒）
2. Playwright浏览器在容器重启后丢失
3. 网络代理配置复杂

## 解决方案

### 1. 多阶段构建优化
创建了基础镜像 `autotest-base:latest`，包含：
- Python 3.11
- 所有系统依赖（字体、库文件等）
- Playwright及其浏览器
- 非root用户配置

### 2. 构建脚本优化
创建了两个构建脚本：

#### `build-optimized.sh` - 完整构建脚本
- 构建基础镜像（只需执行一次）
- 构建应用镜像（基于基础镜像，速度很快）
- 自动启动服务

#### `build-quick.sh` - 快速构建脚本
- 用于日常开发调试
- 假设基础镜像已存在
- 可选择只构建后端、前端或全部

### 3. 性能提升对比

| 构建类型 | 优化前 | 优化后 | 提升 |
|---------|--------|--------|------|
| 首次构建 | 800+秒 | 500+秒 | ~37% |
| 后续构建 | 800+秒 | 70-80秒 | ~90% |
| 仅应用层 | 800+秒 | 70-80秒 | ~90% |

### 4. 文件结构

```
docker/
├── Dockerfile.base          # 基础镜像（包含系统依赖和Playwright）
├── Dockerfile.backend       # 后端镜像（基于基础镜像）
├── Dockerfile.frontend      # 前端镜像
├── build-optimized.sh       # 完整构建脚本
├── build-quick.sh          # 快速构建脚本
└── docker-compose.yml      # 服务编排
```

## 使用方法

### 首次使用
```bash
# 完整构建（包含基础镜像）
./docker/build-optimized.sh
```

### 日常开发
```bash
# 快速构建（仅应用层）
./docker/build-quick.sh
```

### 手动构建
```bash
# 构建基础镜像（只需一次）
docker build -f docker/Dockerfile.base -t autotest-base:latest .

# 构建后端镜像（基于基础镜像）
docker build -f docker/Dockerfile.backend -t docker-backend:latest backend

# 构建前端镜像
docker build -f docker/Dockerfile.frontend -t docker-frontend:latest frontend
```

## 解决的问题

### ✅ 已解决
1. **构建时间优化**：从800+秒减少到70-80秒（后续构建）
2. **Playwright浏览器问题**：浏览器已预装在基础镜像中
3. **网络代理配置**：在Dockerfile中配置了代理环境变量
4. **系统依赖安装**：所有依赖已预装在基础镜像中

### 🔄 当前状态
- Docker镜像构建成功
- Playwright浏览器可以正常启动
- 应用层面的LLM配置问题需要进一步调试

## 优势

1. **构建速度大幅提升**：后续构建时间减少90%
2. **开发效率提高**：日常调试只需重新构建应用层
3. **稳定性增强**：基础镜像包含所有必要依赖
4. **维护性更好**：系统依赖和应用代码分离

## 注意事项

1. 基础镜像较大（包含浏览器），但只需构建一次
2. 首次构建仍需要较长时间，但后续构建很快
3. 如果系统依赖有更新，需要重新构建基础镜像 