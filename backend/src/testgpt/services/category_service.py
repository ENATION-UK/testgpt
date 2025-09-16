"""
分类服务
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional, Dict, Any
from ..database import Category, TestCase
from ..models import CategoryCreate, CategoryUpdate, CategoryResponse
from datetime import datetime

class CategoryService:
    def __init__(self, db: Session):
        self.db = db

    def create_category(self, category_data: CategoryCreate) -> CategoryResponse:
        """创建分类"""
        # 计算层级
        level = 0
        if category_data.parent_id:
            parent = self.db.query(Category).filter(
                and_(Category.id == category_data.parent_id, Category.is_deleted == False)
            ).first()
            if not parent:
                raise ValueError("父分类不存在")
            level = parent.level + 1

        # 创建分类
        db_category = Category(
            name=category_data.name,
            description=category_data.description,
            parent_id=category_data.parent_id,
            level=level,
            sort_order=category_data.sort_order
        )
        
        self.db.add(db_category)
        self.db.commit()
        self.db.refresh(db_category)
        
        return self._to_response(db_category)

    def get_category(self, category_id: int) -> Optional[CategoryResponse]:
        """获取单个分类"""
        category = self.db.query(Category).filter(
            and_(Category.id == category_id, Category.is_deleted == False)
        ).first()
        
        if not category:
            return None
            
        return self._to_response(category)

    def get_categories(self, parent_id: Optional[int] = None, include_inactive: bool = False) -> List[CategoryResponse]:
        """获取分类列表"""
        query = self.db.query(Category).filter(Category.is_deleted == False)
        
        if parent_id is not None:
            query = query.filter(Category.parent_id == parent_id)
        else:
            query = query.filter(Category.parent_id.is_(None))
            
        if not include_inactive:
            query = query.filter(Category.is_active == True)
            
        query = query.order_by(Category.sort_order, Category.name)
        
        categories = query.all()
        return [self._to_response(category) for category in categories]

    def get_category_tree(self, include_inactive: bool = False) -> List[CategoryResponse]:
        """获取分类树形结构"""
        # 获取所有分类
        query = self.db.query(Category).filter(Category.is_deleted == False)
        if not include_inactive:
            query = query.filter(Category.is_active == True)
        query = query.order_by(Category.sort_order, Category.name)
        
        all_categories = query.all()
        
        # 构建树形结构
        category_dict = {cat.id: self._to_response(cat) for cat in all_categories}
        root_categories = []
        
        for category in all_categories:
            if category.parent_id is None:
                root_categories.append(category_dict[category.id])
            else:
                if category.parent_id in category_dict:
                    if category_dict[category.parent_id].children is None:
                        category_dict[category.parent_id].children = []
                    category_dict[category.parent_id].children.append(category_dict[category.id])
        
        return root_categories

    def get_category_with_children(self, category_id: int, include_inactive: bool = False) -> Optional[CategoryResponse]:
        """获取分类及其所有子分类"""
        # 获取指定分类
        category = self.db.query(Category).filter(
            and_(Category.id == category_id, Category.is_deleted == False)
        ).first()
        
        if not category:
            return None
            
        # 获取所有子分类
        children = self._get_all_children(category_id, include_inactive)
        
        response = self._to_response(category)
        response.children = children
        
        return response

    def _get_all_children(self, parent_id: int, include_inactive: bool = False) -> List[CategoryResponse]:
        """递归获取所有子分类"""
        query = self.db.query(Category).filter(
            and_(Category.parent_id == parent_id, Category.is_deleted == False)
        )
        if not include_inactive:
            query = query.filter(Category.is_active == True)
        query = query.order_by(Category.sort_order, Category.name)
        
        children = query.all()
        result = []
        
        for child in children:
            child_response = self._to_response(child)
            child_response.children = self._get_all_children(child.id, include_inactive)
            result.append(child_response)
            
        return result

    def update_category(self, category_id: int, category_data: CategoryUpdate) -> Optional[CategoryResponse]:
        """更新分类"""
        category = self.db.query(Category).filter(
            and_(Category.id == category_id, Category.is_deleted == False)
        ).first()
        
        if not category:
            return None
            
        # 更新字段
        if category_data.name is not None:
            category.name = category_data.name
        if category_data.description is not None:
            category.description = category_data.description
        if category_data.sort_order is not None:
            category.sort_order = category_data.sort_order
        if category_data.is_active is not None:
            category.is_active = category_data.is_active
            
        # 如果更新了父分类，需要重新计算层级
        if category_data.parent_id is not None and category_data.parent_id != category.parent_id:
            if category_data.parent_id == category_id:
                raise ValueError("不能将分类设置为自己的父分类")
                
            # 检查是否会造成循环引用
            if self._would_create_cycle(category_id, category_data.parent_id):
                raise ValueError("不能创建循环引用的分类结构")
                
            category.parent_id = category_data.parent_id
            category.level = self._calculate_level(category_data.parent_id)
            
        category.updated_at = datetime.now()
        
        self.db.commit()
        self.db.refresh(category)
        
        return self._to_response(category)

    def _would_create_cycle(self, category_id: int, new_parent_id: int) -> bool:
        """检查是否会造成循环引用"""
        current_parent_id = new_parent_id
        while current_parent_id is not None:
            if current_parent_id == category_id:
                return True
            parent = self.db.query(Category).filter(
                and_(Category.id == current_parent_id, Category.is_deleted == False)
            ).first()
            if not parent:
                break
            current_parent_id = parent.parent_id
        return False

    def _calculate_level(self, parent_id: Optional[int]) -> int:
        """计算分类层级"""
        if parent_id is None:
            return 0
            
        parent = self.db.query(Category).filter(
            and_(Category.id == parent_id, Category.is_deleted == False)
        ).first()
        
        if not parent:
            return 0
            
        return parent.level + 1

    def delete_category(self, category_id: int, force: bool = False) -> bool:
        """删除分类"""
        category = self.db.query(Category).filter(
            and_(Category.id == category_id, Category.is_deleted == False)
        ).first()
        
        if not category:
            return False
            
        # 检查是否有子分类
        children_count = self.db.query(Category).filter(
            and_(Category.parent_id == category_id, Category.is_deleted == False)
        ).count()
        
        if children_count > 0 and not force:
            raise ValueError("该分类下有子分类，无法删除")
            
        # 检查是否有关联的测试用例
        test_cases_count = self.db.query(TestCase).filter(
            and_(TestCase.category_id == category_id, TestCase.is_deleted == False)
        ).count()
        
        if test_cases_count > 0 and not force:
            raise ValueError("该分类下有关联的测试用例，无法删除")
            
        if force:
            # 强制删除：标记所有子分类为删除
            self._mark_children_deleted(category_id)
            # 将关联的测试用例的分类设为空
            self.db.query(TestCase).filter(
                and_(TestCase.category_id == category_id, TestCase.is_deleted == False)
            ).update({"category_id": None})
            
        category.is_deleted = True
        category.updated_at = datetime.now()
        
        self.db.commit()
        return True

    def _mark_children_deleted(self, parent_id: int):
        """递归标记子分类为删除"""
        children = self.db.query(Category).filter(
            and_(Category.parent_id == parent_id, Category.is_deleted == False)
        ).all()
        
        for child in children:
            child.is_deleted = True
            child.updated_at = datetime.now()
            self._mark_children_deleted(child.id)

    def get_category_test_cases(self, category_id: int, include_children: bool = True) -> List[int]:
        """获取分类下的测试用例ID列表"""
        if include_children:
            # 获取所有子分类ID
            category_ids = self._get_all_descendant_ids(category_id)
            category_ids.append(category_id)
        else:
            category_ids = [category_id]
            
        test_cases = self.db.query(TestCase).filter(
            and_(TestCase.category_id.in_(category_ids), TestCase.is_deleted == False)
        ).all()
        
        return [tc.id for tc in test_cases]

    def _get_all_descendant_ids(self, category_id: int) -> List[int]:
        """获取所有后代分类ID"""
        children = self.db.query(Category).filter(
            and_(Category.parent_id == category_id, Category.is_deleted == False)
        ).all()
        
        descendant_ids = []
        for child in children:
            descendant_ids.append(child.id)
            descendant_ids.extend(self._get_all_descendant_ids(child.id))
            
        return descendant_ids

    def _to_response(self, category: Category) -> CategoryResponse:
        """转换为响应模型"""
        # 计算测试用例数量
        test_case_count = self.db.query(TestCase).filter(
            and_(TestCase.category_id == category.id, TestCase.is_deleted == False)
        ).count()
        
        return CategoryResponse(
            id=category.id,
            name=category.name,
            description=category.description,
            parent_id=category.parent_id,
            level=category.level,
            sort_order=category.sort_order,
            is_active=category.is_active,
            created_at=category.created_at,
            updated_at=category.updated_at,
            children=[],
            test_case_count=test_case_count
        ) 