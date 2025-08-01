<template>
  <div class="prompt-settings">
    <div class="page-header">
      <h2>提示词设置</h2>
      <p>配置自定义提示词，将拼合进 Agent 的测试系统提示词中</p>
    </div>

    <el-card class="settings-card">
      <template #header>
        <div class="card-header">
          <span>提示词配置</span>
          <div class="header-actions">
            <el-button 
              type="success" 
              @click="saveConfig"
              :loading="saving"
            >
              保存配置
            </el-button>
          </div>
        </div>
      </template>

      <el-form 
        ref="formRef" 
        :model="form" 
        :rules="rules"
        class="settings-form"
      >
        <el-form-item  prop="custom_prompt">
          <el-input 
            v-model="form.custom_prompt" 
            type="textarea" 
            :rows="18"
            placeholder="请输入自定义提示词，这些内容将拼合进 Agent 的测试系统提示词中"
            clearable
            show-word-limit
            maxlength="2000"
          />
          <div class="form-tip">
            <el-icon><InfoFilled /></el-icon>
            <span>自定义提示词将追加到默认的系统提示词后面，用于定制 Agent 的行为</span>
          </div>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 配置状态卡片 -->
    <el-card class="status-card" v-if="configStatus">
      <template #header>
        <span>配置状态</span>
      </template>
      
      <div class="status-content">
        <el-alert
          :title="configStatus.is_valid ? '配置有效' : '配置无效'"
          :type="configStatus.is_valid ? 'success' : 'error'"
          :description="configStatus.is_valid ? '提示词配置已正确设置' : '请检查提示词配置'"
          show-icon
        />
        
        <div class="status-details" v-if="configStatus.is_valid">
          <el-descriptions :column="1" border>
            <el-descriptions-item label="自定义提示词">
              <div class="prompt-preview">
                {{ configStatus.custom_prompt || '（未设置）' }}
              </div>
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>
    </el-card>

    <!-- 提示词说明卡片 -->
    <el-card class="info-card">
      <template #header>
        <span>使用说明</span>
      </template>
      
      <div class="info-content">
        <h4>提示词的作用</h4>
        <p>自定义提示词将拼合进 Agent 的测试系统提示词中，用于：</p>
        <ul>
          <li>通用、常用的测试步骤说明</li>
          <li>定制 Agent 的行为和决策逻辑</li>
          <li>添加特定的测试要求或验证标准</li>
          <li>调整 Agent 的响应风格和详细程度</li>
          <li>增加特定业务场景的测试指导</li>
        </ul>
        
        <h4>示例提示词</h4>
        <div class="example-prompt">
          <p><strong>通用、常用的测试步骤说明：</strong></p>
          <pre>
# 请记住以下通用操作
## 登录后台
打开网址:https://www.demo.com/login
输入用户名user
密码password
点击登录## 重要:如有需要以上通用操作请直接应用在具体用例中
          </pre>
          
          <p><strong>特定业务要求：</strong></p>
          <pre>在测试过程中，请特别关注用户体验相关的细节，如页面加载速度、交互响应时间等。</pre>
          
          <p><strong>错误处理：</strong></p>
          <pre>如果遇到网络错误或页面加载失败，请尝试重新加载页面，最多重试3次。</pre>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { InfoFilled } from '@element-plus/icons-vue'
import { promptConfigApi } from '@/services/api'
import type { PromptConfig, PromptConfigResponse } from '@/types/api'

// 表单引用
const formRef = ref()

// 加载状态
const loading = ref(false)
const saving = ref(false)

// 配置状态
const configStatus = ref<PromptConfigResponse | null>(null)

// 表单数据
const form = reactive<PromptConfig>({
  custom_prompt: ''
})

// 表单验证规则
const rules = {
  custom_prompt: [
    { max: 2000, message: '提示词长度不能超过2000个字符', trigger: 'blur' }
  ]
}

// 加载配置
const loadConfig = async () => {
  try {
    loading.value = true
    const config = await promptConfigApi.getConfig()
    
    // 更新表单数据
    form.custom_prompt = config.custom_prompt
    
    configStatus.value = config
  } catch (error) {
    console.error('加载配置失败:', error)
    ElMessage.error('加载配置失败')
  } finally {
    loading.value = false
  }
}

// 保存配置
const saveConfig = async () => {
  try {
    await formRef.value.validate()
    
    saving.value = true
    const result = await promptConfigApi.updateConfig(form)
    
    configStatus.value = result
    ElMessage.success('配置保存成功')
  } catch (error) {
    console.error('保存配置失败:', error)
    ElMessage.error('保存配置失败')
  } finally {
    saving.value = false
  }
}

// 页面加载时获取配置
onMounted(() => {
  loadConfig()
})
</script>

<style scoped>
.prompt-settings {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
  text-align: center;
}

.page-header h2 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 28px;
  font-weight: 600;
}

.page-header p {
  margin: 0;
  color: #606266;
  font-size: 14px;
}

.settings-card {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.settings-form {
  width: 100%;
}

.form-tip {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 4px;
  color: #909399;
  font-size: 12px;
}

.form-tip .el-icon {
  font-size: 14px;
}

.status-card,
.info-card {
  margin-bottom: 24px;
}

.status-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.status-details {
  margin-top: 16px;
}

.prompt-preview {
  max-height: 100px;
  overflow-y: auto;
  white-space: pre-wrap;
  font-family: monospace;
  font-size: 12px;
  color: #606266;
  background-color: #f5f7fa;
  padding: 8px;
  border-radius: 4px;
}

.info-content h4 {
  margin: 16px 0 8px 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
}

.info-content p {
  margin: 8px 0;
  color: #606266;
  line-height: 1.6;
}

.info-content ul {
  margin: 8px 0;
  padding-left: 20px;
  color: #606266;
}

.info-content li {
  margin: 4px 0;
  line-height: 1.6;
}

.example-prompt {
  margin-top: 16px;
}

.example-prompt p {
  margin: 12px 0 4px 0;
  font-weight: 500;
}

.example-prompt pre {
  background-color: #f5f7fa;
  padding: 8px 12px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 12px;
  color: #606266;
  margin: 4px 0 16px 0;
  white-space: pre-wrap;
  border-left: 3px solid #409eff;
}
</style> 