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

      <el-form-item label="操作步骤" prop="task_content">
        <el-input
          v-model="form.task_content"
          type="textarea"
          :rows="4"
          placeholder="请输入具体的操作步骤，例如：1. 打开网站 2. 点击登录按钮 3. 输入用户名密码等"
          maxlength="1000"
          show-word-limit
        />
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

      <el-form-item label="分类" prop="category_id">
        <el-cascader
          v-model="form.category_id"
          :options="categoryOptions"
          :props="cascaderProps"
          placeholder="请选择分类"
          clearable
          style="width: 100%"
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
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { testCaseApi, categoryApi } from '@/services/api'
import type { TestCase, Category } from '@/types/api'

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
  task_content: '',
  category: '',
  category_id: undefined as number | undefined,
  priority: 'medium',
  status: 'active',
  tags: [] as string[],
  expected_result: ''
})

// 分类相关
const categoryOptions = ref<Category[]>([])

// 级联选择器配置
const cascaderProps = {
  value: 'id',
  label: 'name',
  children: 'children',
  checkStrictly: false,
  emitPath: false
}

const rules: FormRules = {
  name: [
    { required: true, message: '请输入测试用例名称', trigger: 'blur' },
    { min: 1, max: 100, message: '长度在 1 到 100 个字符', trigger: 'blur' }
  ],
  task_content: [
    { required: true, message: '请输入操作步骤', trigger: 'blur' }
  ],
  category_id: [
    { required: false, message: '请选择分类', trigger: 'change' }
  ],
  priority: [
    { required: true, message: '请选择优先级', trigger: 'change' }
  ],
  status: [
    { required: true, message: '请选择状态', trigger: 'change' }
  ],
  expected_result: [
    { required: true, message: '请输入预期结果', trigger: 'blur' },
    { min: 2, max: 500, message: '预期结果长度在 2 到 500 个字符', trigger: 'blur' }
  ]
}

// 监听 testCase 变化，填充表单
watch(() => props.testCase, (newTestCase) => {
  if (newTestCase) {
    form.value = {
      name: newTestCase.name,
      task_content: newTestCase.task_content || '',
      category: newTestCase.category || '',
      category_id: newTestCase.category_id || undefined,
      priority: newTestCase.priority || 'medium',
      status: newTestCase.status || 'active',
      tags: [...(newTestCase.tags || [])],
      expected_result: newTestCase.expected_result || ''
    }
    console.log('填充表单数据:', form.value)
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

// 加载分类树
const loadCategoryTree = async () => {
  try {
    categoryOptions.value = await categoryApi.getTree(false)
  } catch (error) {
    ElMessage.error('加载分类树失败')
  }
}

const handleSubmit = async () => {
  if (!formRef.value || !props.testCase) return

  try {
    await formRef.value.validate()
    loading.value = true

    // 处理级联选择器返回的数据格式
    const submitData = { ...form.value }
    
    // 如果category_id是数组（级联选择器返回的格式），取最后一个值
    if (Array.isArray(submitData.category_id)) {
      submitData.category_id = submitData.category_id.length > 0 
        ? submitData.category_id[submitData.category_id.length - 1] 
        : undefined
    }

    await testCaseApi.update(props.testCase.id, submitData)
    ElMessage.success('更新成功')
    emit('updated')
    visible.value = false
  } catch (error) {
    console.error('更新测试用例失败:', error)
    ElMessage.error('更新失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadCategoryTree()
})
</script>

<style scoped>
.dialog-footer {
  text-align: right;
}
</style> 