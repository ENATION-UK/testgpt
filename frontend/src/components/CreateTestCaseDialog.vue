<template>
    <el-dialog
      v-model="visible"
      title="创建测试用例"
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
          <div v-if="form.tags && form.tags.length > 0" style="margin-top: 10px">
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
        <span class="dialog-footer">
          <el-button @click="handleClose">取消</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="loading">
            创建
          </el-button>
        </span>
      </template>
    </el-dialog>
  </template>
  
  <script setup lang="ts">
  import { ref, reactive, watch, onMounted } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { testCaseApi, categoryApi } from '@/services/api'
import type { CreateTestCaseRequest, Category } from '@/types/api'
  
  interface Props {
    modelValue: boolean
  }
  
  interface Emits {
    (e: 'update:modelValue', value: boolean): void
    (e: 'created'): void
  }
  
  const props = defineProps<Props>()
  const emit = defineEmits<Emits>()
  
  const visible = ref(false)
  const loading = ref(false)
  const formRef = ref<FormInstance>()
  const tagInput = ref('')
  
  const form = reactive<CreateTestCaseRequest & { category_id?: number }>({
    name: '',
    description: '',
    task_content: '',
    category: '',
    category_id: undefined,
    priority: 'medium',
    status: 'draft',
    tags: [],
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
      { min: 2, max: 100, message: '名称长度在 2 到 100 个字符', trigger: 'blur' }
    ],
    description: [
      { required: true, message: '请输入测试用例描述', trigger: 'blur' },
      { min: 5, max: 500, message: '描述长度在 5 到 500 个字符', trigger: 'blur' }
    ],
    task_content: [
      { required: true, message: '请输入任务内容', trigger: 'blur' },
      { min: 10, max: 1000, message: '任务内容长度在 10 到 1000 个字符', trigger: 'blur' }
    ],
    category_id: [
      { required: false, message: '请选择分类', trigger: 'change' }
    ],
    priority: [
      { required: true, message: '请选择优先级', trigger: 'change' }
    ],
    status: [
      { required: true, message: '请选择状态', trigger: 'change' }
    ]
  }
  
  // 监听modelValue变化
  watch(() => props.modelValue, (newVal) => {
    visible.value = newVal
    if (newVal) {
      resetForm()
    }
  })
  
  // 监听visible变化
  watch(visible, (newVal) => {
    emit('update:modelValue', newVal)
  })
  
  const resetForm = () => {
    form.name = ''
    form.description = ''
    form.task_content = ''
    form.category = ''
    form.category_id = undefined
    form.priority = 'medium'
    form.status = 'draft'
    form.tags = []
    form.expected_result = ''
    tagInput.value = ''
    formRef.value?.clearValidate()
  }
  
  const addTag = () => {
    const tag = tagInput.value.trim()
    if (tag && form.tags && !form.tags.includes(tag)) {
      form.tags.push(tag)
      tagInput.value = ''
    }
  }
  
  const removeTag = (tag: string) => {
    if (form.tags) {
      const index = form.tags.indexOf(tag)
      if (index > -1) {
        form.tags.splice(index, 1)
      }
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
    if (!formRef.value) return
  
    try {
      await formRef.value.validate()
      loading.value = true
  
      // 处理级联选择器返回的数据格式
      const submitData = { ...form }
      
      // 如果category_id是数组（级联选择器返回的格式），取最后一个值
      if (Array.isArray(submitData.category_id)) {
        submitData.category_id = submitData.category_id.length > 0 
          ? submitData.category_id[submitData.category_id.length - 1] 
          : undefined
      }

      await testCaseApi.create(submitData)
      ElMessage.success('测试用例创建成功')
      emit('created')
      handleClose()
    } catch (error) {
      console.error('创建测试用例失败:', error)
      ElMessage.error('创建测试用例失败')
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
    display: flex;
    justify-content: flex-end;
    gap: 12px;
  }
  </style>