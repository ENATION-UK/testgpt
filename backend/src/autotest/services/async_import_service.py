"""
异步Excel导入服务
支持分批处理大文件，提供实时进度反馈
"""

import asyncio
import json
import math
import os
import pandas as pd
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
from fastapi import UploadFile, HTTPException

from ..database import get_db, ImportTask, TestCase, Category
from ..models import ImportTaskCreate, ImportTaskResponse, ImportTaskStatus
from ..websocket_manager import websocket_manager
from .llm_service import LLMService
from .excel_utils import convert_excel_to_test_cases
from .excel_template_service import ExcelTemplateService


class AsyncImportService:
    """异步导入服务"""
    
    def __init__(self):
        self.running_tasks: Dict[int, bool] = {}  # 记录正在运行的任务
        
    async def create_import_task(
        self, 
        file: UploadFile, 
        task_data: ImportTaskCreate,
        db: Session
    ) -> ImportTaskResponse:
        """创建导入任务"""
        
        # 检查是否有正在运行的任务
        if await self.has_running_task(db):
            raise HTTPException(
                status_code=400, 
                detail="已有导入任务正在进行中，请等待完成后再试"
            )
        
        # 验证文件格式
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="只支持Excel文件格式")
        
        try:
            # 保存上传的文件到临时目录
            file_path = await self._save_uploaded_file(file)
            
            # 读取Excel文件获取总行数
            df = pd.read_excel(file_path)
            total_rows = len(df)
            total_batches = math.ceil(total_rows / task_data.batch_size)
            
            # 创建任务记录
            import_task = ImportTask(
                name=task_data.name,
                file_name=task_data.file_name,
                file_path=str(file_path),
                import_mode=task_data.import_mode,
                status="pending",
                total_rows=total_rows,
                total_batches=total_batches,
                batch_size=task_data.batch_size,
                import_options=task_data.import_options,
                error_log=[],
                result_summary={}
            )
            
            db.add(import_task)
            db.commit()
            db.refresh(import_task)
            
            # 启动异步处理任务
            asyncio.create_task(self._process_import_task(import_task.id))
            
            return ImportTaskResponse.from_orm(import_task)
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"创建导入任务失败: {str(e)}")
    
    async def _save_uploaded_file(self, file: UploadFile) -> Path:
        """保存上传的文件到临时目录"""
        # 创建临时目录
        temp_dir = Path(tempfile.gettempdir()) / "autotest_imports"
        temp_dir.mkdir(exist_ok=True)
        
        # 生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = temp_dir / f"{timestamp}_{file.filename}"
        
        # 保存文件
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return file_path
    
    async def _process_import_task(self, task_id: int):
        """处理导入任务的主要逻辑"""
        db_gen = get_db()
        db = next(db_gen)
        task = None
        
        try:
            # 标记任务为运行状态
            self.running_tasks[task_id] = True
            
            # 获取任务信息
            task = db.query(ImportTask).filter(ImportTask.id == task_id).first()
            if not task:
                return
            
            # 更新任务状态
            task.status = "running"
            task.started_at = datetime.now()
            db.commit()
            
            # 发送开始通知
            await self._send_progress_update(task_id, "running", 0, 0, 0, 0, 0, 0, 0)
            
            # 读取Excel文件
            df = pd.read_excel(task.file_path)
            df = df.fillna('')
            
            # 分批处理
            total_rows = len(df)
            batch_size = task.batch_size
            total_batches = math.ceil(total_rows / batch_size)
            
            success_count = 0
            failed_count = 0
            error_log = []
            
            for batch_num in range(total_batches):
                # 检查是否需要取消任务
                if not self.running_tasks.get(task_id, False):
                    task.status = "cancelled"
                    break
                
                start_idx = batch_num * batch_size
                end_idx = min((batch_num + 1) * batch_size, total_rows)
                batch_df = df.iloc[start_idx:end_idx]
                
                # 处理当前批次
                batch_success, batch_failed, batch_errors = await self._process_batch(
                    batch_df, task.import_options, task.import_mode, db
                )
                
                success_count += batch_success
                failed_count += batch_failed
                error_log.extend(batch_errors)
                
                # 更新任务进度
                processed_rows = end_idx
                progress = (processed_rows / total_rows) * 100
                
                task.current_batch = batch_num + 1
                task.processed_rows = processed_rows
                task.success_rows = success_count
                task.failed_rows = failed_count
                task.progress_percentage = progress
                task.error_log = error_log
                
                db.commit()
                
                # 发送进度更新
                await self._send_progress_update(
                    task_id, "running", progress, batch_num + 1, total_batches,
                    processed_rows, total_rows, success_count, failed_count
                )
                
                # 短暂延迟，避免过快处理
                await asyncio.sleep(0.1)
            
            # 完成任务
            if task.status != "cancelled":
                task.status = "completed"
                task.completed_at = datetime.now()
                task.result_summary = {
                    "total_rows": total_rows,
                    "success_rows": success_count,
                    "failed_rows": failed_count,
                    "success_rate": (success_count / total_rows * 100) if total_rows > 0 else 0
                }
                
                # 发送完成通知
                await self._send_progress_update(
                    task_id, "completed", 100, total_batches, total_batches,
                    total_rows, total_rows, success_count, failed_count
                )
            
            db.commit()
            
        except Exception as e:
            # 处理异常
            if task:
                task.status = "failed"
                task.completed_at = datetime.now()
                task.error_log = task.error_log or []
                task.error_log.append({
                    "type": "system_error",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat()
                })
                db.commit()
                
                # 发送错误通知
                await self._send_progress_update(
                    task_id, "failed", task.progress_percentage or 0,
                    task.current_batch or 0, task.total_batches or 0,
                    task.processed_rows or 0, task.total_rows or 0,
                    task.success_rows or 0, task.failed_rows or 0
                )
            
        finally:
            # 清理任务状态
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
            
            # 清理临时文件
            try:
                if task and task.file_path and os.path.exists(task.file_path):
                    os.remove(task.file_path)
            except:
                pass
            
            db.close()
    
    async def _process_batch(
        self, 
        batch_df: pd.DataFrame, 
        import_options: dict,
        import_mode: str,
        db: Session
    ) -> tuple[int, int, List[dict]]:
        """处理单个批次的数据"""
        success_count = 0
        failed_count = 0
        error_log = []
        
        try:
            # 根据导入模式选择不同的解析方式
            if import_mode == "standard":
                # 标准模版解析
                test_cases = ExcelTemplateService.parse_standard_template(batch_df)
            else:
                # 智能识别解析（使用LLM服务或规则转换）
                test_cases = await LLMService.analyze_excel_with_llm(batch_df, import_options)
            
            # 逐行创建测试用例
            for i, test_case_data in enumerate(test_cases):
                try:
                    # 验证必需字段
                    if not test_case_data.get('name') or not test_case_data.get('task_content'):
                        failed_count += 1
                        error_log.append({
                            "row": i + 1,
                            "type": "validation_error",
                            "message": "缺少必需字段：name 或 task_content",
                            "timestamp": datetime.now().isoformat()
                        })
                        continue
                    
                    # 处理分类：优先使用用户选择的分类
                    selected_category_id = import_options.get('selectedCategoryId')
                    if selected_category_id:
                        # 验证分类是否存在
                        category = db.query(Category).filter(
                            Category.id == selected_category_id,
                            Category.is_deleted == False
                        ).first()
                        if category:
                            test_case_data['category_id'] = selected_category_id
                            test_case_data['category'] = category.name
                        else:
                            # 如果选择的分类不存在，使用默认分类
                            test_case_data['category'] = import_options.get('defaultCategory', '导入')
                    else:
                        # 没有选择分类，使用默认分类
                        test_case_data['category'] = import_options.get('defaultCategory', '导入')
                    
                    # 创建测试用例
                    db_test_case = TestCase(**test_case_data)
                    db.add(db_test_case)
                    db.flush()  # 不立即提交，等批次结束再提交
                    success_count += 1
                    
                except Exception as e:
                    failed_count += 1
                    error_log.append({
                        "row": i + 1,
                        "type": "creation_error",
                        "message": str(e),
                        "data": test_case_data,
                        "timestamp": datetime.now().isoformat()
                    })
            
            # 提交当前批次
            db.commit()
            
        except Exception as e:
            # 整个批次失败
            db.rollback()
            failed_count = len(batch_df)
            error_log.append({
                "type": "batch_error",
                "message": f"批次处理失败: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })
        
        return success_count, failed_count, error_log
    
    async def _send_progress_update(
        self, 
        task_id: int, 
        status: str, 
        progress: float,
        current_batch: int, 
        total_batches: int,
        processed_rows: int, 
        total_rows: int,
        success_rows: int, 
        failed_rows: int
    ):
        """发送进度更新通知"""
        try:
            update_data = {
                "type": "import_progress",
                "task_id": task_id,
                "status": status,
                "progress_percentage": round(progress, 2),
                "current_batch": current_batch,
                "total_batches": total_batches,
                "processed_rows": processed_rows,
                "total_rows": total_rows,
                "success_rows": success_rows,
                "failed_rows": failed_rows,
                "timestamp": datetime.now().isoformat()
            }
            
            await websocket_manager.broadcast(json.dumps(update_data))
        except Exception as e:
            print(f"发送进度更新失败: {e}")
    
    async def get_task_status(self, task_id: int, db: Session) -> ImportTaskStatus:
        """获取任务状态"""
        task = db.query(ImportTask).filter(ImportTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        error_messages = []
        if task.error_log:
            error_messages = [error.get("message", "") for error in task.error_log[-5:]]  # 最近5个错误
        
        return ImportTaskStatus(
            task_id=task.id,
            status=task.status,
            progress_percentage=task.progress_percentage,
            current_batch=task.current_batch,
            total_batches=task.total_batches,
            processed_rows=task.processed_rows,
            total_rows=task.total_rows,
            success_rows=task.success_rows,
            failed_rows=task.failed_rows,
            error_messages=error_messages
        )
    
    async def cancel_task(self, task_id: int, db: Session) -> bool:
        """取消任务"""
        task = db.query(ImportTask).filter(ImportTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        if task.status not in ["pending", "running"]:
            raise HTTPException(status_code=400, detail="任务无法取消")
        
        # 标记任务为取消状态
        self.running_tasks[task_id] = False
        task.status = "cancelled"
        task.completed_at = datetime.now()
        db.commit()
        
        return True
    
    async def has_running_task(self, db: Session) -> bool:
        """检查是否有正在运行的任务"""
        running_task = db.query(ImportTask).filter(
            ImportTask.status.in_(["pending", "running"])
        ).first()
        return running_task is not None
    
    async def list_tasks(self, db: Session, limit: int = 10) -> List[ImportTaskResponse]:
        """获取任务列表"""
        tasks = db.query(ImportTask).order_by(ImportTask.created_at.desc()).limit(limit).all()
        return [ImportTaskResponse.from_orm(task) for task in tasks]