<template>
  <el-dialog
    v-model="visible"
    title="编辑测试用例"
    width="600px"
    :before-close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="100px"
    >
      <el-form-item label="名称" prop="name">
        <el-input
          v-model="form.name"
          placeholder="请输入测试用例名称"
          maxlength="100"
          show-word-limit
        />
      </el-form-item>

      <el-form-item label="描述" prop="description">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="3"
          placeholder="请输入测试用例描述"
          maxlength="500"
          show-word-limit
        />
      </el-form-item>

      <el-form-item label="任务内容" prop="task_content">
        <el-input
          v-model="form.task_content"
          type="textarea"
          :rows="4"
          placeholder="请输入测试任务内容，例如：打开网站，执行登录操作等"
          maxlength="1000"
          show-word-limit
        />
      </el-form-item>

      <el-form-item label="分类" prop="category">
        <el-input
          v-model="form.category"
          placeholder="请输入测试用例分类"
          maxlength="50"
        />
      </el-form-item>

      <el-form-item label="优先级" prop="priority">
        <el-select v-model="form.priority" placeholder="请选择优先级" style="width: 100%">
          <el-option label="低" value="low" />
          <el-option label="中" value="medium" />
          <el-option label="高" value="high" />
          <el-option label="紧急" value="critical" />
        </el-select>
      </el-form-item>

      <el-form-item label="状态" prop="status">
        <el-select v-model="form.status" placeholder="请选择状态" style="width: 100%">
          <el-option label="激活" value="active" />
          <el-option label="非激活" value="inactive" />
          <el-option label="草稿" value="draft" />
        </el-select>
      </el-form-item>

      <el-form-item label="标签">
        <el-input
          v-model="tagInput"
          placeholder="输入标签后按回车添加"
          @keyup.enter="addTag"
          style="margin-bottom: 10px"
        />
        <div v-if="form.tags.length > 0" style="margin-top: 10px">
          <el-tag
            v-for="tag in form.tags"
            :key="tag"
            closable
            @close="removeTag(tag)"
            style="margin-right: 8px; margin-bottom: 8px"
          >
            {{ tag }}
          </el-tag>
        </div>
      </el-form-item>

      <el-form-item label="预期结果" prop="expected_result">
        <el-input
          v-model="form.expected_result"
          type="textarea"
          :rows="3"
          placeholder="请输入预期测试结果"
          maxlength="500"
          show-word-limit
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="loading">
          保存
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { testCaseApi } from '@/services/api'
import type { TestCase } from '@/types/api'

interface Props {
  modelValue: boolean
  testCase: TestCase | null
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'updated'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const loading = ref(false)
const formRef = ref<FormInstance>()
const tagInput = ref('')

const form = ref({
  name: '',
  description: '',
  task_content: '',
  category: '',
  priority: 'medium',
  status: 'active',
  tags: [] as string[],
  expected_result: ''
})

const rules: FormRules = {
  name: [
    { required: true, message: '请输入测试用例名称', trigger: 'blur' },
    { min: 1, max: 100, message: '长度在 1 到 100 个字符', trigger: 'blur' }
  ],
  task_content: [
    { required: true, message: '请输入任务内容', trigger: 'blur' }
  ],
  category: [
    { required: true, message: '请输入分类', trigger: 'blur' }
  ],
  priority: [
    { required: true, message: '请选择优先级', trigger: 'change' }
  ],
  status: [
    { required: true, message: '请选择状态', trigger: 'change' }
  ]
}

// 监听 testCase 变化，填充表单
watch(() => props.testCase, (newTestCase) => {
  if (newTestCase) {
    form.value = {
      name: newTestCase.name,
      description: newTestCase.description || '',
      task_content: newTestCase.task_content || '',
      category: newTestCase.category || '',
      priority: newTestCase.priority || 'medium',
      status: newTestCase.status || 'active',
      tags: [...(newTestCase.tags || [])],
      expected_result: newTestCase.expected_result || ''
    }
  }
}, { immediate: true })

const addTag = () => {
  const tag = tagInput.value.trim()
  if (tag && !form.value.tags.includes(tag)) {
    form.value.tags.push(tag)
    tagInput.value = ''
  }
}

const removeTag = (tag: string) => {
  const index = form.value.tags.indexOf(tag)
  if (index > -1) {
    form.value.tags.splice(index, 1)
  }
}

const handleClose = () => {
  visible.value = false
}

const handleSubmit = async () => {
  if (!formRef.value || !props.testCase) return

  try {
    await formRef.value.validate()
    loading.value = true

    await testCaseApi.update(props.testCase.id, form.value)
    ElMessage.success('更新成功')
    emit('updated')
    visible.value = false
  } catch (error) {
    if (error !== false) {
      ElMessage.error('更新失败')
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.dialog-footer {
  text-align: right;
}
</style> 