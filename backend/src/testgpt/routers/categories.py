"""
分类管理路由
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import CategoryCreate, CategoryUpdate, CategoryResponse, CategoryTreeResponse
from ..services.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["分类管理"])

@router.post("/", response_model=CategoryResponse)
def create_category(
    category_data: CategoryCreate,
    db: Session = Depends(get_db)
):
    """创建分类"""
    try:
        category_service = CategoryService(db)
        return category_service.create_category(category_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建分类失败: {str(e)}")

@router.get("/", response_model=List[CategoryResponse])
def get_categories(
    parent_id: Optional[int] = Query(None, description="父分类ID"),
    include_inactive: bool = Query(False, description="是否包含非激活分类"),
    db: Session = Depends(get_db)
):
    """获取分类列表"""
    try:
        category_service = CategoryService(db)
        return category_service.get_categories(parent_id, include_inactive)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取分类列表失败: {str(e)}")

@router.get("/tree", response_model=List[CategoryResponse])
def get_category_tree(
    include_inactive: bool = Query(False, description="是否包含非激活分类"),
    db: Session = Depends(get_db)
):
    """获取分类树形结构"""
    try:
        category_service = CategoryService(db)
        return category_service.get_category_tree(include_inactive)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取分类树失败: {str(e)}")

@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(
    category_id: int,
    db: Session = Depends(get_db)
):
    """获取单个分类"""
    try:
        category_service = CategoryService(db)
        category = category_service.get_category(category_id)
        if not category:
            raise HTTPException(status_code=404, detail="分类不存在")
        return category
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取分类失败: {str(e)}")

@router.get("/{category_id}/with-children", response_model=CategoryResponse)
def get_category_with_children(
    category_id: int,
    include_inactive: bool = Query(False, description="是否包含非激活分类"),
    db: Session = Depends(get_db)
):
    """获取分类及其所有子分类"""
    try:
        category_service = CategoryService(db)
        category = category_service.get_category_with_children(category_id, include_inactive)
        if not category:
            raise HTTPException(status_code=404, detail="分类不存在")
        return category
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取分类及其子分类失败: {str(e)}")

@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    db: Session = Depends(get_db)
):
    """更新分类"""
    try:
        category_service = CategoryService(db)
        category = category_service.update_category(category_id, category_data)
        if not category:
            raise HTTPException(status_code=404, detail="分类不存在")
        return category
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新分类失败: {str(e)}")

@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    force: bool = Query(False, description="是否强制删除（包括子分类和关联的测试用例）"),
    db: Session = Depends(get_db)
):
    """删除分类"""
    try:
        category_service = CategoryService(db)
        success = category_service.delete_category(category_id, force)
        if not success:
            raise HTTPException(status_code=404, detail="分类不存在")
        return {"message": "分类删除成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除分类失败: {str(e)}")

@router.get("/{category_id}/test-cases")
def get_category_test_cases(
    category_id: int,
    include_children: bool = Query(True, description="是否包含子分类下的测试用例"),
    db: Session = Depends(get_db)
):
    """获取分类下的测试用例ID列表"""
    try:
        category_service = CategoryService(db)
        test_case_ids = category_service.get_category_test_cases(category_id, include_children)
        return {
            "category_id": category_id,
            "include_children": include_children,
            "test_case_ids": test_case_ids,
            "count": len(test_case_ids)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取分类测试用例失败: {str(e)}") 