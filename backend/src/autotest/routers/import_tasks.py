"""
导入任务管理路由
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import os

from ..database import get_db
from ..models import (
    ImportTaskCreate, 
    ImportTaskResponse, 
    ImportTaskStatus,
    ImportTaskListResponse
)
from ..services.async_import_service import AsyncImportService
from ..services.excel_template_service import ExcelTemplateService

router = APIRouter(prefix="/import-tasks", tags=["导入任务管理"])

# 创建服务实例
async_import_service = AsyncImportService()

@router.post("/", response_model=ImportTaskResponse)
async def create_import_task(
    file: UploadFile = File(...),
    name: str = Form(...),
    import_mode: str = Form("smart"),
    import_options: str = Form(...),
    batch_size: int = Form(10),
    db: Session = Depends(get_db)
):
    """创建导入任务"""
    try:
        # 验证导入模式
        if import_mode not in ["standard", "smart"]:
            raise HTTPException(status_code=400, detail="导入模式必须是 'standard' 或 'smart'")
        
        # 解析导入选项
        options = json.loads(import_options)
        
        # 创建任务数据
        task_data = ImportTaskCreate(
            name=name,
            file_name=file.filename,
            import_mode=import_mode,
            import_options=options,
            batch_size=batch_size
        )
        
        return await async_import_service.create_import_task(file, task_data, db)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="导入选项格式错误")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=ImportTaskListResponse)
async def list_import_tasks(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """获取导入任务列表"""
    tasks = await async_import_service.list_tasks(db, limit)
    has_running = await async_import_service.has_running_task(db)
    
    return ImportTaskListResponse(
        tasks=tasks,
        total=len(tasks),
        has_running_task=has_running
    )

@router.get("/{task_id}/status", response_model=ImportTaskStatus)
async def get_task_status(
    task_id: int,
    db: Session = Depends(get_db)
):
    """获取任务状态"""
    return await async_import_service.get_task_status(task_id, db)

@router.post("/{task_id}/cancel")
async def cancel_import_task(
    task_id: int,
    db: Session = Depends(get_db)
):
    """取消导入任务"""
    success = await async_import_service.cancel_task(task_id, db)
    return {"success": success, "message": "任务已取消"}

@router.get("/has-running")
async def check_running_task(db: Session = Depends(get_db)):
    """检查是否有正在运行的任务"""
    has_running = await async_import_service.has_running_task(db)
    return {"has_running_task": has_running}

@router.get("/template/download")
async def download_excel_template():
    """下载标准Excel导入模版"""
    try:
        template_path = ExcelTemplateService.generate_template_file()
        return FileResponse(
            path=template_path,
            filename="测试用例导入模版.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载模版失败: {str(e)}")

@router.get("/{task_id}", response_model=ImportTaskResponse)
async def get_import_task(
    task_id: int,
    db: Session = Depends(get_db)
):
    """获取导入任务详情"""
    from ..database import ImportTask
    
    task = db.query(ImportTask).filter(ImportTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return ImportTaskResponse.from_orm(task)