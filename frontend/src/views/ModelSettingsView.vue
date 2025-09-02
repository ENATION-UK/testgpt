<template>
  <div class="model-settings">
    <div class="page-header">
      <h2>模型设置</h2>
      <p>配置大语言模型的参数和API密钥</p>
    </div>

    <el-card class="settings-card">
      <template #header>
        <div class="card-header">
          <span>模型配置</span>
          <div class="header-actions">
            <el-button 
              type="primary" 
              @click="testConfig"
              :loading="testing"
              :disabled="!form.api_key"
            >
              测试配置
            </el-button>
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
        label-width="120px"
        class="settings-form"
      >
        <el-form-item label="模型类型" prop="model_type">
          <el-select v-model="form.model_type" placeholder="选择模型类型" style="width: 100%">
            <el-option label="DeepSeek" value="deepseek" />
            <el-option label="OpenAI" value="openai" />
            <el-option label="豆包" value="doubao" />
          </el-select>
        </el-form-item>

        <el-form-item label="API密钥" prop="api_key">
          <el-input 
            v-model="form.api_key" 
            type="password" 
            placeholder="请输入API密钥"
            show-password
            clearable
          />
          <div class="form-tip">
            <el-icon><InfoFilled /></el-icon>
            <span>API密钥将安全保存，不会在界面上明文显示</span>
          </div>
        </el-form-item>

        <el-form-item label="基础URL" prop="base_url">
          <el-input 
            v-model="form.base_url" 
            placeholder="API基础URL"
            clearable
          />
          <div class="form-tip">
            <el-icon><InfoFilled /></el-icon>
            <span>DeepSeek: https://api.deepseek.com/v1, OpenAI: https://api.openai.com/v1, 豆包: https://api.doubao.com</span>
          </div>
        </el-form-item>

        <el-form-item label="模型名称" prop="model">
          <el-input 
            v-model="form.model" 
            placeholder="模型名称"
            clearable
          />
          <div class="form-tip">
            <el-icon><InfoFilled /></el-icon>
            <span>DeepSeek: deepseek-chat, OpenAI: gpt-4o, 豆包: doubao-v1.5</span>
          </div>
        </el-form-item>

        <el-form-item label="温度参数" prop="temperature">
          <el-slider 
            v-model="form.temperature" 
            :min="0" 
            :max="2" 
            :step="0.1"
            show-input
            :show-input-controls="false"
            style="width: 100%"
          />
          <div class="form-tip">
            <el-icon><InfoFilled /></el-icon>
            <span>控制输出的随机性，0表示确定性输出，2表示最大随机性</span>
          </div>
        </el-form-item>

        <el-form-item label="最大Token数" prop="max_tokens">
          <el-input-number 
            v-model="form.max_tokens" 
            :min="1" 
            :max="4000"
            placeholder="留空表示无限制"
            style="width: 100%"
          />
          <div class="form-tip">
            <el-icon><InfoFilled /></el-icon>
            <span>限制模型输出的最大token数量，留空表示无限制</span>
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
          :description="configStatus.is_valid ? '模型配置已正确设置' : '请检查API密钥和配置参数'"
          show-icon
        />
        
        <div class="status-details" v-if="configStatus.is_valid">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="模型类型">
              {{ configStatus.model_type }}
            </el-descriptions-item>
            <el-descriptions-item label="模型名称">
              {{ configStatus.model }}
            </el-descriptions-item>
            <el-descriptions-item label="基础URL">
              {{ configStatus.base_url }}
            </el-descriptions-item>
            <el-descriptions-item label="温度参数">
              {{ configStatus.temperature }}
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>
    </el-card>

    <!-- 测试结果 -->
    <el-card class="test-result-card" v-if="testResult">
      <template #header>
        <span>测试结果</span>
      </template>
      
      <el-alert
        :title="testResult.success ? '测试成功' : '测试失败'"
        :type="testResult.success ? 'success' : 'error'"
        :description="testResult.message"
        show-icon
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { InfoFilled } from '@element-plus/icons-vue'
import { modelConfigApi } from '@/services/api'
import type { ModelConfig, ModelConfigResponse, TestConfigResult } from '@/types/api'

// 表单引用
const formRef = ref()

// 加载状态
const loading = ref(false)
const saving = ref(false)
const testing = ref(false)

// 配置状态
const configStatus = ref<ModelConfigResponse | null>(null)
const testResult = ref<TestConfigResult | null>(null)

// 表单数据
const form = reactive<ModelConfig>({
  model_type: 'deepseek',
  api_key: '',
  base_url: 'https://api.deepseek.com/v1',
  model: 'deepseek-chat',
  temperature: 0.7,
  max_tokens: undefined
})

// 表单验证规则
const rules = {
  model_type: [
    { required: true, message: '请选择模型类型', trigger: 'change' }
  ],
  api_key: [
    { required: true, message: '请输入API密钥', trigger: 'blur' }
  ],
  base_url: [
    { required: true, message: '请输入基础URL', trigger: 'blur' }
  ],
  model: [
    { required: true, message: '请输入模型名称', trigger: 'blur' }
  ],
  temperature: [
    { required: true, message: '请设置温度参数', trigger: 'blur' }
  ]
}

// 加载配置
const loadConfig = async () => {
  try {
    loading.value = true
    const config = await modelConfigApi.getConfig()
    
    // 更新表单数据
    Object.assign(form, {
      model_type: config.model_type,
      api_key: config.api_key,
      base_url: config.base_url || '',
      model: config.model,
      temperature: config.temperature,
      max_tokens: config.max_tokens
    })
    
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
    const result = await modelConfigApi.updateConfig(form)
    
    configStatus.value = result
    testResult.value = null
    ElMessage.success('配置保存成功')
  } catch (error) {
    console.error('保存配置失败:', error)
    ElMessage.error('保存配置失败')
  } finally {
    saving.value = false
  }
}

// 测试配置
const testConfig = async () => {
  try {
    await formRef.value.validate()
    
    testing.value = true
    const result = await modelConfigApi.testConfig(form)
    
    testResult.value = result
    if (result.success) {
      ElMessage.success('配置测试成功')
    } else {
      ElMessage.error('配置测试失败')
    }
  } catch (error) {
    console.error('测试配置失败:', error)
    ElMessage.error('测试配置失败')
  } finally {
    testing.value = false
  }
}

// 监听模型类型变化
const handleModelTypeChange = () => {
  if (form.model_type === 'deepseek') {
    form.base_url = 'https://api.deepseek.com/v1'
    form.model = 'deepseek-chat'
  } else if (form.model_type === 'openai') {
    form.base_url = 'https://api.openai.com/v1'
    form.model = 'gpt-4o'
  } else if (form.model_type === 'doubao') {
    form.base_url = 'https://api.doubao.com'
    form.model = 'doubao-v1.5'
  }
}

// 监听模型类型变化
watch(() => form.model_type, handleModelTypeChange)

// 页面加载时获取配置
onMounted(() => {
  loadConfig()
})
</script>

<style scoped>
.model-settings {
  max-width: 800px;
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
  max-width: 600px;
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
.test-result-card {
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

:deep(.el-slider__input) {
  width: 80px;
}

:deep(.el-input-number) {
  width: 100%;
}
</style> 