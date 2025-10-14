export default {
  // Common text
  common: {
    // Buttons
    create: 'Create',
    edit: 'Edit',
    delete: 'Delete',
    save: 'Save',
    cancel: 'Cancel',
    confirm: 'Confirm',
    reset: 'Reset',
    refresh: 'Refresh',
    search: 'Search',
    filter: 'Filter',
    submit: 'Submit',
    update: 'Update',
    view: 'View',
    back: 'Back',
    next: 'Next',
    previous: 'Previous',
    close: 'Close',
    ok: 'OK',
    yes: 'Yes',
    no: 'No',
    loading: 'Loading...',
    saving: 'Saving...',
    testing: 'Testing...',
    
    // Status
    active: 'Active',
    inactive: 'Inactive',
    draft: 'Draft',
    pending: 'Pending',
    running: 'Running',
    completed: 'Completed',
    failed: 'Failed',
    success: 'Success',
    error: 'Error',
    warning: 'Warning',
    info: 'Info',
    available: 'Available',
    rateLimited: 'Rate Limited',
    
    // Priority
    low: 'Low',
    medium: 'Medium',
    high: 'High',
    critical: 'Critical',
    
    // Time related
    created_at: 'Created At',
    updated_at: 'Updated At',
    started_at: 'Started At',
    completed_at: 'Completed At',
    duration: 'Duration',
    average_duration: 'Average Duration',
    
    // Statistics
    total: 'Total',
    count: 'Count',
    success_rate: 'Success Rate',
    passed: 'Passed',
    total_count: 'Total Count',
    success_count: 'Success Count',
    failed_count: 'Failed Count',
    
    // Operations
    operation: 'Operation',
    actions: 'Actions',
    batch_delete: 'Batch Delete',
    batch_execute: 'Batch Execute',
    select_all: 'Select All',
    clear_selection: 'Clear Selection',
    execute: 'Execute',
    executeHeadless: 'Execute (Headless)',
    executeVisible: 'Execute (Visible)',
    executionRecord: 'Execution Record',
    
    // Others
    name: 'Name',
    description: 'Description',
    status: 'Status',
    priority: 'Priority',
    category: 'Category',
    tags: 'Tags',
    sort_order: 'Sort Order',
    parent: 'Parent',
    children: 'Children',
    empty: 'No Data',
    no_data: 'No Data',
    loading_failed: 'Loading Failed',
    save_success: 'Save Success',
    save_failed: 'Save Failed',
    delete_success: 'Delete Success',
    delete_failed: 'Delete Failed',
    operation_success: 'Operation Success',
    operation_failed: 'Operation Failed'
  },

  // Navigation menu
  nav: {
    home: 'Home',
    testCases: 'Test Cases',
    categories: 'Categories',
    excelImport: 'Excel Import',
    executions: 'Executions',
    batchExecutions: 'Batch Executions',
    statistics: 'Statistics',
    multiModelSettings: 'Model Settings',
    promptSettings: 'Prompt Settings'
  },

  // Home page
  home: {
    title: 'Welcome to TestGPT',
    description: 'Intelligent web automation testing tool based on Browser Use, supporting semantic test case writing and detailed test result recording.',
    createTestCase: 'Create Test Case',
    testCases: 'Test Cases',
    executions: 'Executions',
    successRate: 'Success Rate',
    averageDuration: 'Average Duration',
    recentExecutions: 'Recent Executions',
    quickActions: 'Quick Actions',
    manageTestCases: 'Manage Test Cases',
    viewExecutions: 'View Executions',
    viewStatistics: 'View Statistics',
    noExecutionRecords: 'No Execution Records'
  },

  // Test cases
  testCase: {
    title: 'Test Case Management',
    create: 'Create Test Case',
    edit: 'Edit Test Case',
    view: 'View Test Case',
    delete: 'Delete Test Case',
    batchDelete: 'Batch Delete',
    batchExecute: 'Batch Execute',
    importExcel: 'Import Excel',
    categoryManagement: 'Category Management',
    name: 'Test Case Name',
    taskContent: 'Task Steps',
    expectedResult: 'Expected Result',
    categoryId: 'Category',
    priority: 'Priority',
    status: 'Status',
    tags: 'Tags',
    noTaskContent: 'No task content',
    noExpectedResult: 'No expected result',
    noTags: 'No tags',
    placeholder: {
      name: 'Please enter test case name',
      taskContent: 'Please enter specific operation steps, e.g.: 1. Open website 2. Click login button 3. Enter username and password',
      expectedResult: 'Please enter expected test result',
      category: 'Please select category',
      priority: 'Please select priority',
      status: 'Please select status',
      tags: 'Enter tag and press Enter to add'
    },
    validation: {
      nameRequired: 'Please enter test case name',
      nameLength: 'Test case name length should be between 1 and 100 characters',
      taskContentRequired: 'Please enter operation steps',
      taskContentLength: 'Task content length should be between 1 and 1000 characters',
      expectedResultLength: 'Expected result length cannot exceed 500 characters',
      categoryRequired: 'Please select category',
      priorityRequired: 'Please select priority',
      statusRequired: 'Please select status'
    },
    messages: {
      createSuccess: 'Test case created successfully',
      createFailed: 'Failed to create test case',
      updateSuccess: 'Test case updated successfully',
      updateFailed: 'Failed to update test case',
      deleteSuccess: 'Test case deleted successfully',
      deleteFailed: 'Failed to delete test case',
      loadFailed: 'Failed to load test cases',
      notFound: 'Test case not found',
      confirmDelete: 'Are you sure to delete this test case?',
      confirmBatchDelete: 'Are you sure to delete selected test cases?'
    }
  },

  // Category management
  category: {
    title: 'Category Management',
    create: 'Create Category',
    edit: 'Edit Category',
    delete: 'Delete Category',
    addSubCategory: 'Add Sub Category',
    name: 'Category Name',
    description: 'Category Description',
    parentId: 'Parent Category',
    sortOrder: 'Sort Order',
    isActive: 'Status',
    testCaseCount: ' test cases',
    placeholder: {
      name: 'Please enter category name',
      description: 'Please enter category description',
      parent: 'Please select parent category (optional)'
    },
    validation: {
      nameRequired: 'Please enter category name',
      nameLength: 'Category name length should be between 1 and 100 characters',
      descriptionLength: 'Category description length cannot exceed 500 characters'
    },
    messages: {
      createSuccess: 'Category created successfully',
      createFailed: 'Failed to create category',
      updateSuccess: 'Category updated successfully',
      updateFailed: 'Failed to update category',
      deleteSuccess: 'Delete successful',
      deleteFailed: 'Delete failed',
      loadFailed: 'Failed to load category tree',
      confirmDelete: 'Are you sure to delete category "{name}"?',
      confirmDeleteWithChildren: 'Are you sure to delete category "{name}" and all its subcategories?'
    }
  },

  // Execution records
  execution: {
    title: 'Execution Records',
    testCaseExecutions: 'Test Case {id} Execution Records',
    executionName: 'Execution Name',
    testCaseId: 'Test Case ID',
    overallStatus: 'Status',
    stepStats: 'Step Statistics',
    totalSteps: 'Total Steps',
    passedSteps: 'Passed Steps',
    duration: 'Duration',
    viewDetails: 'View Details',
    backToTestCase: 'Back to Test Case',
    detail: 'Execution Details',
    completedSteps: 'completed steps',
    messages: {
      loadFailed: 'Failed to load execution records'
    }
  },

  // Batch execution
  batchExecution: {
    title: 'Batch Execution Tasks',
    taskName: 'Task Name',
    status: 'Status',
    progress: 'Progress',
    statistics: 'Statistics',
    startTime: 'Start Time',
    completeTime: 'Complete Time',
    execute: 'Execute',
    stop: 'Stop',
    viewDetails: 'View Details',
    realtimeConnection: 'Realtime Connection',
    connectionDisconnected: 'Connection Disconnected',
    detail: 'Batch Execution Task Details',
    taskInfo: 'Task Information',
    messages: {
      startSuccess: 'Batch execution started',
      startFailed: 'Failed to start batch execution',
      stopSuccess: 'Batch execution stopped',
      stopFailed: 'Failed to stop batch execution',
      loadFailed: 'Failed to load batch execution records'
    }
  },

  // Statistics
  statistics: {
    title: 'Statistics',
    totalTestCases: 'Total Test Cases',
    totalExecutions: 'Total Executions',
    successRate: 'Success Rate',
    averageDuration: 'Average Duration',
    categoryStats: 'Category Statistics',
    priorityStats: 'Priority Statistics',
    noCategoryData: 'No category data',
    noPriorityData: 'No priority data',
    messages: {
      loadFailed: 'Failed to load statistics'
    }
  },

  // Settings pages
  settings: {
    multiModel: {
      title: 'Multi-Model Configuration',
      description: 'Configure multiple model providers and API keys to implement polling mechanism and increase concurrency limits',
      providerConfig: 'Model Provider Configuration',
      testConfig: 'Test Configuration',
      saveConfig: 'Save Configuration',
      providerName: 'Provider Name',
      modelType: 'Model Type',
      baseUrl: 'API Base URL',
      apiKey: 'API Key',
      maxTokens: 'Max Tokens',
      temperature: 'Temperature',
      timeout: 'Timeout (seconds)',
      maxRetries: 'Max Retries',
      isActive: 'Enable',
      disabled: 'Disable',
      addProvider: 'Add Provider',
      removeProvider: 'Remove',
      placeholder: {
        providerName: 'e.g.: OpenAI Account 1',
        modelType: 'Select model type',
        baseUrl: 'API Base URL',
        apiKey: 'Please enter API key',
        maxTokens: 'Max tokens',
        temperature: 'Temperature value (0-2)',
        timeout: 'Timeout',
        maxRetries: 'Max retries'
      },
      tips: {
        baseUrl: 'DeepSeek: https://api.deepseek.com/v1, OpenAI: https://api.openai.com/v1, Doubao: https://api.doubao.com',
        apiKey: 'Please enter valid API key',
        maxTokens: 'Maximum token count for single request',
        temperature: 'Controls output randomness, between 0-2',
        timeout: 'Request timeout in seconds',
        maxRetries: 'Maximum retry count when request fails'
      },
      configStatus: 'Configuration Status',
      totalProviders: 'Total Providers',
      totalApiKeys: 'Total API Keys',
      currentProviderIndex: 'Current Provider Index',
      providerDetails: 'Provider Details',
      apiKeyCount: 'API Key Count',
      rateLimit: 'Rate Limit',
      currentRequests: 'Current Requests',
      messages: {
        saveSuccess: 'Configuration saved successfully',
        saveFailed: 'Failed to save configuration',
        testSuccess: 'Configuration test successful',
        testFailed: 'Configuration test failed',
        loadFailed: 'Failed to load configuration',
        atLeastOneProvider: 'At least one provider must be kept',
        confirmDelete: 'Are you sure to delete this provider?',
        providerNameRequired: 'Provider name cannot be empty',
        apiKeyRequired: 'Provider {name} must configure at least one API key',
        getStatusFailed: 'Failed to get status'
      },
      labels: {
        providerName: 'Provider Name',
        modelType: 'Model Type',
        baseUrl: 'API Base URL',
        modelName: 'Model Name',
        temperature: 'Temperature',
        maxTokens: 'Max Tokens',
        rateLimit: 'Rate Limit',
        apiKeyConfig: 'API Key Configuration'
      },
      placeholders: {
        providerName: 'e.g.: OpenAI Account 1',
        selectModelType: 'Select model type',
        baseUrl: 'API Base URL',
        modelName: 'Model Name',
        apiKey: 'Please enter API key',
        noLimit: 'No limit'
      },
      tips: {
        baseUrlExamples: 'DeepSeek: https://api.deepseek.com/v1, OpenAI: https://api.openai.com/v1, Doubao: https://api.doubao.com',
        modelExamples: 'DeepSeek: deepseek-chat, OpenAI: gpt-4o, Doubao: doubao-v1.5',
        rateLimitTip: 'Maximum requests per minute'
      },
      actions: {
        enable: 'Enable',
        disable: 'Disable',
        delete: 'Delete',
        addApiKey: 'Add API Key'
      },
      modelTypes: {
        deepseek: 'DeepSeek',
        openai: 'OpenAI',
        doubao: 'Doubao'
      },
      defaultProviderName: 'DeepSeek Default Configuration',
      providerNameTemplate: 'Model Provider {index}'
    },
    prompt: {
      title: 'Prompt Settings',
      description: 'Configure custom prompts that will be combined into the Agent\'s test system prompts',
      promptConfig: 'Prompt Configuration',
      saveConfig: 'Save Configuration',
      customPrompt: 'Custom Prompt',
      configStatus: 'Configuration Status',
      usageInstructions: 'Usage Instructions',
      placeholder: {
        customPrompt: 'Please enter custom prompt, this content will be combined into the Agent\'s test system prompts'
      },
      tips: {
        customPrompt: 'Custom prompt will be appended to the default system prompt for customizing Agent behavior'
      },
      status: {
        valid: 'Configuration Valid',
        invalid: 'Configuration Invalid',
        validDescription: 'Prompt configuration is correctly set',
        invalidDescription: 'Please check prompt configuration',
        notSet: '(Not Set)'
      },
      usage: {
        title: 'Purpose of Prompts',
        description: 'Custom prompts will be combined into the Agent\'s test system prompts for:',
        purposes: [
          'Common and frequently used test step descriptions',
          'Customizing Agent behavior and decision logic',
          'Adding specific test requirements or validation criteria',
          'Adjusting Agent response style and detail level',
          'Adding specific business scenario test guidance'
        ],
        examples: {
          title: 'Example Prompts',
          commonSteps: {
            title: 'Common and frequently used test step descriptions:',
            content: `# Please remember the following common operations
## Login to backend
Open URL: https://www.demo.com/login
Enter username: user
Enter password: password
Click login## Important: If needed, apply the above common operations directly in specific test cases`
          },
          businessRequirements: {
            title: 'Specific business requirements:',
            content: 'During testing, please pay special attention to user experience related details, such as page loading speed and interaction response time.'
          },
          errorHandling: {
            title: 'Error handling:',
            content: 'If you encounter network errors or page loading failures, please try reloading the page, with a maximum of 3 retries.'
          }
        }
      },
      messages: {
        saveSuccess: 'Prompt configuration saved successfully',
        saveFailed: 'Failed to save prompt configuration',
        loadFailed: 'Failed to load prompt configuration'
      }
    }
  },

  // Excel import
  excelImport: {
    title: 'Excel Batch Import',
    description: 'Supports large file batch processing with real-time import progress',
    selectFile: 'Select Excel File',
    uploadFile: 'Upload File',
    downloadTemplate: 'Download Template',
    importData: 'Import Data',
    importProgress: 'Import Progress',
    importResult: 'Import Result',
    successCount: 'Success Count',
    failedCount: 'Failed Count',
    totalCount: 'Total Count',
    importMode: 'Import Mode',
    smartMode: 'Smart Recognition Mode',
    smartModeDesc: 'Supports various Excel file formats, automatically recognizes column names and content',
    standardMode: 'Standard Template Mode',
    standardModeDesc: 'Uses unified standard template format to ensure data quality',
    dragFile: 'Drag Excel file here, or',
    clickUpload: 'click to upload',
    uploadTip: 'Only xlsx/xls files are supported, and file size cannot exceed 10MB',
    previewData: 'Preview Data (First 5 rows)',
    importOptions: 'Import Options',
    defaultStatus: 'Default Status',
    defaultPriority: 'Default Priority',
    defaultCategory: 'Default Category',
    selectDefaultStatus: 'Select default status',
    selectDefaultPriority: 'Select default priority',
    enterDefaultCategory: 'Enter default category',
    import: 'Import',
    importing: 'Importing...',
    startImport: 'Start Import',
    useStandardTemplate: 'Use Standard Template',
    templateDescription: 'Please download the standard template first, fill in the data according to the template format, then upload',
    viewSample: 'View Sample',
    smartModeDescription: 'Supports various column name formats, such as: Title/Name, Step Description/Task Content, Expected Result, etc.',
    importConfig: 'Import Configuration',
    taskName: 'Task Name',
    taskNamePlaceholder: 'Name this import task',
    batchSize: 'Batch Size',
    batchSizePlaceholder: 'Rows per batch',
    selectDefaultCategory: 'Select default category',
    clearFile: 'Clear File',
    taskInProgress: 'Import task in progress',
    taskInProgressDescription: 'The system can only run one import task at a time, please wait for the current task to complete',
    importTask: 'Import Task',
    overallProgress: 'Overall Progress',
    rows: 'rows',
    batchProgress: 'Batch Progress',
    batch: 'Batch',
    successImport: 'Successfully Imported',
    failedImport: 'Import Failed',
    totalRows: 'Total Rows',
    recentErrors: 'Recent Errors',
    cancelTask: 'Cancel Task',
    viewResults: 'View Results',
    importHistory: 'Import History',
    fileName: 'File Name',
    viewDetails: 'View Details',
    messages: {
      uploadSuccess: 'File uploaded successfully',
      uploadFailed: 'Failed to upload file',
      importSuccess: 'Data imported successfully',
      importFailed: 'Failed to import data',
      invalidFile: 'Please select a valid Excel file',
      fileTooLarge: 'File size cannot exceed 10MB'
    }
  },

  // Error messages
  messages: {
    // Common errors
    networkError: 'Network error, please check your connection',
    serverError: 'Server error, please try again later',
    unauthorized: 'Unauthorized access',
    forbidden: 'Access forbidden',
    notFound: 'Resource not found',
    validationError: 'Data validation failed',
    
    // Business errors
    testCaseNotFound: 'Test case not found',
    categoryNotFound: 'Category not found',
    executionNotFound: 'Execution record not found',
    batchExecutionNotFound: 'Batch execution task not found',
    configNotFound: 'Configuration not found',
    
    // Operation errors
    operationNotAllowed: 'Operation not allowed',
    dataInUse: 'Data is in use, cannot delete',
    duplicateData: 'Data already exists',
    invalidData: 'Invalid data format',
    
    // System errors
    systemBusy: 'System busy, please try again later',
    timeout: 'Request timeout',
    unknownError: 'Unknown error'
  },

  // Form validation
  validation: {
    required: 'This field is required',
    minLength: 'Length cannot be less than {min} characters',
    maxLength: 'Length cannot exceed {max} characters',
    min: 'Value cannot be less than {min}',
    max: 'Value cannot be greater than {max}',
    email: 'Please enter a valid email address',
    url: 'Please enter a valid URL',
    number: 'Please enter a valid number',
    integer: 'Please enter a valid integer',
    positive: 'Please enter a positive number',
    negative: 'Please enter a negative number',
    pattern: 'Invalid format',
    custom: 'Validation failed'
  },

  // Language switching
  language: {
    switch: 'Switch Language',
    chinese: '中文',
    english: 'English',
    current: 'Current Language'
  }
}
