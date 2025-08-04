"""
数据库配置和连接
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Float, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# 数据库连接配置
# MySQL配置
MYSQL_DATABASE_URL = "mysql+pymysql://root:12346@192.168.2.153:3306/autotest"

# SQLite配置（本地开发用）
SQLITE_DATABASE_URL = "sqlite:///./autotest.db"

# 根据环境选择数据库
USE_MYSQL = os.getenv("USE_MYSQL", "false").lower() == "true"
DATABASE_URL = MYSQL_DATABASE_URL if USE_MYSQL else SQLITE_DATABASE_URL

print(f"🔧 使用数据库: {'MySQL' if USE_MYSQL else 'SQLite'}")
print(f"🔧 数据库URL: {DATABASE_URL}")

# 创建数据库引擎
if USE_MYSQL:
    engine = create_engine(
        DATABASE_URL,
        echo=True,  # 显示SQL语句（开发环境）
        pool_pre_ping=True,  # 连接前ping一下确保连接有效
        pool_recycle=3600,  # 连接回收时间（秒）
    )
else:
    engine = create_engine(
        DATABASE_URL,
        echo=True,  # 显示SQL语句（开发环境）
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
    tags = Column(JSON, comment="标签列表")
    expected_result = Column(Text, comment="预期结果")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    is_deleted = Column(Boolean, default=False, comment="是否删除")
    
    # 关联关系
    executions = relationship("TestExecution", back_populates="test_case")

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
    started_at = Column(DateTime, default=datetime.utcnow, comment="开始时间")
    completed_at = Column(DateTime, comment="完成时间")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    
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
    started_at = Column(DateTime, default=datetime.utcnow, comment="开始时间")
    completed_at = Column(DateTime, comment="完成时间")
    
    # 关联关系
    execution = relationship("TestExecution", back_populates="steps")

# 批量执行任务模型
class BatchExecution(Base):
    __tablename__ = "batch_execution"
    
    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    name = Column(String(255), nullable=False, comment="批量执行任务名称")
    status = Column(String(50), default="running", comment="执行状态: running, completed, failed, cancelled")
    total_count = Column(Integer, default=0, comment="总测试用例数")
    success_count = Column(Integer, default=0, comment="成功执行数")
    failed_count = Column(Integer, default=0, comment="失败执行数")
    running_count = Column(Integer, default=0, comment="正在执行数")
    pending_count = Column(Integer, default=0, comment="待执行数")
    total_duration = Column(Float, default=0.0, comment="总执行时间(秒)")
    started_at = Column(DateTime, default=datetime.utcnow, comment="开始时间")
    completed_at = Column(DateTime, comment="完成时间")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
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
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
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
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    is_deleted = Column(Boolean, default=False, comment="是否删除")

# 测试套件用例关联模型
class TestSuiteCase(Base):
    __tablename__ = "test_suite_case"
    
    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    suite_id = Column(Integer, ForeignKey("test_suite.id"), nullable=False, comment="测试套件ID")
    test_case_id = Column(Integer, ForeignKey("test_case.id"), nullable=False, comment="测试用例ID")
    execution_order = Column(Integer, comment="执行顺序")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

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
        Base.metadata.create_all(bind=engine)
        print("✅ 数据库表创建成功！")
    except Exception as e:
        print(f"❌ 数据库表创建失败: {e}")

def init_db():
    """初始化数据库"""
    try:
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
打开 https://seller-bbc740.javamall.com.cn/
输入用户名superadmin
密码123456
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
# 商品查询测试
打开 https://seller-bbc740.javamall.com.cn/
登录系统
进入商品管理页面
搜索商品名称"测试商品"
验证搜索结果是否正确显示
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
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")

if __name__ == "__main__":
    # 测试数据库连接
    if test_connection():
        # 初始化数据库
        init_db()