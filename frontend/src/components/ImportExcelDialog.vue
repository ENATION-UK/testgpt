<template>
  <el-dialog
    v-model="visible"
    :title="$t('excelImport.title')"
    width="600px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div class="import-container">
      <!-- 文件上传区域 -->
      <div class="upload-area">
        <el-upload
          ref="uploadRef"
          :auto-upload="false"
          :show-file-list="true"
          :limit="1"
          accept=".xlsx,.xls"
          :on-change="handleFileChange"
          :on-remove="handleFileRemove"
          drag
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            {{ $t('excelImport.dragFile') }}<em>{{ $t('excelImport.clickUpload') }}</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              {{ $t('excelImport.uploadTip') }}
            </div>
          </template>
        </el-upload>
      </div>

      <!-- 预览区域 -->
      <div v-if="previewData.length > 0" class="preview-area">
        <h4>{{ $t('excelImport.previewData') }}</h4>
        <el-table :data="previewData" style="width: 100%" size="small">
          <el-table-column prop="name" :label="$t('common.name')" />
          <el-table-column prop="description" :label="$t('common.description')" />
          <el-table-column prop="task_content" :label="$t('testCase.taskContent')" />
          <el-table-column prop="category" :label="$t('common.category')" />
          <el-table-column prop="priority" :label="$t('common.priority')" />
        </el-table>
      </div>

      <!-- 导入选项 -->
      <div class="import-options">
        <h4>{{ $t('excelImport.importOptions') }}</h4>
        <el-form :model="importOptions" label-width="100px">
          <el-form-item :label="$t('excelImport.defaultStatus')">
            <el-select v-model="importOptions.defaultStatus" :placeholder="$t('excelImport.selectDefaultStatus')">
              <el-option :label="$t('common.active')" value="active" />
              <el-option :label="$t('common.inactive')" value="inactive" />
              <el-option :label="$t('common.draft')" value="draft" />
            </el-select>
          </el-form-item>
          <el-form-item :label="$t('excelImport.defaultPriority')">
            <el-select v-model="importOptions.defaultPriority" :placeholder="$t('excelImport.selectDefaultPriority')">
              <el-option :label="$t('common.low')" value="low" />
              <el-option :label="$t('common.medium')" value="medium" />
              <el-option :label="$t('common.high')" value="high" />
              <el-option :label="$t('common.critical')" value="critical" />
            </el-select>
          </el-form-item>
          <el-form-item :label="$t('excelImport.defaultCategory')">
            <el-input v-model="importOptions.defaultCategory" :placeholder="$t('excelImport.enterDefaultCategory')" />
          </el-form-item>
        </el-form>
      </div>
    </div>

    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleClose">{{ $t('common.cancel') }}</el-button>
        <el-button 
          type="primary" 
          @click="handleImport"
          :loading="importing"
          :disabled="!selectedFile"
        >
          {{ importing ? $t('excelImport.importing') : $t('excelImport.startImport') }}
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { testCaseApi } from '@/services/api'
import type { TestCase } from '@/types/api'

const { t } = useI18n()

interface ImportOptions {
  defaultStatus: string
  defaultPriority: string
  defaultCategory: string
}

interface Props {
  modelValue: boolean
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'imported'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const uploadRef = ref()
const selectedFile = ref<File | null>(null)
const previewData = ref<any[]>([])
const importing = ref(false)

const importOptions = ref<ImportOptions>({
  defaultStatus: 'active',
  defaultPriority: 'medium',
  defaultCategory: '导入'
})

const handleFileChange = (file: any) => {
  selectedFile.value = file.raw
  previewExcelFile(file.raw)
}

const handleFileRemove = () => {
  selectedFile.value = null
  previewData.value = []
}

const previewExcelFile = async (file: File) => {
  try {
    const formData = new FormData()
    formData.append('file', file)
    
    // 使用API服务而不是直接fetch
    const response = await testCaseApi.previewExcel(formData)
    previewData.value = response.preview || []
  } catch (error) {
    ElMessage.error('预览Excel文件失败')
  }
}

const handleImport = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择Excel文件')
    return
  }

  importing.value = true
  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    formData.append('options', JSON.stringify(importOptions.value))
    
    // 使用API服务而不是直接fetch
    const result = await testCaseApi.importExcel(formData)
    ElMessage.success(`成功导入 ${result.imported_count} 个测试用例`)
    emit('imported')
    handleClose()
  } catch (error) {
    ElMessage.error('导入失败')
  } finally {
    importing.value = false
  }
}

const handleClose = () => {
  visible.value = false
  selectedFile.value = null
  previewData.value = []
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
}
</script>

<style scoped>
.import-container {
  max-height: 500px;
  overflow-y: auto;
}

.upload-area {
  margin-bottom: 20px;
}

.preview-area {
  margin-bottom: 20px;
}

.preview-area h4 {
  margin-bottom: 10px;
  color: #606266;
}

.import-options h4 {
  margin-bottom: 15px;
  color: #606266;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style> 