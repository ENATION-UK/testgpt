<template>
  <div id="app">
    <el-container class="layout-container">
      <el-header class="header">
        <div class="header-content">
          <h1 class="logo">
            <el-icon><Monitor /></el-icon>
            AutoTest
          </h1>
          <el-menu
            mode="horizontal"
            :router="true"
            :default-active="$route.path"
            class="nav-menu"
          >
            <el-menu-item index="/">
              <el-icon><House /></el-icon>
              首页
            </el-menu-item>
            <el-menu-item index="/test-cases">
              <el-icon><Document /></el-icon>
              测试用例
            </el-menu-item>
            <el-menu-item index="/executions">
              <el-icon><VideoPlay /></el-icon>
              执行记录
            </el-menu-item>
            <el-menu-item index="/statistics">
              <el-icon><TrendCharts /></el-icon>
              统计信息
            </el-menu-item>
            <el-menu-item index="/model-settings">
              <el-icon><Setting /></el-icon>
              模型设置
            </el-menu-item>
            <el-menu-item index="/prompt-settings">
              <el-icon><ChatDotRound /></el-icon>
              提示词设置
            </el-menu-item>
          </el-menu>
        </div>
      </el-header>
      
      <el-main class="main-content">
        <router-view />
      </el-main>
      
      <el-footer class="footer">
        <p>&copy; 2024 AutoTest. All rights reserved.</p>
      </el-footer>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { Monitor, House, Document, VideoPlay, TrendCharts, Setting, ChatDotRound } from '@element-plus/icons-vue'
</script>

<style scoped>
.layout-container {
  min-height: 100vh;
}

.header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: 24px;
  font-weight: bold;
}

.nav-menu {
  background: transparent;
  border: none;
}

.nav-menu .el-menu-item {
  color: white;
  border-bottom: 2px solid transparent;
}

.nav-menu .el-menu-item:hover,
.nav-menu .el-menu-item.is-active {
  background: rgba(255, 255, 255, 0.1);
  border-bottom-color: white;
}

.main-content {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

.footer {
  text-align: center;
  color: #666;
  padding: 20px;
  background: #f5f5f5;
}
</style>

<style>
#app {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
}

body {
  margin: 0;
  padding: 0;
  background: #f5f5f5;
}
</style> 