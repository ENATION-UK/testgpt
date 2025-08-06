<template>
  <div class="multi-model-settings">
    <div class="page-header">
      <h2>多模型配置</h2>
      <p>配置多个模型提供商和API密钥，实现轮询机制增加并发限制</p>
    </div>
    
    <el-card class="settings-card">
      <template #header>
        <div class="card-header">
          <span>模型提供商配置</span>
          <div class="header-actions">
            <el-button 
              type="primary" 
              @click="testConfig"
              :loading="testing"
              :disabled="!isConfigValid"
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
      
      <div class="providers-container">
        <!-- 层级1：模型提供商配置 -->
        <div 
          v-for="(provider, index) in form.providers" 
          :key="provider.provider_id || index" 
          class="provider-item"
        >
          <el-card class="provider-card">
            <template #header>
              <div class="provider-header">
                <div class="provider-title">
                  <el-icon><Setting /></el-icon>
                  <span>{{ provider.provider_name || `模型提供商 ${index + 1}` }}</span>
                </div>
                <div class="provider-actions">
                  <el-switch 
                    v-model="provider.is_active" 
                    active-text="启用" 
                    inactive-text="禁用"
                  />
                  <el-button 
                    type="danger" 
                    size="small" 
                    @click="removeProvider(index)"
                    :disabled="form.providers.length <= 1"
                  >
                    删除
                  </el-button>
                </div>
              </div>
            </template>

            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="提供商名称" required>
                  <el-input 
                    v-model="provider.provider_name" 
                    placeholder="如：OpenAI账号1"
                    clearable
                  />
                </el-form-item>
              </el-col>
              
              <el-col :span="12">
                <el-form-item label="模型类型" required>
                  <el-select 
                    v-model="provider.model_type" 
                    placeholder="选择模型类型"
                    @change="onModelTypeChange(provider)"
                  >
                    <el-option label="DeepSeek" value="deepseek" />
                    <el-option label="OpenAI" value="openai" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="API基础URL" required>
                  <el-input 
                    v-model="provider.base_url" 
                    placeholder="API基础URL"
                    clearable
                  />
                  <div class="form-tip">
                    <el-icon><InfoFilled /></el-icon>
                    <span>DeepSeek: https://api.deepseek.com/v1, OpenAI: https://api.openai.com/v1</span>
                  </div>
                </el-form-item>
              </el-col>
              
              <el-col :span="12">
                <el-form-item label="模型名称" required>
                  <el-input 
                    v-model="provider.model" 
                    placeholder="模型名称"
                    clearable
                  />
                  <div class="form-tip">
                    <el-icon><InfoFilled /></el-icon>
                    <span>DeepSeek: deepseek-chat, OpenAI: gpt-4o</span>
                  </div>
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="16">
              <el-col :span="8">
                <el-form-item label="温度参数">
                  <el-slider 
                    v-model="provider.temperature" 
                    :min="0" 
                    :max="2" 
                    :step="0.1"
                    show-input
                    :show-input-controls="false"
                  />
                </el-form-item>
              </el-col>
              
              <el-col :span="8">
                <el-form-item label="最大Token数">
                  <el-input-number 
                    v-model="provider.max_tokens" 
                    :min="1" 
                    :max="100000"
                    placeholder="不限制"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
              
              <el-col :span="8">
                <el-form-item label="限流数量">
                  <el-input-number 
                    v-model="provider.rate_limit" 
                    :min="1" 
                    :max="100"
                    style="width: 100%"
                  />
                  <div class="form-tip">
                    <el-icon><InfoFilled /></el-icon>
                    <span>每分钟最大请求数</span>
                  </div>
                </el-form-item>
              </el-col>
            </el-row>

            <!-- 层级2：API密钥配置 -->
            <el-divider content-position="left">
              <el-icon><Key /></el-icon>
              <span>API密钥配置</span>
            </el-divider>

            <div class="api-keys-container">
              <div 
                v-for="(key, keyIndex) in provider.api_keys" 
                :key="keyIndex" 
                class="api-key-item"
              >
                <el-input 
                  v-model="provider.api_keys[keyIndex]" 
                  type="password" 
                  placeholder="请输入API密钥"
                  show-password
                  clearable
                />
                <el-button 
                  type="danger" 
                  size="small" 
                  @click="removeApiKey(index, keyIndex)"
                  :disabled="provider.api_keys.length <= 1"
                >
                  删除
                </el-button>
              </div>
              
              <el-button 
                type="primary" 
                size="small" 
                @click="addApiKey(index)"
                style="margin-top: 8px;"
              >
                <el-icon><Plus /></el-icon>
                添加API密钥
              </el-button>
            </div>
          </el-card>
        </div>

        <el-button 
          type="primary" 
          @click="addProvider"
          style="width: 100%; margin-top: 16px; height: 50px;"
          size="large"
        >
          <el-icon><Plus /></el-icon>
          添加模型提供商
        </el-button>
      </div>
    </el-card>

    <!-- 配置状态 -->
    <el-card class="status-card" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>配置状态</span>
          <el-button 
            type="primary" 
            size="small" 
            @click="refreshStatus"
            :loading="loadingStatus"
          >
            刷新状态
          </el-button>
        </div>
      </template>

      <div v-if="status" class="status-content">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="总提供商数">{{ status.total_providers }}</el-descriptions-item>
          <el-descriptions-item label="总API密钥数">{{ status.total_api_keys }}</el-descriptions-item>
          <el-descriptions-item label="当前提供商索引">{{ status.current_provider_index }}</el-descriptions-item>
        </el-descriptions>

        <div class="provider-details" style="margin-top: 16px;">
          <h4>提供商详情</h4>
          <el-table :data="status.provider_details" style="width: 100%">
            <el-table-column prop="provider_name" label="提供商名称" />
            <el-table-column prop="model_type" label="模型类型" width="100" />
            <el-table-column prop="api_key_count" label="API密钥数" width="100" />
            <el-table-column prop="rate_limit" label="限流数量" width="100" />
            <el-table-column prop="current_requests" label="当前请求数" width="120" />
            <el-table-column prop="is_available" label="状态" width="100">
              <template #default="scope">
                <el-tag :type="scope.row.is_available ? 'success' : 'danger'">
                  {{ scope.row.is_available ? '可用' : '限流中' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Setting, InfoFilled, Key, Plus } from '@element-plus/icons-vue'
import { multiModelConfigApi } from '@/services/api'

interface ModelProvider {
  provider_id: string
  provider_name: string
  model_type: string
  base_url: string
  model: string
  temperature: number
  max_tokens: number | null
  api_keys: string[]
  rate_limit: number
  is_active: boolean
  current_key_index: number
}

interface ConfigStatus {
  total_providers: number
  total_api_keys: number
  current_provider_index: number
  provider_details: Array<{
    provider_id: string
    provider_name: string
    model_type: string
    api_key_count: number
    rate_limit: number
    current_requests: number
    last_request_time: number
    is_available: boolean
  }>
}

const testing = ref(false)
const saving = ref(false)
const loadingStatus = ref(false)
const status = ref<ConfigStatus | null>(null)

const form = reactive({
  providers: [
    {
      provider_id: 'deepseek_default',
      provider_name: 'DeepSeek默认配置',
      model_type: 'deepseek',
      base_url: 'https://api.deepseek.com/v1',
      model: 'deepseek-chat',
      temperature: 0.7,
      max_tokens: null,
      api_keys: [''],
      rate_limit: 2,
      is_active: true,
      current_key_index: 0
    }
  ],
  current_provider_index: 0
})

const isConfigValid = computed(() => {
  return form.providers.some(provider => 
    provider.is_active && provider.api_keys.some(key => key.trim() !== '')
  )
})

const generateProviderId = () => {
  return 'provider_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
}

const onModelTypeChange = (provider: ModelProvider) => {
  if (provider.model_type === 'deepseek') {
    provider.base_url = 'https://api.deepseek.com/v1'
    provider.model = 'deepseek-chat'
  } else if (provider.model_type === 'openai') {
    provider.base_url = 'https://api.openai.com/v1'
    provider.model = 'gpt-4o'
  }
}

const addProvider = () => {
  const newProvider = {
    provider_id: generateProviderId(),
    provider_name: `模型提供商 ${form.providers.length + 1}`,
    model_type: 'deepseek',
    base_url: 'https://api.deepseek.com/v1',
    model: 'deepseek-chat',
    temperature: 0.7,
    max_tokens: null,
    api_keys: [''],
    rate_limit: 2,
    is_active: true,
    current_key_index: 0
  }
  form.providers.push(newProvider)
}

const removeProvider = (index: number) => {
  form.providers.splice(index, 1)
}

const addApiKey = (providerIndex: number) => {
  form.providers[providerIndex].api_keys.push('')
}

const removeApiKey = (providerIndex: number, keyIndex: number) => {
  form.providers[providerIndex].api_keys.splice(keyIndex, 1)
}

const loadConfig = async () => {
  try {
    const config = await multiModelConfigApi.getConfig()
    // 确保每个提供商都有provider_id
    config.providers.forEach((provider: any) => {
      if (!provider.provider_id) {
        provider.provider_id = generateProviderId()
      }
    })
    Object.assign(form, config)
  } catch (error) {
    console.error('加载配置失败:', error)
    ElMessage.error('加载配置失败')
  }
}

const saveConfig = async () => {
  try {
    // 验证配置
    for (const provider of form.providers) {
      if (!provider.provider_name.trim()) {
        ElMessage.error('提供商名称不能为空')
        return
      }
      if (!provider.provider_id) {
        provider.provider_id = generateProviderId()
      }
      if (provider.is_active && !provider.api_keys.some(key => key.trim())) {
        ElMessage.error(`提供商 ${provider.provider_name} 必须配置至少一个API密钥`)
        return
      }
    }
    
    saving.value = true
    await multiModelConfigApi.updateConfig(form)
    ElMessage.success('配置保存成功')
    await loadConfig()
  } catch (error: any) {
    console.error('保存配置失败:', error)
    ElMessage.error(error.response?.data?.detail || '保存配置失败')
  } finally {
    saving.value = false
  }
}

const testConfig = async () => {
  try {
    testing.value = true
    const response = await multiModelConfigApi.testConfig()
    if (response.success) {
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

const refreshStatus = async () => {
  try {
    loadingStatus.value = true
    const response = await multiModelConfigApi.getStatus()
    status.value = response
  } catch (error) {
    console.error('获取状态失败:', error)
    ElMessage.error('获取状态失败')
  } finally {
    loadingStatus.value = false
  }
}

onMounted(async () => {
  await loadConfig()
  await refreshStatus()
})
</script>

<style scoped>
.multi-model-settings {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0 0 8px 0;
  color: #303133;
}

.page-header p {
  margin: 0;
  color: #606266;
}

.settings-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.providers-container {
  width: 100%;
}

.provider-item {
  margin-bottom: 20px;
}

.provider-card {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
}

.provider-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.provider-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #303133;
}

.provider-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.form-tip {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 4px;
  color: #909399;
  font-size: 12px;
}

.api-keys-container {
  width: 100%;
}

.api-key-item {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
}

.api-key-item .el-input {
  flex: 1;
}

.status-card {
  margin-top: 20px;
}

.status-content {
  width: 100%;
}

.provider-details h4 {
  margin: 0 0 16px 0;
  color: #303133;
}

.el-divider {
  margin: 20px 0;
}

.el-divider__text {
  background-color: #fff;
  color: #303133;
  font-weight: 500;
}
</style> 