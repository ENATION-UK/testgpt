<template>
  <div class="categories">
    <div class="page-header">
      <h2>{{ $t('category.title') }}</h2>
      <div class="header-actions">
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon>
          {{ $t('category.create') }}
        </el-button>
      </div>
    </div>

    <el-card>
      <div class="category-tree-container">
        <el-tree
          ref="categoryTreeRef"
          :data="categoryTree"
          :props="treeProps"
          node-key="id"
          default-expand-all
          :expand-on-click-node="false"
          @node-click="handleNodeClick"
        >
          <template #default="{ node, data }">
            <div class="category-node">
              <div class="category-info">
                <span class="category-name">{{ data.name }}</span>
                <el-tag v-if="data.test_case_count > 0" size="small" type="info">
                  {{ data.test_case_count }}{{ $t('category.testCaseCount') }}
                </el-tag>
                <el-tag v-if="!data.is_active" size="small" type="warning">
                  {{ $t('common.inactive') }}
                </el-tag>
              </div>
              <div class="category-actions">
                <el-button size="small" type="primary" @click.stop="editCategory(data)">
                  {{ $t('common.edit') }}
                </el-button>
                <el-button size="small" type="success" @click.stop="addSubCategory(data)">
                  {{ $t('category.addSubCategory') }}
                </el-button>
                <el-button size="small" type="danger" @click.stop="deleteCategory(data)">
                  {{ $t('common.delete') }}
                </el-button>
              </div>
            </div>
          </template>
        </el-tree>
      </div>
    </el-card>

    <!-- 创建/编辑分类对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editingCategory ? $t('category.edit') : $t('category.create')"
      width="500px"
    >
      <el-form
        ref="categoryFormRef"
        :model="categoryForm"
        :rules="categoryRules"
        label-width="100px"
      >
        <el-form-item :label="$t('category.name')" prop="name">
          <el-input v-model="categoryForm.name" :placeholder="$t('category.placeholder.name')" />
        </el-form-item>
        
        <el-form-item :label="$t('category.description')" prop="description">
          <el-input
            v-model="categoryForm.description"
            type="textarea"
            :rows="3"
            :placeholder="$t('category.placeholder.description')"
          />
        </el-form-item>
        
        <el-form-item :label="$t('category.parentId')" prop="parent_id">
          <el-select
            v-model="categoryForm.parent_id"
            :placeholder="$t('category.placeholder.parent')"
            clearable
            style="width: 100%"
          >
            <el-option
              v-for="category in availableParentCategories"
              :key="category.id"
              :label="category.name"
              :value="category.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item :label="$t('category.sortOrder')" prop="sort_order">
          <el-input-number
            v-model="categoryForm.sort_order"
            :min="0"
            :max="999"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item v-if="editingCategory" :label="$t('category.isActive')" prop="is_active">
          <el-switch v-model="categoryForm.is_active" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showCreateDialog = false">{{ $t('common.cancel') }}</el-button>
          <el-button type="primary" @click="saveCategory" :loading="saving">
            {{ editingCategory ? $t('common.update') : $t('common.create') }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { categoryApi } from '@/services/api'
import type { Category, CategoryCreate, CategoryUpdate } from '@/types/api'

const { t } = useI18n()

const loading = ref(false)
const saving = ref(false)
const categoryTree = ref<Category[]>([])
const showCreateDialog = ref(false)
const editingCategory = ref<Category | null>(null)
const categoryTreeRef = ref()

// 表单相关
const categoryFormRef = ref<FormInstance>()
const categoryForm = ref<CategoryCreate & { is_active?: boolean }>({
  name: '',
  description: '',
  parent_id: undefined,
  sort_order: 0,
  is_active: true
})

// 表单验证规则
const categoryRules: FormRules = {
  name: [
    { required: true, message: t('category.validation.nameRequired'), trigger: 'blur' },
    { min: 1, max: 100, message: t('category.validation.nameLength'), trigger: 'blur' }
  ],
  description: [
    { max: 500, message: t('category.validation.descriptionLength'), trigger: 'blur' }
  ]
}

// 树形组件配置
const treeProps = {
  children: 'children',
  label: 'name'
}

// 可选的父分类列表（排除当前编辑的分类及其子分类）
const availableParentCategories = computed(() => {
  if (!editingCategory.value) {
    return categoryTree.value
  }
  
  // 递归获取所有子分类ID
  const getDescendantIds = (category: Category): number[] => {
    const ids = [category.id]
    if (category.children) {
      category.children.forEach(child => {
        ids.push(...getDescendantIds(child))
      })
    }
    return ids
  }
  
  const excludeIds = getDescendantIds(editingCategory.value)
  
  // 递归过滤分类树
  const filterCategories = (categories: Category[]): Category[] => {
    return categories
      .filter(cat => !excludeIds.includes(cat.id))
      .map(cat => ({
        ...cat,
        children: cat.children ? filterCategories(cat.children) : []
      }))
  }
  
  return filterCategories(categoryTree.value)
})

// 加载分类树
const loadCategoryTree = async () => {
  loading.value = true
  try {
    categoryTree.value = await categoryApi.getTree(false)
  } catch (error) {
    ElMessage.error(t('category.messages.loadFailed'))
  } finally {
    loading.value = false
  }
}

// 处理节点点击
const handleNodeClick = (data: Category) => {
  console.log('点击分类:', data)
}

// 编辑分类
const editCategory = (category: Category) => {
  editingCategory.value = category
  categoryForm.value = {
    name: category.name,
    description: category.description || '',
    parent_id: category.parent_id,
    sort_order: category.sort_order,
    is_active: category.is_active
  }
  showCreateDialog.value = true
}

// 添加子分类
const addSubCategory = (parentCategory: Category) => {
  editingCategory.value = null
  categoryForm.value = {
    name: '',
    description: '',
    parent_id: parentCategory.id,
    sort_order: 0,
    is_active: true
  }
  showCreateDialog.value = true
}

// 删除分类
const deleteCategory = async (category: Category) => {
  try {
    const message = category.children && category.children.length > 0
      ? t('category.messages.confirmDeleteWithChildren', { name: category.name })
      : t('category.messages.confirmDelete', { name: category.name })
      
    await ElMessageBox.confirm(message, t('common.confirm'), {
      confirmButtonText: t('common.confirm'),
      cancelButtonText: t('common.cancel'),
      type: 'warning'
    })
    
    await categoryApi.delete(category.id, true)
    ElMessage.success(t('category.messages.deleteSuccess'))
    loadCategoryTree()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(t('category.messages.deleteFailed'))
    }
  }
}

