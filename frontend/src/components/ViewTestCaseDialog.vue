<template>
    <el-dialog
      v-model="visible"
      :title="$t('testCase.view')"
      width="700px"
      :before-close="handleClose"
    >
      <div v-if="testCase" class="test-case-details">
        <el-descriptions :column="2" border>
          <el-descriptions-item :label="$t('common.name')">
            {{ testCase.name }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('common.category')">
            {{ testCase.category }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('common.priority')">
            <el-tag :type="getPriorityType(testCase.priority)">
              {{ getPriorityLabel(testCase.priority) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item :label="$t('common.status')">
            <el-tag :type="getStatusType(testCase.status)">
              {{ getStatusLabel(testCase.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item :label="$t('common.created_at')" :span="2">
            {{ testCase.created_at ? formatDate(testCase.created_at) : '' }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('testCase.taskContent')" :span="2">
            <div class="task-content">{{ testCase.task_content || $t('testCase.noTaskContent') }}</div>
          </el-descriptions-item>
          <el-descriptions-item :label="$t('testCase.expectedResult')" :span="2">
            {{ testCase.expected_result || $t('testCase.noExpectedResult') }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('testCase.tags')" :span="2">
            <div v-if="testCase.tags && testCase.tags.length > 0">
              <el-tag
                v-for="tag in testCase.tags"
                :key="tag"
                style="margin-right: 8px; margin-bottom: 8px"
              >
                {{ tag }}
              </el-tag>
            </div>
            <span v-else class="no-tags">{{ $t('testCase.noTags') }}</span>
          </el-descriptions-item>
        </el-descriptions>
      </div>
  
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="handleClose">{{ $t('common.close') }}</el-button>
          <el-button type="primary" @click="handleEdit">{{ $t('common.edit') }}</el-button>
        </div>
      </template>
    </el-dialog>
  </template>
  
  <script setup lang="ts">
  import { computed } from 'vue'
  import { useI18n } from 'vue-i18n'
  import type { TestCase } from '@/types/api'

  const { t } = useI18n()
  
  interface Props {
    modelValue: boolean
    testCase: TestCase | null
  }
  
  interface Emits {
    (e: 'update:modelValue', value: boolean): void
    (e: 'edit', testCase: TestCase): void
  }
  
  const props = defineProps<Props>()
  const emit = defineEmits<Emits>()
  
  const visible = computed({
    get: () => props.modelValue,
    set: (value) => emit('update:modelValue', value)
  })
  
  const handleClose = () => {
    visible.value = false
  }
  
  const handleEdit = () => {
    if (props.testCase) {
      emit('edit', props.testCase)
      visible.value = false
    }
  }
  
  const getPriorityType = (priority: string): string => {
    const types = {
      low: 'info',
      medium: 'warning',
      high: 'danger',
      critical: 'danger'
    }
    return types[priority as keyof typeof types] || 'info'
  }
  
  const getPriorityLabel = (priority: string): string => {
    const labels = {
      low: '低',
      medium: '中',
      high: '高',
      critical: '紧急'
    }
    return labels[priority as keyof typeof labels] || priority
  }
  
  const getStatusType = (status: string): string => {
    const types = {
      active: 'success',
      inactive: 'info',
      draft: 'warning'
    }
    return types[status as keyof typeof types] || 'info'
  }
  
  const getStatusLabel = (status: string): string => {
    const labels = {
      active: '激活',
      inactive: '非激活',
      draft: '草稿'
    }
    return labels[status as keyof typeof labels] || status
  }
  
  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleString('zh-CN')
  }
  </script>
  
  <style scoped>
  .test-case-details {
    max-height: 60vh;
    overflow-y: auto;
  }
  
  .task-content {
    white-space: pre-wrap;
    word-break: break-word;
    line-height: 1.5;
  }
  
  .no-tags {
    color: #909399;
    font-style: italic;
  }
  
  .dialog-footer {
    text-align: right;
  }
  </style>