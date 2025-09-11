"""
数据库配置和连接
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Float, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timezone, timedelta
import os
import pathlib
from .config_manager import ConfigManager

# 设置时区为北京时间
BEIJING_TZ = timezone(timedelta(hours=8))

def beijing_now():
    """获取北京时间"""
    return datetime.now(BEIJING_TZ)

# 数据库配置管理
class DatabaseConfig:
    """数据库配置管理器"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.db_dir = self._get_database_directory()
        self.db_name = os.getenv("DB_NAME", "autotest.db")
        self.db_path = self.db_dir / self.db_name
        
    def _get_database_directory(self) -> pathlib.Path:
        """获取数据库目录路径"""
        # 使用配置管理器的数据库路径
        return self.config_manager.get_database_path().parent
    
    def get_database_url(self) -> str:
        """获取数据库连接URL"""
        return f"sqlite:///{self.db_path}"
    
    def ensure_database_directory(self):
        """确保数据库目录存在并有正确权限"""
        self.db_dir.mkdir(parents=True, exist_ok=True)
        # 在Docker环境中，确保目录可写
        if os.getenv("DOCKER_ENV"):
            try:
                # 尝试设置目录权限为755
                self.db_dir.chmod(0o755)
            except Exception:
                pass  # 忽略权限设置错误

# 创建数据库配置实例
db_config = DatabaseConfig()

# MySQL配置
MYSQL_DATABASE_URL = "mysql+pymysql://root:12346@192.168.2.153:3306/autotest"

# 根据环境选择数据库
USE_MYSQL = os.getenv("USE_MYSQL", "false").lower() == "true"
DATABASE_URL = MYSQL_DATABASE_URL if USE_MYSQL else db_config.get_database_url()

# 控制SQL日志输出
ENABLE_SQL_ECHO = os.getenv("ENABLE_SQL_ECHO", "false").lower() == "true"

print(f"🔧 使用数据库: {'MySQL' if USE_MYSQL else 'SQLite'}")
print(f"🔧 数据库URL: {DATABASE_URL}")
print(f"🔧 数据库文件路径: {db_config.db_path}")
print(f"🔧 SQL日志: {'开启' if ENABLE_SQL_ECHO else '关闭'}")

# 确保数据库目录存在
db_config.ensure_database_directory()

# 创建数据库引擎
if USE_MYSQL:
    engine = create_engine(
        DATABASE_URL,
        echo=ENABLE_SQL_ECHO,  # 通过环境变量控制SQL语句显示
        pool_pre_ping=True,  # 连接前ping一下确保连接有效
        pool_recycle=3600,  # 连接回收时间（秒）
    )
else:
    engine = create_engine(
        DATABASE_URL,
        echo=ENABLE_SQL_ECHO,  # 通过环境变量控制SQL语句显示
        connect_args={"check_same_thread": False}  # SQLite需要这个参数
    )

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
Base = declarative_base()

# 测试用例模型
class TestCase(Base):
    __tablename__ = "test_case"
    
    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    name = Column(String(255), nullable=False, comment="测试用例名称")
    task_content = Column(Text, nullable=False, comment="测试任务内容")
    status = Column(String(50), default="active", comment="状态: active, inactive, draft")
    priority = Column(String(20), default="medium", comment="优先级: low, medium, high, critical")
    category = Column(String(100), comment="测试分类")
    category_id = Column(Integer, ForeignKey("category.id"), nullable=True, comment="分类ID")
    tags = Column(JSON, comment="标签列表")
    expected_result = Column(Text, comment="预期结果")
    history_path = Column(String(500), comment="历史记录文件路径")
    history_updated_at = Column(DateTime, comment="历史记录更新时间")
    created_at = Column(DateTime, default=beijing_now, comment="创建时间")
    updated_at = Column(DateTime, default=beijing_now, onupdate=beijing_now, comment="更新时间")
    is_deleted = Column(Boolean, default=False, comment="是否删除")
    
    # 关联关系
    executions = relationship("TestExecution", back_populates="test_case")
    category_obj = relationship("Category", back_populates="test_cases")

