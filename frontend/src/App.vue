<template>
  <div id="app">
    <el-config-provider :locale="currentElementLocale">
      <el-container class="layout-container">
        <el-header class="header">
          <div class="header-content">
            <h1 class="logo">
              <el-icon><Monitor /></el-icon>
              TestGPT
            </h1>
            <el-menu
              mode="horizontal"
              :router="true"
              :default-active="$route.path"
              class="nav-menu"
            >
              <el-menu-item index="/">
                <el-icon><House /></el-icon>
                {{ $t('nav.home') }}
              </el-menu-item>
              <el-menu-item index="/test-cases">
                <el-icon><Document /></el-icon>
                {{ $t('nav.testCases') }}
              </el-menu-item>
              <el-menu-item index="/categories">
                <el-icon><Folder /></el-icon>
                {{ $t('nav.categories') }}
              </el-menu-item>
              <el-menu-item index="/excel-import">
                <el-icon><Upload /></el-icon>
                {{ $t('nav.excelImport') }}
              </el-menu-item>
              <el-menu-item index="/executions">
                <el-icon><VideoPlay /></el-icon>
                {{ $t('nav.executions') }}
              </el-menu-item>
              <el-menu-item index="/batch-executions">
                <el-icon><Collection /></el-icon>
                {{ $t('nav.batchExecutions') }}
              </el-menu-item>
              <el-menu-item index="/statistics">
                <el-icon><TrendCharts /></el-icon>
                {{ $t('nav.statistics') }}
              </el-menu-item>
              <el-menu-item index="/multi-model-settings">
                <el-icon><Setting /></el-icon>
                {{ $t('nav.multiModelSettings') }}
              </el-menu-item>
              <el-menu-item index="/prompt-settings">
                <el-icon><ChatDotRound /></el-icon>
                {{ $t('nav.promptSettings') }}
              </el-menu-item>
            </el-menu>
            <div class="language-switcher">
              <el-dropdown @command="handleLanguageChange" trigger="click">
                <el-button type="text" class="language-btn">
                  <el-icon><Setting /></el-icon>
                  {{ currentLanguageText }}
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="zh-CN">中文</el-dropdown-item>
                    <el-dropdown-item command="en-US">English</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
        </el-header>
        
        <el-main class="main-content">
          <router-view />
        </el-main>
        
        <el-footer class="footer">
          <p>&copy; 2024 TestGPT. All rights reserved.</p>
        </el-footer>
      </el-container>
    </el-config-provider>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Monitor, House, Document, VideoPlay, Collection, TrendCharts, Setting, ChatDotRound, Folder, Upload } from '@element-plus/icons-vue'
// @ts-ignore
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
// @ts-ignore
import en from 'element-plus/dist/locale/en.mjs'

const { locale } = useI18n()

// Element Plus 语言配置
const currentElementLocale = computed(() => {
  return locale.value === 'zh-CN' ? zhCn : en
})

// 当前语言显示文本
const currentLanguageText = computed(() => {
  return locale.value === 'zh-CN' ? '中文' : 'English'
})

// 语言切换处理
const handleLanguageChange = (command: string) => {
  locale.value = command
  localStorage.setItem('locale', command)
}
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

.language-switcher {
  margin-left: 20px;
}

.language-btn {
  color: white !important;
  font-size: 14px;
}

.language-btn:hover {
  background: rgba(255, 255, 255, 0.1) !important;
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