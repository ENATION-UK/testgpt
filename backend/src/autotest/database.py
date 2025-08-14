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
    description = Column(Text, comment="测试用例描述")
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
    status = Column(String(50), comment="步骤状态: PASSED, FAILED, SKIPPED")
    description = Column(Text, comment="步骤描述")
    error_message = Column(Text, comment="错误信息")
    screenshot_path = Column(String(500), comment="截图路径")
    duration_seconds = Column(Float, comment="执行时间(秒)")
    started_at = Column(DateTime, default=beijing_now, comment="开始时间")
    completed_at = Column(DateTime, comment="完成时间")
    
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
            required_tables = ['test_case', 'test_execution', 'test_step', 'category', 'batch_execution', 'test_suite', 'test_suite_case']
            
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
                TestCase(
                    name="用户登录测试",
                    description="测试用户登录功能是否正常",
                    task_content="""

# 登录测试
打开 https://admin-bbc740.javamall.com.cn/
输入用户名superadmin
密码111111
验证码1111

# 验证条件
是否正常进入控制台
                    
                    """,
                    status="active",
                    priority="high",
                    category="登录功能",
                    tags=["login", "authentication"],
                    expected_result="成功登录并进入控制台页面"
                ),
                TestCase(
                    name="商品查询测试",
                    description="测试商品查询功能",
                    task_content="""
# 操作步骤
1.打开：https://buyer-bbc740.javamall.com.cn/login
2.点击`账号登录`
3.输入：
用户名: food
密码: 111111
验证码: 1111
4.点击登录按钮
# 验证方法
登录成功后会跳到首页
首页的导航条部分会有`我的账户`字样
                    """,
                    status="active",
                    priority="medium",
                    category="商品管理",
                    tags=["product", "search"],
                    expected_result="能够正确搜索并显示商品信息"
                ),
                TestCase(
                    name="订单创建测试",
                    description="测试订单创建功能",
                    task_content="""
# 订单创建测试
打开 https://seller-bbc740.javamall.com.cn/
登录系统
进入订单管理页面
创建新订单
填写订单信息
提交订单
验证订单是否创建成功
                    """,
                    status="inactive",
                    priority="medium",
                    category="订单管理",
                    tags=["order", "create"],
                    expected_result="订单创建成功并显示在订单列表中"
                )
            ]
            
            for case in test_cases:
                db.add(case)
            
            db.commit()
            print(f"✅ 成功插入 {len(test_cases)} 条测试数据")
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