<template>
  <el-dialog
    v-model="visible"
    title="导入Excel测试用例"
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
            将Excel文件拖到此处，或<em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              只能上传xlsx/xls文件，且不超过10MB
            </div>
          </template>
        </el-upload>
      </div>

      <!-- 预览区域 -->
      <div v-if="previewData.length > 0" class="preview-area">
        <h4>预览数据 (前5行)</h4>
        <el-table :data="previewData" style="width: 100%" size="small">
          <el-table-column prop="name" label="名称" />
          <el-table-column prop="description" label="描述" />
          <el-table-column prop="task_content" label="任务内容" />
          <el-table-column prop="category" label="分类" />
          <el-table-column prop="priority" label="优先级" />
        </el-table>
      </div>

      <!-- 导入选项 -->
      <div class="import-options">
        <h4>导入选项</h4>
        <el-form :model="importOptions" label-width="100px">
          <el-form-item label="默认状态">
            <el-select v-model="importOptions.defaultStatus" placeholder="选择默认状态">
              <el-option label="激活" value="active" />
              <el-option label="非激活" value="inactive" />
              <el-option label="草稿" value="draft" />
            </el-select>
          </el-form-item>
          <el-form-item label="默认优先级">
            <el-select v-model="importOptions.defaultPriority" placeholder="选择默认优先级">
              <el-option label="低" value="low" />
              <el-option label="中" value="medium" />
              <el-option label="高" value="high" />
              <el-option label="紧急" value="critical" />
            </el-select>
          </el-form-item>
          <el-form-item label="默认分类">
            <el-input v-model="importOptions.defaultCategory" placeholder="输入默认分类" />
          </el-form-item>
        </el-form>
      </div>
    </div>

    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button 
          type="primary" 
          @click="handleImport"
          :loading="importing"
          :disabled="!selectedFile"
        >
          {{ importing ? '导入中...' : '开始导入' }}
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { testCaseApi } from '@/services/api'
import type { TestCase } from '@/types/api'

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
    
    const response = await fetch('/api/test-cases/preview-excel', {
      method: 'POST',
      body: formData
    })
    
    if (response.ok) {
      const data = await response.json()
      previewData.value = data.preview || []
    } else {
      ElMessage.error('预览Excel文件失败')
    }
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
    
    const response = await fetch('/api/test-cases/import-excel', {
      method: 'POST',
      body: formData
    })
    
    if (response.ok) {
      const result = await response.json()
      ElMessage.success(`成功导入 ${result.imported_count} 个测试用例`)
      emit('imported')
      handleClose()
    } else {
      const error = await response.json()
      ElMessage.error(error.detail || '导入失败')
    }
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