# 测试执行记录模型
class TestExecution(Base):
    __tablename__ = "test_execution"
    
    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    test_case_id = Column(Integer, ForeignKey("test_case.id"), nullable=False, comment="测试用例ID")
    execution_name = Column(String(255), comment="执行名称")
    status = Column(String(50), default="running", comment="执行状态: running, passed, failed, error, cancelled")
    overall_status = Column(String(50), comment="整体状态: PASSED, FAILED, PARTIAL")
    total_steps = Column(Integer, default=0, comment="总步骤数")
    passed_steps = Column(Integer, default=0, comment="通过的步骤数")
    failed_steps = Column(Integer, default=0, comment="失败的步骤数")
    skipped_steps = Column(Integer, default=0, comment="跳过的步骤数")
    total_duration = Column(Float, comment="总执行时间(秒)")
    summary = Column(Text, comment="测试总结")
    recommendations = Column(Text, comment="改进建议")
    error_message = Column(Text, comment="错误信息")
    browser_logs = Column(JSON, comment="浏览器日志")
    screenshots = Column(JSON, comment="截图路径列表")
    started_at = Column(DateTime, default=beijing_now, comment="开始时间")
    completed_at = Column(DateTime, comment="完成时间")
    created_at = Column(DateTime, default=beijing_now, comment="创建时间")
    
    # 关联关系
    test_case = relationship("TestCase", back_populates="executions")
    steps = relationship("TestStep", back_populates="execution")

# 测试步骤模型
class TestStep(Base):
    __tablename__ = "test_step"
    
    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    execution_id = Column(Integer, ForeignKey("test_execution.id"), nullable=False, comment="执行记录ID")
    step_name = Column(String(255), nullable=False, comment="步骤名称")
    step_order = Column(Integer, comment="步骤顺序")
    status = Column(String(50), comment="步骤状态: PASSED, FAILED, SKIPPED, RUNNING")
    description = Column(Text, comment="步骤描述")
    error_message = Column(Text, comment="错误信息")
    screenshot_path = Column(Text, comment="截图路径")
    duration_seconds = Column(Float, comment="执行时间(秒)")
    started_at = Column(DateTime, default=beijing_now, comment="开始时间")
    completed_at = Column(DateTime, comment="完成时间")
    
    # 新增字段：Browser-Use事件详细信息
    url = Column(String(2000), comment="步骤执行时的页面URL")
    actions = Column(JSON, comment="执行的动作列表")
    evaluation = Column(Text, comment="前一目标的评估结果")
    memory = Column(Text, comment="Agent记忆信息")
    next_goal = Column(Text, comment="下一个目标")
    screenshot_data = Column(Text, comment="截图数据或路径")
    event_timestamp = Column(DateTime, comment="事件发生时间")
    step_metadata = Column(JSON, comment="步骤元数据")
    
    # 关联关系
    execution = relationship("TestExecution", back_populates="steps")

# 分类模型 - 支持多级无限级分类
class Category(Base):
    __tablename__ = "category"
    
    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    name = Column(String(100), nullable=False, comment="分类名称")
    description = Column(Text, comment="分类描述")
    parent_id = Column(Integer, ForeignKey("category.id"), nullable=True, comment="父分类ID")
    level = Column(Integer, default=0, comment="分类层级")
    sort_order = Column(Integer, default=0, comment="排序顺序")
    is_active = Column(Boolean, default=True, comment="是否激活")
    created_at = Column(DateTime, default=beijing_now, comment="创建时间")
    updated_at = Column(DateTime, default=beijing_now, onupdate=beijing_now, comment="更新时间")
    is_deleted = Column(Boolean, default=False, comment="是否删除")
    
    # 关联关系
    parent = relationship("Category", remote_side=[id], backref="children")
    test_cases = relationship("TestCase", back_populates="category_obj")

# 批量执行任务模型
class BatchExecution(Base):
    __tablename__ = "batch_execution"
    
    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    name = Column(String(255), nullable=False, comment="批量执行任务名称")
    status = Column(String(50), default="running", comment="执行状态: pending, running, completed, failed, cancelled")
    total_count = Column(Integer, default=0, comment="总测试用例数")
    success_count = Column(Integer, default=0, comment="成功执行数")
    failed_count = Column(Integer, default=0, comment="失败执行数")
    running_count = Column(Integer, default=0, comment="正在执行数")
    pending_count = Column(Integer, default=0, comment="待执行数")
    total_duration = Column(Float, default=0.0, comment="总执行时间(秒)")
    headless = Column(Boolean, default=True, comment="是否无头模式")
    started_at = Column(DateTime, default=beijing_now, comment="开始时间")
    completed_at = Column(DateTime, comment="完成时间")
    created_at = Column(DateTime, default=beijing_now, comment="创建时间")
    updated_at = Column(DateTime, default=beijing_now, onupdate=beijing_now, comment="更新时间")
    
    # 关联关系
    test_cases = relationship("BatchExecutionTestCase", back_populates="batch_execution")

