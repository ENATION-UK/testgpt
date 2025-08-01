# Tests Directory

This directory contains all test files for the autotest project.

## Test Files

- `test_api.py` - API接口测试
- `test_api_with_db.py` - 带数据库的API测试
- `test_all_features.py` - 全功能测试
- `test_browser_use.py` - 浏览器使用测试
- `test_database.py` - 数据库测试
- `test_execution.py` - 执行测试
- `test_model_config.py` - 模型配置测试
- `test_mysql_connection.py` - MySQL连接测试
- `test_prompt_settings.py` - 提示设置测试
- `test_setup.py` - 设置测试

## Running Tests

To run all tests:
```bash
python -m pytest tests/
```

To run a specific test:
```bash
python -m pytest tests/test_api.py
``` 