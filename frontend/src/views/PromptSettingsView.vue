<template>
  <div class="prompt-settings">
    <div class="page-header">
      <h2>{{ $t('settings.prompt.title') }}</h2>
      <p>{{ $t('settings.prompt.description') }}</p>
    </div>

    <el-card class="settings-card">
      <template #header>
        <div class="card-header">
          <span>{{ $t('settings.prompt.promptConfig') }}</span>
          <div class="header-actions">
            <el-button 
              type="success" 
              @click="saveConfig"
              :loading="saving"
            >
              {{ $t('settings.prompt.saveConfig') }}
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
            :placeholder="$t('settings.prompt.placeholder.customPrompt')"
            clearable
            show-word-limit
            maxlength="2000"
          />
          <div class="form-tip">
            <el-icon><InfoFilled /></el-icon>
            <span>{{ $t('settings.prompt.tips.customPrompt') }}</span>
          </div>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 配置状态卡片 -->
    <el-card class="status-card" v-if="configStatus">
      <template #header>
        <span>{{ $t('settings.prompt.configStatus') }}</span>
      </template>
      
      <div class="status-content">
        <el-alert
          :title="configStatus.is_valid ? $t('settings.prompt.status.valid') : $t('settings.prompt.status.invalid')"
          :type="configStatus.is_valid ? 'success' : 'error'"
          :description="configStatus.is_valid ? $t('settings.prompt.status.validDescription') : $t('settings.prompt.status.invalidDescription')"
          show-icon
        />
        
        <div class="status-details" v-if="configStatus.is_valid">
          <el-descriptions :column="1" border>
            <el-descriptions-item :label="$t('settings.prompt.customPrompt')">
              <div class="prompt-preview">
                {{ configStatus.custom_prompt || $t('settings.prompt.status.notSet') }}
              </div>
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>
    </el-card>

    <!-- 提示词说明卡片 -->
    <el-card class="info-card">
      <template #header>
        <span>{{ $t('settings.prompt.usageInstructions') }}</span>
      </template>
      
      <div class="info-content">
        <h4>{{ $t('settings.prompt.usage.title') }}</h4>
        <p>{{ $t('settings.prompt.usage.description') }}</p>
        <ul>
          <li>{{ $t('settings.prompt.usage.purposes.0') }}</li>
          <li>{{ $t('settings.prompt.usage.purposes.1') }}</li>
          <li>{{ $t('settings.prompt.usage.purposes.2') }}</li>
          <li>{{ $t('settings.prompt.usage.purposes.3') }}</li>
          <li>{{ $t('settings.prompt.usage.purposes.4') }}</li>
        </ul>
        
        <h4>{{ $t('settings.prompt.usage.examples.title') }}</h4>
        <div class="example-prompt">
          <p><strong>{{ $t('settings.prompt.usage.examples.commonSteps.title') }}</strong></p>
          <pre>{{ $t('settings.prompt.usage.examples.commonSteps.content') }}</pre>
          
          <p><strong>{{ $t('settings.prompt.usage.examples.businessRequirements.title') }}</strong></p>
          <pre>{{ $t('settings.prompt.usage.examples.businessRequirements.content') }}</pre>
          
          <p><strong>{{ $t('settings.prompt.usage.examples.errorHandling.title') }}</strong></p>
          <pre>{{ $t('settings.prompt.usage.examples.errorHandling.content') }}</pre>
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