# Excel导入任务模型
class ImportTask(Base):
    __tablename__ = "import_task"
    
    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    name = Column(String(255), nullable=False, comment="导入任务名称")
    file_name = Column(String(255), nullable=False, comment="Excel文件名")
    file_path = Column(String(500), comment="文件存储路径")
    import_mode = Column(String(20), default="smart", comment="导入模式: standard(标准模版) 或 smart(智能识别)")
    status = Column(String(50), default="pending", comment="任务状态: pending, running, completed, failed, cancelled")
    total_rows = Column(Integer, default=0, comment="总行数")
    processed_rows = Column(Integer, default=0, comment="已处理行数")
    success_rows = Column(Integer, default=0, comment="成功导入行数")
    failed_rows = Column(Integer, default=0, comment="失败行数")
    current_batch = Column(Integer, default=0, comment="当前批次")
    total_batches = Column(Integer, default=0, comment="总批次数")
    batch_size = Column(Integer, default=10, comment="批次大小")
    progress_percentage = Column(Float, default=0.0, comment="进度百分比")
    import_options = Column(JSON, comment="导入选项")
    error_log = Column(JSON, comment="错误日志")
    result_summary = Column(JSON, comment="导入结果摘要")
    started_at = Column(DateTime, comment="开始时间")
    completed_at = Column(DateTime, comment="完成时间")
    created_at = Column(DateTime, default=beijing_now, comment="创建时间")
    updated_at = Column(DateTime, default=beijing_now, onupdate=beijing_now, comment="更新时间")

# 批量执行任务中的测试用例模型
class BatchExecutionTestCase(Base):
    __tablename__ = "batch_execution_test_case"
    
    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    batch_execution_id = Column(Integer, ForeignKey("batch_execution.id"), nullable=False, comment="批量执行任务ID")
    test_case_id = Column(Integer, ForeignKey("test_case.id"), nullable=False, comment="测试用例ID")
    execution_id = Column(Integer, ForeignKey("test_execution.id"), nullable=True, comment="执行记录ID")
    status = Column(String(50), default="pending", comment="执行状态: pending, running, completed, failed")
    started_at = Column(DateTime, comment="开始时间")
    completed_at = Column(DateTime, comment="完成时间")
    created_at = Column(DateTime, default=beijing_now, comment="创建时间")
    updated_at = Column(DateTime, default=beijing_now, onupdate=beijing_now, comment="更新时间")
    
    # 关联关系
    batch_execution = relationship("BatchExecution", back_populates="test_cases")
    test_case = relationship("TestCase")
    execution = relationship("TestExecution")

# 测试套件模型
class TestSuite(Base):
    __tablename__ = "test_suite"
    
    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    name = Column(String(255), nullable=False, comment="测试套件名称")
    description = Column(Text, comment="测试套件描述")
    status = Column(String(50), default="active", comment="状态")
    created_at = Column(DateTime, default=beijing_now, comment="创建时间")
    updated_at = Column(DateTime, default=beijing_now, onupdate=beijing_now, comment="更新时间")
    is_deleted = Column(Boolean, default=False, comment="是否删除")

# 测试套件用例关联模型
class TestSuiteCase(Base):
    __tablename__ = "test_suite_case"
    
    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    suite_id = Column(Integer, ForeignKey("test_suite.id"), nullable=False, comment="测试套件ID")
    test_case_id = Column(Integer, ForeignKey("test_case.id"), nullable=False, comment="测试用例ID")
    execution_order = Column(Integer, comment="执行顺序")
    created_at = Column(DateTime, default=beijing_now, comment="创建时间")

def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_connection():
    """测试数据库连接"""
    try:
        with engine.connect() as connection:
            from sqlalchemy import text
            result = connection.execute(text("SELECT 1"))
            print("✅ 数据库连接成功！")
            return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False

def create_tables():
    """创建数据库表"""
    try:
        # 确保数据库目录存在
        db_config.ensure_database_directory()
        
        # 检查数据库文件是否存在
        if not db_config.db_path.exists():
            print(f"📁 创建新的数据库文件: {db_config.db_path}")
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        print("✅ 数据库表创建成功！")
        
        # 验证表是否真的创建了
        with engine.connect() as connection:
            from sqlalchemy import text, inspect
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            print(f"📋 已创建的表: {', '.join(tables)}")
            
    except Exception as e:
        print(f"❌ 数据库表创建失败: {e}")
        print(f"🔍 数据库路径: {db_config.db_path}")
        print(f"🔍 数据库目录权限: {oct(db_config.db_dir.stat().st_mode)[-3:] if db_config.db_dir.exists() else '目录不存在'}")
        raise

