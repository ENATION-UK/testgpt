# Playwright Docker 问题修复总结

## 问题
在Docker环境中运行Playwright时出现系统依赖缺失错误。

## 修改的文件

### 1. `docker/Dockerfile.backend`
**修改内容：**
- 添加了Playwright运行所需的所有系统依赖包
- 创建了专门的`playwright`用户
- 添加了`xvfb`虚拟显示服务器
- 修改了启动命令使用自定义启动脚本

**新增的依赖包：**
```bash
libglib2.0-0 libnspr4 libnss3 libdbus-1-3 libatk1.0-0 
libatspi2.0-0 libxcomposite1 libxdamage1 libxfixes3 
libxrandr2 libgbm1 libxkbcommon0 libasound2 xvfb
```

### 2. `docker/docker-compose.yml`
**修改内容：**
- 添加了`DISPLAY=:99`环境变量
- 添加了`PLAYWRIGHT_BROWSERS_PATH`环境变量
- 增加了`shm_size: '2gb'`共享内存配置

### 3. `backend/src/autotest/test_executor.py`
**修改内容：**
- 增强了浏览器启动参数，添加了更多Docker环境优化选项

**新增的启动参数：**
```bash
--disable-web-security
--disable-background-timer-throttling
--disable-backgrounding-occluded-windows
--disable-renderer-backgrounding
--disable-features=TranslateUI
--disable-ipc-flooding-protection
```

### 4. 新增文件

#### `docker/start-backend.sh`
- 启动Xvfb虚拟显示服务器
- 等待显示服务器就绪
- 启动后端服务

#### `docker/rebuild-and-restart.sh`
- 自动化重建和重启Docker容器的脚本

#### `docker/test-playwright.sh`
- 测试Playwright在Docker环境中是否正常工作的脚本

#### `docker/PLAYWRIGHT_DOCKER_FIX.md`
- 详细的修复说明文档

## 使用方法

### 应用修复
```bash
cd docker
./rebuild-and-restart.sh
```

### 测试修复
```bash
cd docker
./test-playwright.sh
```

### 查看日志
```bash
docker-compose logs -f backend
```

## 预期结果
修复后，Playwright应该能够在Docker环境中正常启动Chromium浏览器，不再出现系统依赖缺失的错误。

## 注意事项
1. 确保Docker环境有足够的内存（至少2GB）
2. 浏览器将以无头模式运行
3. 所有测试执行都会在虚拟显示环境中进行 