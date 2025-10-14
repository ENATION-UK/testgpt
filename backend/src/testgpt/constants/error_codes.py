"""
错误码常量定义
"""

# 通用错误码
GENERAL_ERROR = "general_error"
NETWORK_ERROR = "network_error"
SERVER_ERROR = "server_error"
UNAUTHORIZED = "unauthorized"
FORBIDDEN = "forbidden"
NOT_FOUND = "not_found"
VALIDATION_ERROR = "validation_error"
OPERATION_NOT_ALLOWED = "operation_not_allowed"
DATA_IN_USE = "data_in_use"
DUPLICATE_DATA = "duplicate_data"
INVALID_DATA = "invalid_data"
SYSTEM_BUSY = "system_busy"
TIMEOUT = "timeout"
UNKNOWN_ERROR = "unknown_error"

# 测试用例相关错误码
TEST_CASE_NOT_FOUND = "test_case_not_found"
TEST_CASE_CREATE_FAILED = "test_case_create_failed"
TEST_CASE_UPDATE_FAILED = "test_case_update_failed"
TEST_CASE_DELETE_FAILED = "test_case_delete_failed"
TEST_CASE_LOAD_FAILED = "test_case_load_failed"
TEST_CASE_NAME_REQUIRED = "test_case_name_required"
TEST_CASE_NAME_LENGTH_INVALID = "test_case_name_length_invalid"
TEST_CASE_TASK_CONTENT_REQUIRED = "test_case_task_content_required"
TEST_CASE_TASK_CONTENT_LENGTH_INVALID = "test_case_task_content_length_invalid"
TEST_CASE_EXPECTED_RESULT_LENGTH_INVALID = "test_case_expected_result_length_invalid"
TEST_CASE_CATEGORY_REQUIRED = "test_case_category_required"
TEST_CASE_PRIORITY_REQUIRED = "test_case_priority_required"
TEST_CASE_STATUS_REQUIRED = "test_case_status_required"

# 分类相关错误码
CATEGORY_NOT_FOUND = "category_not_found"
CATEGORY_CREATE_FAILED = "category_create_failed"
CATEGORY_UPDATE_FAILED = "category_update_failed"
CATEGORY_DELETE_FAILED = "category_delete_failed"
CATEGORY_LOAD_FAILED = "category_load_failed"
CATEGORY_NAME_REQUIRED = "category_name_required"
CATEGORY_NAME_LENGTH_INVALID = "category_name_length_invalid"
CATEGORY_DESCRIPTION_LENGTH_INVALID = "category_description_length_invalid"
CATEGORY_HAS_CHILDREN = "category_has_children"
CATEGORY_HAS_TEST_CASES = "category_has_test_cases"

# 执行记录相关错误码
EXECUTION_NOT_FOUND = "execution_not_found"
EXECUTION_CREATE_FAILED = "execution_create_failed"
EXECUTION_UPDATE_FAILED = "execution_update_failed"
EXECUTION_DELETE_FAILED = "execution_delete_failed"
EXECUTION_LOAD_FAILED = "execution_load_failed"
EXECUTION_START_FAILED = "execution_start_failed"
EXECUTION_STOP_FAILED = "execution_stop_failed"

# 批量执行相关错误码
BATCH_EXECUTION_NOT_FOUND = "batch_execution_not_found"
BATCH_EXECUTION_CREATE_FAILED = "batch_execution_create_failed"
BATCH_EXECUTION_UPDATE_FAILED = "batch_execution_update_failed"
BATCH_EXECUTION_DELETE_FAILED = "batch_execution_delete_failed"
BATCH_EXECUTION_LOAD_FAILED = "batch_execution_load_failed"
BATCH_EXECUTION_START_FAILED = "batch_execution_start_failed"
BATCH_EXECUTION_STOP_FAILED = "batch_execution_stop_failed"

# 配置相关错误码
CONFIG_NOT_FOUND = "config_not_found"
CONFIG_SAVE_FAILED = "config_save_failed"
CONFIG_LOAD_FAILED = "config_load_failed"
CONFIG_TEST_FAILED = "config_test_failed"
CONFIG_INVALID = "config_invalid"
MULTI_MODEL_CONFIG_INVALID = "multi_model_config_invalid"
PROMPT_CONFIG_INVALID = "prompt_config_invalid"

# 统计相关错误码
STATISTICS_LOAD_FAILED = "statistics_load_failed"

# Excel导入相关错误码
EXCEL_IMPORT_FAILED = "excel_import_failed"
EXCEL_FILE_INVALID = "excel_file_invalid"
EXCEL_FILE_TOO_LARGE = "excel_file_too_large"
EXCEL_TEMPLATE_INVALID = "excel_template_invalid"
