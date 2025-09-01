import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/test-cases',
      name: 'test-cases',
      component: () => import('../views/TestCasesView.vue')
    },
    {
      path: '/executions',
      name: 'executions',
      component: () => import('../views/ExecutionsView.vue')
    },
    {
      path: '/test-cases/:testCaseId/executions',
      name: 'test-case-executions',
      component: () => import('../views/ExecutionsView.vue')
    },
    {
      path: '/statistics',
      name: 'statistics',
      component: () => import('../views/StatisticsView.vue')
    },
    {
      path: '/executions/:executionId',
      name: 'execution-detail',
      component: () => import('../views/ExecutionDetailView.vue')
    },
    {
      path: '/model-settings',
      name: 'model-settings',
      component: () => import('../views/ModelSettingsView.vue')
    },
    {
      path: '/multi-model-settings',
      name: 'multi-model-settings',
      component: () => import('../views/MultiModelSettingsView.vue')
    },
    {
      path: '/prompt-settings',
      name: 'prompt-settings',
      component: () => import('../views/PromptSettingsView.vue')
    },
    {
      path: '/batch-executions',
      name: 'batch-executions',
      component: () => import('../views/BatchExecutionsView.vue')
    },
    {
      path: '/batch-executions/:id',
      name: 'batch-execution-detail',
      component: () => import('../views/BatchExecutionDetailView.vue')
    },
    {
      path: '/categories',
      name: 'categories',
      component: () => import('../views/CategoriesView.vue')
    },
    {
      path: '/excel-import',
      name: 'excel-import',
      component: () => import('../views/ExcelImportView.vue')
    }
  ]
})

export default router