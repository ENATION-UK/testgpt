"""
Excel导入服务
"""

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
import pandas as pd
import io
import json
import os
from typing import List, Dict, Any

from ..database import TestCase
from ..config_manager import ConfigManager
from .llm_service import LLMService

class ExcelService:
    """Excel文件处理服务"""
    
    @staticmethod
    async def preview_excel(file: UploadFile) -> Dict[str, Any]:
        """预览Excel文件内容"""
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="只支持Excel文件格式")
        
        try:
            # 读取Excel文件
            content = await file.read()
            df = pd.read_excel(io.BytesIO(content))
            
            # 处理NaN值
            df = df.fillna('')
            
            # 转换为字典列表
            data = df.to_dict('records')
            
            # 返回前5行作为预览
            preview = data[:5] if len(data) > 5 else data
            
            return {"preview": preview, "total_rows": len(data)}
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"读取Excel文件失败: {str(e)}")

    @staticmethod
    async def import_excel(file: UploadFile, options: str, db: Session) -> Dict[str, Any]:
        """导入Excel文件中的测试用例"""
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="只支持Excel文件格式")
        
        try:
            # 解析导入选项
            import_options = json.loads(options)
            
            # 读取Excel文件
            content = await file.read()
            df = pd.read_excel(io.BytesIO(content))
            
            # 处理NaN值
            df = df.fillna('')
            
            # 使用大模型分析Excel内容并转换为测试用例格式
            test_cases = await LLMService.analyze_excel_with_llm(df, import_options)
            
            # 批量创建测试用例
            created_count = 0
            for test_case_data in test_cases:
                try:
                    db_test_case = TestCase(**test_case_data)
                    db.add(db_test_case)
                    created_count += 1
                except Exception as e:
                    print(f"创建测试用例失败: {e}")
                    continue
            
            db.commit()
            
            return {
                "success": True,
                "imported_count": created_count,
                "total_rows": len(df),
                "message": f"成功导入 {created_count} 个测试用例"
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"导入Excel文件失败: {str(e)}")

 