// 保存分类
const saveCategory = async () => {
  if (!categoryFormRef.value) return
  
  try {
    await categoryFormRef.value.validate()
    saving.value = true
    
    if (editingCategory.value) {
      // 更新分类
      const updateData: CategoryUpdate = {
        name: categoryForm.value.name,
        description: categoryForm.value.description,
        parent_id: categoryForm.value.parent_id,
        sort_order: categoryForm.value.sort_order,
        is_active: categoryForm.value.is_active
      }
      await categoryApi.update(editingCategory.value.id, updateData)
      ElMessage.success(t('category.messages.updateSuccess'))
    } else {
      // 创建分类
      const createData: CategoryCreate = {
        name: categoryForm.value.name,
        description: categoryForm.value.description,
        parent_id: categoryForm.value.parent_id,
        sort_order: categoryForm.value.sort_order
      }
      await categoryApi.create(createData)
      ElMessage.success(t('category.messages.createSuccess'))
    }
    
    showCreateDialog.value = false
    resetForm()
    loadCategoryTree()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(editingCategory.value ? t('category.messages.updateFailed') : t('category.messages.createFailed'))
    }
  } finally {
    saving.value = false
  }
}

// 重置表单
const resetForm = () => {
  editingCategory.value = null
  categoryForm.value = {
    name: '',
    description: '',
    parent_id: undefined,
    sort_order: 0,
    is_active: true
  }
  categoryFormRef.value?.clearValidate()
}

// 监听对话框关闭
const handleDialogClose = () => {
  resetForm()
}

onMounted(() => {
  loadCategoryTree()
})
</script>

<style scoped>
.categories {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.category-tree-container {
  min-height: 400px;
}

.category-node {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: 8px 0;
}

.category-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.category-name {
  font-weight: 500;
}

.category-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s;
}

.category-node:hover .category-actions {
  opacity: 1;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

:deep(.el-tree-node__content) {
  height: auto;
  padding: 4px 0;
}

:deep(.el-tree-node__content:hover) {
  background-color: #f5f7fa;
}
</style> 