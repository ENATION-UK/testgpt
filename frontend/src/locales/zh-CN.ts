export default {
  // 通用文本
  common: {
    // 按钮
    create: '创建',
    edit: '编辑',
    delete: '删除',
    save: '保存',
    cancel: '取消',
    confirm: '确认',
    reset: '重置',
    refresh: '刷新',
    search: '搜索',
    filter: '筛选',
    submit: '提交',
    update: '更新',
    view: '查看',
    back: '返回',
    next: '下一步',
    previous: '上一步',
    close: '关闭',
    ok: '确定',
    yes: '是',
    no: '否',
    loading: '加载中...',
    saving: '保存中...',
    testing: '测试中...',
    
    // 状态
    active: '激活',
    inactive: '非激活',
    draft: '草稿',
    pending: '待处理',
    running: '运行中',
    completed: '已完成',
    failed: '失败',
    success: '成功',
    error: '错误',
    warning: '警告',
    info: '信息',
    available: '可用',
    rateLimited: '限流中',
    
    // 优先级
    low: '低',
    medium: '中',
    high: '高',
    critical: '紧急',
    
    // 时间相关
    created_at: '创建时间',
    updated_at: '更新时间',
    started_at: '开始时间',
    completed_at: '完成时间',
    duration: '耗时',
    average_duration: '平均耗时',
    
    // 统计
    total: '总计',
    count: '数量',
    success_rate: '成功率',
    passed: '通过',
    total_count: '总计',
    success_count: '成功',
    failed_count: '失败',
    
    // 操作
    operation: '操作',
    actions: '操作',
    batch_delete: '批量删除',
    batch_execute: '批量执行',
    select_all: '全选',
    clear_selection: '清空选择',
    execute: '执行',
    executeHeadless: '执行（隐藏浏览器界面）',
    executeVisible: '执行（显示浏览器界面）',
    executionRecord: '执行记录',
    
    // 其他
    name: '名称',
    description: '描述',
    status: '状态',
    priority: '优先级',
    category: '分类',
    tags: '标签',
    sort_order: '排序',
    parent: '父级',
    children: '子级',
    empty: '暂无数据',
    no_data: '暂无数据',
    loading_failed: '加载失败',
    save_success: '保存成功',
    save_failed: '保存失败',
    delete_success: '删除成功',
    delete_failed: '删除失败',
    operation_success: '操作成功',
    operation_failed: '操作失败'
  },

  // 导航菜单
  nav: {
    home: '首页',
    testCases: '测试用例',
    categories: '分类管理',
    excelImport: 'Excel导入',
    executions: '执行记录',
    batchExecutions: '批量执行',
    statistics: '统计信息',
    multiModelSettings: '模型设置',
    promptSettings: '提示词设置'
  },

  // 首页
  home: {
    title: '欢迎使用 TestGPT',
    description: '基于Browser Use的智能Web自动化测试工具，支持语义化测试用例编写和详细的测试结果记录。',
    createTestCase: '创建测试用例',
    testCases: '测试用例',
    executions: '执行次数',
    successRate: '成功率',
    averageDuration: '平均耗时',
    recentExecutions: '最近执行记录',
    quickActions: '快速操作',
    manageTestCases: '管理测试用例',
    viewExecutions: '查看执行记录',
    viewStatistics: '查看统计信息',
    noExecutionRecords: '暂无执行记录'
  },

  // 测试用例
  testCase: {
    title: '测试用例管理',
    create: '创建测试用例',
    edit: '编辑测试用例',
    view: '查看测试用例',
    delete: '删除测试用例',
    batchDelete: '批量删除',
    batchExecute: '批量执行',
    importExcel: '导入Excel',
    categoryManagement: '分类管理',
    name: '测试用例名称',
    taskContent: '操作步骤',
    expectedResult: '预期结果',
    categoryId: '分类',
    priority: '优先级',
    status: '状态',
    tags: '标签',
    noTaskContent: '暂无任务内容',
    noExpectedResult: '暂无预期结果',
    noTags: '暂无标签',
    placeholder: {
      name: '请输入测试用例名称',
      taskContent: '请输入具体的操作步骤，例如：1. 打开网站 2. 点击登录按钮 3. 输入用户名密码等',
      expectedResult: '请输入预期测试结果',
      category: '请选择分类',
      priority: '请选择优先级',
      status: '请选择状态',
      tags: '输入标签后按回车添加'
    },
    validation: {
      nameRequired: '请输入测试用例名称',
      nameLength: '测试用例名称长度在 1 到 100 个字符',
      taskContentRequired: '请输入操作步骤',
      taskContentLength: '操作步骤长度在 1 到 1000 个字符',
      expectedResultLength: '预期结果长度不能超过 500 个字符',
      categoryRequired: '请选择分类',
      priorityRequired: '请选择优先级',
      statusRequired: '请选择状态'
    },
    messages: {
      createSuccess: '测试用例创建成功',
      createFailed: '测试用例创建失败',
      updateSuccess: '测试用例更新成功',
      updateFailed: '测试用例更新失败',
      deleteSuccess: '测试用例删除成功',
      deleteFailed: '测试用例删除失败',
      loadFailed: '加载测试用例失败',
      notFound: '测试用例不存在',
      confirmDelete: '确定要删除这个测试用例吗？',
      confirmBatchDelete: '确定要删除选中的测试用例吗？'
    }
  },

  // 分类管理
  category: {
    title: '分类管理',
    create: '创建分类',
    edit: '编辑分类',
    delete: '删除分类',
    addSubCategory: '添加子分类',
    name: '分类名称',
    description: '分类描述',
    parentId: '父分类',
    sortOrder: '排序',
    isActive: '状态',
    testCaseCount: '个用例',
    placeholder: {
      name: '请输入分类名称',
      description: '请输入分类描述',
      parent: '请选择父分类（可选）'
    },
    validation: {
      nameRequired: '请输入分类名称',
      nameLength: '分类名称长度在 1 到 100 个字符',
      descriptionLength: '分类描述长度不能超过 500 个字符'
    },
    messages: {
      createSuccess: '分类创建成功',
      createFailed: '分类创建失败',
      updateSuccess: '分类更新成功',
      updateFailed: '分类更新失败',
      deleteSuccess: '删除成功',
      deleteFailed: '删除失败',
      loadFailed: '加载分类树失败',
      confirmDelete: '确定要删除分类 "{name}" 吗？',
      confirmDeleteWithChildren: '确定要删除分类 "{name}" 及其所有子分类吗？'
    }
  },

  // 执行记录
  execution: {
    title: '执行记录',
    testCaseExecutions: '测试用例 {id} 的执行记录',
    executionName: '执行名称',
    testCaseId: '测试用例ID',
    overallStatus: '状态',
    stepStats: '步骤统计',
    totalSteps: '总步骤',
    passedSteps: '通过步骤',
    duration: '耗时',
    viewDetails: '查看详情',
    backToTestCase: '返回测试用例',
    detail: '执行详情',
    completedSteps: '个已完成步骤',
    messages: {
      loadFailed: '加载执行记录失败'
    }
  },

  // 批量执行
  batchExecution: {
    title: '批量执行任务',
    taskName: '任务名称',
    status: '状态',
    progress: '进度',
    statistics: '统计信息',
    startTime: '开始时间',
    completeTime: '完成时间',
    execute: '执行',
    stop: '停止',
    viewDetails: '查看详情',
    realtimeConnection: '实时连接',
    connectionDisconnected: '连接断开',
    detail: '批量执行任务详情',
    taskInfo: '任务信息',
    messages: {
      startSuccess: '批量执行已开始',
      startFailed: '启动批量执行失败',
      stopSuccess: '批量执行已停止',
      stopFailed: '停止批量执行失败',
      loadFailed: '加载批量执行记录失败'
    }
  },

  // 统计信息
  statistics: {
    title: '统计信息',
    totalTestCases: '测试用例总数',
    totalExecutions: '执行总次数',
    successRate: '成功率',
    averageDuration: '平均耗时',
    categoryStats: '分类统计',
    priorityStats: '优先级统计',
    noCategoryData: '暂无分类数据',
    noPriorityData: '暂无优先级数据',
    messages: {
      loadFailed: '加载统计信息失败'
    }
  },

  // 设置页面
  settings: {
    multiModel: {
      title: '多模型配置',
      description: '配置多个模型提供商和API密钥，实现轮询机制增加并发限制',
      providerConfig: '模型提供商配置',
      testConfig: '测试配置',
      saveConfig: '保存配置',
      providerName: '提供商名称',
      modelType: '模型类型',
      baseUrl: 'API基础URL',
      apiKey: 'API密钥',
      maxTokens: '最大Token数',
      temperature: '温度',
      timeout: '超时时间(秒)',
      maxRetries: '最大重试次数',
      isActive: '启用',
      disabled: '禁用',
      addProvider: '添加提供商',
      removeProvider: '删除',
      placeholder: {
        providerName: '如：OpenAI账号1',
        modelType: '选择模型类型',
        baseUrl: 'API基础URL',
        apiKey: '请输入API密钥',
        maxTokens: '最大Token数',
        temperature: '温度值(0-2)',
        timeout: '超时时间',
        maxRetries: '最大重试次数'
      },
      tips: {
        baseUrl: 'DeepSeek: https://api.deepseek.com/v1, OpenAI: https://api.openai.com/v1, 豆包: https://api.doubao.com',
        apiKey: '请输入有效的API密钥',
        maxTokens: '单次请求的最大Token数量',
        temperature: '控制输出的随机性，0-2之间',
        timeout: '请求超时时间，单位秒',
        maxRetries: '请求失败时的最大重试次数'
      },
      configStatus: '配置状态',
      totalProviders: '总提供商数',
      totalApiKeys: '总API密钥数',
      currentProviderIndex: '当前提供商索引',
      providerDetails: '提供商详情',
      apiKeyCount: 'API密钥数',
      rateLimit: '限流数量',
      currentRequests: '当前请求数',
      messages: {
        saveSuccess: '配置保存成功',
        saveFailed: '配置保存失败',
        testSuccess: '配置测试成功',
        testFailed: '配置测试失败',
        loadFailed: '加载配置失败',
        atLeastOneProvider: '至少需要保留一个提供商',
        confirmDelete: '确定要删除这个提供商吗？',
        providerNameRequired: '提供商名称不能为空',
        apiKeyRequired: '提供商 {name} 必须配置至少一个API密钥',
        getStatusFailed: '获取状态失败'
      },
      labels: {
        providerName: '提供商名称',
        modelType: '模型类型',
        baseUrl: 'API基础URL',
        modelName: '模型名称',
        temperature: '温度参数',
        maxTokens: '最大Token数',
        rateLimit: '限流数量',
        apiKeyConfig: 'API密钥配置'
      },
      placeholders: {
        providerName: '如：OpenAI账号1',
        selectModelType: '选择模型类型',
        baseUrl: 'API基础URL',
        modelName: '模型名称',
        apiKey: '请输入API密钥',
        noLimit: '不限制'
      },
      tips: {
        baseUrlExamples: 'DeepSeek: https://api.deepseek.com/v1, OpenAI: https://api.openai.com/v1, 豆包: https://api.doubao.com',
        modelExamples: 'DeepSeek: deepseek-chat, OpenAI: gpt-4o, 豆包: doubao-v1.5',
        rateLimitTip: '每分钟最大请求数'
      },
      actions: {
        enable: '启用',
        disable: '禁用',
        delete: '删除',
        addApiKey: '添加API密钥'
      },
      modelTypes: {
        deepseek: 'DeepSeek',
        openai: 'OpenAI',
        doubao: '豆包'
      },
      defaultProviderName: 'DeepSeek默认配置',
      providerNameTemplate: '模型提供商 {index}'
    },
    prompt: {
      title: '提示词设置',
      description: '配置自定义提示词，将拼合进 Agent 的测试系统提示词中',
      promptConfig: '提示词配置',
      saveConfig: '保存配置',
      customPrompt: '自定义提示词',
      configStatus: '配置状态',
      usageInstructions: '使用说明',
      placeholder: {
        customPrompt: '请输入自定义提示词，这些内容将拼合进 Agent 的测试系统提示词中'
      },
      tips: {
        customPrompt: '自定义提示词将追加到默认的系统提示词后面，用于定制 Agent 的行为'
      },
      status: {
        valid: '配置有效',
        invalid: '配置无效',
        validDescription: '提示词配置已正确设置',
        invalidDescription: '请检查提示词配置',
        notSet: '（未设置）'
      },
      usage: {
        title: '提示词的作用',
        description: '自定义提示词将拼合进 Agent 的测试系统提示词中，用于：',
        purposes: [
          '通用、常用的测试步骤说明',
          '定制 Agent 的行为和决策逻辑',
          '添加特定的测试要求或验证标准',
          '调整 Agent 的响应风格和详细程度',
          '增加特定业务场景的测试指导'
        ],
        examples: {
          title: '示例提示词',
          commonSteps: {
            title: '通用、常用的测试步骤说明：',
            content: `# 请记住以下通用操作
## 登录后台
打开网址:https://www.demo.com/login
输入用户名user
密码password
点击登录## 重要:如有需要以上通用操作请直接应用在具体用例中`
          },
          businessRequirements: {
            title: '特定业务要求：',
            content: '在测试过程中，请特别关注用户体验相关的细节，如页面加载速度、交互响应时间等。'
          },
          errorHandling: {
            title: '错误处理：',
            content: '如果遇到网络错误或页面加载失败，请尝试重新加载页面，最多重试3次。'
          }
        }
      },
      messages: {
        saveSuccess: '提示词配置保存成功',
        saveFailed: '提示词配置保存失败',
        loadFailed: '加载提示词配置失败'
      }
    }
  },

  // Excel导入
  excelImport: {
    title: 'Excel批量导入',
    description: '支持大文件分批处理，实时显示导入进度',
    selectFile: '选择Excel文件',
    uploadFile: '上传文件',
    downloadTemplate: '下载模板',
    importData: '导入数据',
    importProgress: '导入进度',
    importResult: '导入结果',
    successCount: '成功数量',
    failedCount: '失败数量',
    totalCount: '总数量',
    importMode: '导入模式',
    smartMode: '智能识别模式',
    smartModeDesc: '支持各种格式的Excel文件，自动识别列名和内容',
    standardMode: '标准模版模式',
    standardModeDesc: '使用统一的标准模版格式，保证数据质量',
    dragFile: '将Excel文件拖到此处，或',
    clickUpload: '点击上传',
    uploadTip: '只能上传xlsx/xls文件，且不超过10MB',
    previewData: '预览数据 (前5行)',
    importOptions: '导入选项',
    defaultStatus: '默认状态',
    defaultPriority: '默认优先级',
    defaultCategory: '默认分类',
    selectDefaultStatus: '选择默认状态',
    selectDefaultPriority: '选择默认优先级',
    enterDefaultCategory: '输入默认分类',
    import: '导入',
    importing: '导入中...',
    startImport: '开始导入',
    useStandardTemplate: '使用标准模版',
    templateDescription: '请先下载标准模版，按照模版格式填写数据后上传',
    viewSample: '查看样例',
    smartModeDescription: '支持各种列名格式，如：标题/名称/Name、步骤描述/任务内容、预期结果等',
    importConfig: '导入配置',
    taskName: '任务名称',
    taskNamePlaceholder: '为此次导入任务命名',
    batchSize: '批次大小',
    batchSizePlaceholder: '每批处理行数',
    selectDefaultCategory: '选择默认分类',
    clearFile: '清除文件',
    taskInProgress: '有导入任务正在进行中',
    taskInProgressDescription: '系统同时只能运行一个导入任务，请等待当前任务完成后再试',
    importTask: '导入任务',
    overallProgress: '总体进度',
    rows: '行',
    batchProgress: '批次进度',
    batch: '批次',
    successImport: '成功导入',
    failedImport: '导入失败',
    totalRows: '总行数',
    recentErrors: '最近错误',
    cancelTask: '取消任务',
    viewResults: '查看结果',
    importHistory: '导入历史',
    fileName: '文件名',
    viewDetails: '查看详情',
    messages: {
      uploadSuccess: '文件上传成功',
      uploadFailed: '文件上传失败',
      importSuccess: '数据导入成功',
      importFailed: '数据导入失败',
      invalidFile: '请选择有效的Excel文件',
      fileTooLarge: '文件大小不能超过10MB'
    }
  },

  // 错误消息
  messages: {
    // 通用错误
    networkError: '网络错误，请检查网络连接',
    serverError: '服务器错误，请稍后重试',
    unauthorized: '未授权访问',
    forbidden: '访问被禁止',
    notFound: '资源不存在',
    validationError: '数据验证失败',
    
    // 业务错误
    testCaseNotFound: '测试用例不存在',
    categoryNotFound: '分类不存在',
    executionNotFound: '执行记录不存在',
    batchExecutionNotFound: '批量执行任务不存在',
    configNotFound: '配置不存在',
    
    // 操作错误
    operationNotAllowed: '操作不被允许',
    dataInUse: '数据正在使用中，无法删除',
    duplicateData: '数据已存在',
    invalidData: '数据格式无效',
    
    // 系统错误
    systemBusy: '系统繁忙，请稍后重试',
    timeout: '请求超时',
    unknownError: '未知错误'
  },

  // 表单验证
  validation: {
    required: '此字段为必填项',
    minLength: '长度不能少于 {min} 个字符',
    maxLength: '长度不能超过 {max} 个字符',
    min: '值不能小于 {min}',
    max: '值不能大于 {max}',
    email: '请输入有效的邮箱地址',
    url: '请输入有效的URL',
    number: '请输入有效的数字',
    integer: '请输入有效的整数',
    positive: '请输入正数',
    negative: '请输入负数',
    pattern: '格式不正确',
    custom: '验证失败'
  },

  // 语言切换
  language: {
    switch: '切换语言',
    chinese: '中文',
    english: 'English',
    current: '当前语言'
  }
}