def check_tables_exist():
    """检查数据库表是否存在"""
    try:
        with engine.connect() as connection:
            from sqlalchemy import text, inspect
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            required_tables = ['test_case', 'test_execution', 'test_step', 'category', 'batch_execution', 'test_suite', 'test_suite_case', 'import_task']
            
            missing_tables = [table for table in required_tables if table not in tables]
            
            if missing_tables:
                print(f"⚠️  缺少以下表: {', '.join(missing_tables)}")
                return False
            else:
                print(f"✅ 所有必需的表都存在: {', '.join(tables)}")
                return True
    except Exception as e:
        print(f"❌ 检查表存在性失败: {e}")
        return False

def init_db():
    """初始化数据库"""
    try:
        print(f"🚀 开始初始化数据库: {db_config.db_path}")
        
        # 检查表是否已存在
        if check_tables_exist():
            print("✅ 数据库表已存在，跳过创建")
        else:
            # 创建表
            create_tables()
        
        # 插入一些测试数据
        db = SessionLocal()
        
        # 检查是否已有数据
        existing_count = db.query(TestCase).count()
        if existing_count == 0:
            # 插入测试数据
            test_cases = [
                # 1. 首页功能测试
                TestCase(
                    name="首页统计信息展示测试",
                    task_content="""
# 操作步骤
1.打开：http://localhost:3000
2.验证首页统计卡片是否正确显示：
   - 测试用例总数
   - 执行次数
   - 成功率
   - 平均耗时
3.验证快速操作按钮是否可点击：
   - 管理测试用例
   - 查看执行记录
   - 查看统计信息
4.验证最近执行记录区域是否正常显示
                    """,
                    status="active",
                    priority="high",
                    category="首页功能",
                    tags=["home", "statistics", "dashboard"],
                    expected_result="""
                    首页功能正常：
                    - 统计卡片正确显示数据
                    - 快速操作按钮可正常跳转
                    - 最近执行记录区域正常显示（如果有数据）
                    """
                ),
                
                # 2. 测试用例管理功能测试
                TestCase(
                    name="测试用例创建和编辑测试",
                    task_content="""
# 操作步骤
1.打开：http://localhost:3000/test-cases
2.点击`创建测试用例`按钮
3.填写测试用例信息：
   - 名称：测试用例管理功能验证
   - 操作步骤：验证测试用例的增删改查功能
   - 预期结果：能够正常创建、编辑、删除测试用例
   - 优先级：高
   - 分类：测试管理
   - 标签：management, crud
4.点击创建按钮
5.验证用例是否出现在列表中
6.点击编辑按钮，修改用例信息
7.点击查看按钮，验证用例详情
8.点击删除按钮，确认删除
                    """,
                    status="active",
                    priority="high",
                    category="测试管理",
                    tags=["test-case", "crud", "management"],
                    expected_result="""
                    测试用例管理功能正常：
                    - 能够成功创建测试用例
                    - 用例列表正确显示新创建的用例
                    - 编辑功能正常工作
                    - 查看功能正常显示详情
                    - 删除功能正常工作
                    """
                ),
                
                # 3. 分类管理功能测试
                TestCase(
                    name="分类管理功能测试",
                    task_content="""
# 操作步骤
1.打开：http://localhost:3000/categories
2.点击`创建分类`按钮
3.填写分类信息：
   - 分类名称：功能测试
   - 描述：用于功能测试的分类
4.点击创建按钮
5.验证分类是否出现在树形结构中
6.点击`添加子分类`按钮，创建子分类：
   - 子分类名称：UI测试
   - 描述：用户界面测试
7.验证子分类是否正确显示在父分类下
8.点击编辑按钮，修改分类信息
9.点击删除按钮，删除测试分类
                    """,
                    status="active",
                    priority="medium",
                    category="分类管理",
                    tags=["category", "tree", "management"],
                    expected_result="""
                    分类管理功能正常：
                    - 能够成功创建分类
                    - 分类树形结构正确显示
                    - 子分类创建功能正常
                    - 编辑功能正常工作
                    - 删除功能正常工作
                    """
                ),
                
                # 4. Excel导入功能测试
                TestCase(
                    name="Excel批量导入功能测试",
                    task_content="""
# 操作步骤
1.打开：http://localhost:3000/excel-import
2.选择导入模式：
   - 智能识别模式：支持各种格式的Excel文件
   - 标准模版模式：使用统一的标准模版格式
3.如果选择标准模版模式，点击`下载标准模版`按钮
4.点击`选择文件`按钮，选择一个Excel文件
5.填写导入选项：
   - 任务名称：Excel导入测试
   - 批次大小：10
   - 默认状态：active
   - 默认优先级：medium
   - 默认分类：导入测试
6.点击`开始导入`按钮
7.观察导入进度和状态
8.验证导入结果是否正确
                    """,
                    status="active",
                    priority="medium",
                    category="数据导入",
                    tags=["excel", "import", "batch"],
                    expected_result="""
                    Excel导入功能正常：
                    - 能够正确识别Excel文件格式
                    - 导入进度正确显示
                    - 导入结果准确
                    - 错误处理机制正常
                    """
                ),
                
                # 5. 执行记录功能测试
                TestCase(
                    name="执行记录查看和管理测试",
                    task_content="""
# 操作步骤
1.打开：http://localhost:3000/executions
2.验证执行记录列表是否正确显示：
   - 执行名称
   - 测试用例名称
   - 执行状态
   - 开始时间
   - 执行时长
3.点击某个执行记录，查看详细信息
4.验证执行详情页面是否包含：
   - 执行状态和结果
   - 执行步骤详情
   - 错误信息（如果有）
   - 截图信息（如果有）
5.测试筛选功能：
   - 按状态筛选
   - 按时间范围筛选
   - 按测试用例筛选
                    """,
                    status="active",
                    priority="medium",
                    category="执行管理",
                    tags=["execution", "history", "monitoring"],
                    expected_result="""
                    执行记录功能正常：
                    - 执行记录列表正确显示
                    - 执行详情页面信息完整
                    - 筛选功能正常工作
                    - 状态和结果信息准确
                    """
                ),
                
                # 6. 批量执行功能测试
                TestCase(
                    name="批量执行功能测试",
                    task_content="""
# 操作步骤
1.打开：http://localhost:3000/test-cases
2.选择多个测试用例（至少2个）
3.点击`批量执行`按钮
4.填写批量执行配置：
   - 执行名称：批量执行测试
   - 执行模式：无头模式
5.点击`开始执行`按钮
6.跳转到批量执行详情页面
7.观察批量执行进度：
   - 总用例数
   - 成功执行数
   - 失败执行数
   - 正在执行数
   - 待执行数
8.验证每个用例的执行状态和结果
                    """,
                    status="active",
                    priority="high",
                    category="批量执行",
                    tags=["batch", "execution", "parallel"],
                    expected_result="""
                    批量执行功能正常：
                    - 能够正确选择多个测试用例
                    - 批量执行配置正确
                    - 执行进度实时更新
                    - 各用例执行状态准确
                    - 执行结果正确汇总
                    """
                ),
                
                # 7. 统计信息功能测试
                TestCase(
                    name="统计信息页面测试",
                    task_content="""
# 操作步骤
1.打开：http://localhost:3000/statistics
2.验证统计概览卡片：
   - 测试用例总数
   - 执行总次数
   - 成功率
   - 平均耗时
3.验证分类统计图表：
   - 各分类的用例数量
   - 各分类的执行情况
4.验证优先级统计图表：
   - 各优先级的用例分布
   - 各优先级的执行情况
5.验证趋势分析图表：
   - 执行趋势图
   - 成功率趋势图
6.验证时间范围筛选功能
                    """,
                    status="active",
                    priority="medium",
                    category="统计分析",
                    tags=["statistics", "charts", "analytics"],
                    expected_result="""
                    统计信息功能正常：
                    - 统计概览数据准确
                    - 分类统计图表正确显示
                    - 优先级统计图表正确显示
                    - 趋势分析图表正确显示
                    - 时间筛选功能正常工作
                    """
                ),
                
                # 8. 模型设置功能测试
                TestCase(
                    name="多模型配置功能测试",
                    task_content="""
# 操作步骤
1.打开：http://localhost:3000/multi-model-settings
2.验证模型提供商配置区域：
   - 提供商名称
   - API密钥配置
   - 模型选择
   - 启用/禁用开关
3.点击`添加提供商`按钮，添加新的模型提供商
4.填写提供商信息：
   - 提供商名称：测试提供商
   - API密钥：test-key
   - 选择模型：gpt-3.5-turbo
   - 启用该提供商
5.点击`测试配置`按钮，验证配置是否正确
6.点击`保存配置`按钮
7.验证配置是否成功保存
8.测试删除提供商功能
                    """,
                    status="active",
                    priority="medium",
                    category="系统配置",
                    tags=["model", "config", "api"],
                    expected_result="""
                    多模型配置功能正常：
                    - 能够正确添加模型提供商
                    - 配置测试功能正常
                    - 配置保存功能正常
                    - 提供商管理功能正常
                    """
                ),
                
                # 9. 提示词设置功能测试
                TestCase(
                    name="提示词设置功能测试",
                    task_content="""
# 操作步骤
1.打开：http://localhost:3000/prompt-settings
2.验证提示词配置区域：
   - 系统提示词
   - 用户提示词模板
   - 错误处理提示词
3.修改系统提示词内容
4.修改用户提示词模板
5.点击`保存设置`按钮
6.验证设置是否成功保存
7.点击`重置为默认`按钮
8.验证是否恢复到默认设置
9.测试提示词预览功能
                    """,
                    status="active",
                    priority="low",
                    category="系统配置",
                    tags=["prompt", "template", "config"],
                    expected_result="""
                    提示词设置功能正常：
                    - 能够正确修改提示词内容
                    - 设置保存功能正常
                    - 重置功能正常工作
                    - 预览功能正常显示
                    """
                ),
                
                # 10. 导航和页面跳转测试
                TestCase(
                    name="页面导航和跳转测试",
                    task_content="""
# 操作步骤
1.打开：http://localhost:3000
2.测试顶部导航栏的所有链接：
   - 首页
   - 测试用例
   - 分类管理
   - Excel导入
   - 执行记录
   - 批量执行
   - 统计信息
   - 模型设置
   - 提示词设置
3.验证每个页面是否正确加载
4.验证页面标题和内容是否正确
5.测试浏览器前进后退功能
6.测试页面刷新功能
7.验证响应式布局在不同屏幕尺寸下的表现
                    """,
                    status="active",
                    priority="low",
                    category="界面测试",
                    tags=["navigation", "ui", "responsive"],
                    expected_result="""
                    页面导航功能正常：
                    - 所有导航链接正确跳转
                    - 页面内容正确加载
                    - 浏览器导航功能正常
                    - 响应式布局正常
                    """
                )
            ]
            
            for case in test_cases:
                db.add(case)
            
            # 插入一些分类数据
            categories = [
                Category(
                    name="首页功能",
                    description="首页相关功能测试",
                    level=0,
                    sort_order=1,
                    is_active=True
                ),
                Category(
                    name="测试管理",
                    description="测试用例管理功能",
                    level=0,
                    sort_order=2,
                    is_active=True
                ),
                Category(
                    name="分类管理",
                    description="分类管理功能测试",
                    level=0,
                    sort_order=3,
                    is_active=True
                ),
                Category(
                    name="数据导入",
                    description="Excel导入功能测试",
                    level=0,
                    sort_order=4,
                    is_active=True
                ),
                Category(
                    name="执行管理",
                    description="测试执行相关功能",
                    level=0,
                    sort_order=5,
                    is_active=True
                ),
                Category(
                    name="批量执行",
                    description="批量执行功能测试",
                    level=0,
                    sort_order=6,
                    is_active=True
                ),
                Category(
                    name="统计分析",
                    description="统计信息功能测试",
                    level=0,
                    sort_order=7,
                    is_active=True
                ),
                Category(
                    name="系统配置",
                    description="系统配置相关功能",
                    level=0,
                    sort_order=8,
                    is_active=True
                ),
                Category(
                    name="界面测试",
                    description="用户界面相关测试",
                    level=0,
                    sort_order=9,
                    is_active=True
                )
            ]
            
            for category in categories:
                db.add(category)
            
            db.commit()
            print(f"✅ 成功插入 {len(test_cases)} 条测试数据和 {len(categories)} 条分类数据")
        else:
            print(f"✅ 数据库中已有 {existing_count} 条记录")
        
        db.close()
        print("✅ 数据库初始化完成！")
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        print(f"🔍 请检查数据库路径和权限: {db_config.db_path}")
        raise

if __name__ == "__main__":
    # 测试数据库连接
    if test_connection():
        # 初始化数据库
        init_db()