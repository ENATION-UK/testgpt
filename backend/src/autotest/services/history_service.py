"""
历史记录服务模块
"""
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import timedelta

from ..core.time_utils import beijing_now, ensure_timezone_aware
from ..database import TestCase, SessionLocal
from ..config_manager import ConfigManager

class HistoryService:
    """历史记录服务"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config_manager = ConfigManager()
        self.history_cache_dir = self.config_manager.get_history_directory()
    
    def get_history_path(self, test_case_id: int) -> Path:
        """获取测试用例的 history 文件路径"""
        return self.history_cache_dir / f"test_case_{test_case_id}_history.json"
    
    def get_history_path_from_relative(self, relative_path: str) -> Optional[Path]:
        """根据相对路径获取完整的 history 文件路径"""
        self.logger.info(f"=== 开始解析 history 路径 ===")
        self.logger.info(f"输入的相对路径: {relative_path}")
        self.logger.info(f"配置根目录: {self.config_manager.data_dir}")
        
        if not relative_path:
            self.logger.warning("输入的相对路径为空")
            return None
        
        # 如果已经是绝对路径，直接返回
        if Path(relative_path).is_absolute():
            self.logger.info(f"输入路径已经是绝对路径: {relative_path}")
            return Path(relative_path)
        
        # 如果是相对路径，相对于配置根目录构建完整路径
        full_path = self.config_manager.data_dir / relative_path
        self.logger.info(f"构建的完整路径: {full_path}")
        self.logger.info(f"=== history 路径解析完成 ===")
        return full_path
    
    def is_history_valid(self, test_case: TestCase) -> bool:
        """检查 history 是否有效"""
        self.logger.info(f"=== 开始验证测试用例 {test_case.id} 的 history 缓存 ===")
        self.logger.info(f"测试用例 {test_case.id} 的 history_path: {test_case.history_path}")
        self.logger.info(f"测试用例 {test_case.id} 的 history_updated_at: {test_case.history_updated_at}")
        
        if not test_case.history_path:
            self.logger.info(f"测试用例 {test_case.id} 没有 history_path，缓存无效")
            return False
        
        # 根据相对路径获取完整路径
        history_path = self.get_history_path_from_relative(test_case.history_path)
        self.logger.info(f"测试用例 {test_case.id} 的完整 history 路径: {history_path}")
        
        if not history_path or not history_path.exists():
            self.logger.warning(f"测试用例 {test_case.id} 的 history 文件不存在或路径无效: {history_path}")
            return False
        
        # 检查文件是否为空或损坏
        try:
            file_size = history_path.stat().st_size
            self.logger.info(f"测试用例 {test_case.id} 的 history 文件大小: {file_size} 字节")
            
            if file_size == 0:
                self.logger.warning(f"测试用例 {test_case.id} 的 history 文件为空")
                return False
            
            # 尝试解析 JSON 文件
            with open(history_path, 'r', encoding='utf-8') as f:
                content = f.read()
                json.loads(content)
                self.logger.info(f"测试用例 {test_case.id} 的 history 文件 JSON 格式验证通过")
            return True
        except Exception as e:
            self.logger.warning(f"测试用例 {test_case.id} 的 history 文件 {history_path} 无效: {e}")
            return False
        finally:
            self.logger.info(f"=== 测试用例 {test_case.id} 的 history 缓存验证完成 ===")
    
    def should_use_history(self, test_case: TestCase) -> bool:
        """判断是否应该使用 history 缓存"""
        self.logger.info(f"=== 开始判断测试用例 {test_case.id} 是否应该使用 history 缓存 ===")
        
        # 如果没有 history 文件，直接返回 False
        if not self.is_history_valid(test_case):
            self.logger.info(f"测试用例 {test_case.id} 的 history 缓存无效，将重新执行")
            return False
        
        # 检查 history 是否过期（比如超过7天）
        if test_case.history_updated_at:
            try:
                # 确保时区一致性
                history_time = ensure_timezone_aware(test_case.history_updated_at)
                current_time = beijing_now()
                time_diff = current_time - history_time
                days_diff = time_diff.days
                
                self.logger.info(f"测试用例 {test_case.id} 的 history 更新时间: {history_time}")
                self.logger.info(f"当前时间: {current_time}")
                self.logger.info(f"时间差: {time_diff} (共 {days_diff} 天)")
                
                if time_diff > timedelta(days=7):
                    self.logger.info(f"测试用例 {test_case.id} 的 history 已过期 ({days_diff} 天 > 7 天)，将重新执行")
                    return False
                else:
                    self.logger.info(f"测试用例 {test_case.id} 的 history 未过期 ({days_diff} 天 <= 7 天)，可以使用缓存")
            except Exception as e:
                self.logger.warning(f"测试用例 {test_case.id} 的 history 时间计算出错: {e}")
                return False
        else:
            self.logger.warning(f"测试用例 {test_case.id} 的 history_updated_at 为空，将重新执行")
            return False
        
        self.logger.info(f"=== 测试用例 {test_case.id} 可以使用 history 缓存 ===")
        return True
    
    def save_history_to_cache(self, test_case_id: int, agent, db) -> str:
        """保存 history 到缓存并更新数据库"""
        try:
            self.logger.info(f"=== 开始保存测试用例 {test_case_id} 的 history 到缓存 ===")
            
            # 生成 history 文件路径
            history_path = self.get_history_path(test_case_id)
            self.logger.info(f"生成的 history 文件路径: {history_path}")
            
            # 使用 agent.save_history() 方法保存，这是正确的方式
            self.logger.info("开始调用 agent.save_history() 保存历史记录...")
            agent.save_history(str(history_path))
            self.logger.info("agent.save_history() 调用完成")
            
            # 将绝对路径转换为相对路径（相对于配置根目录）
            relative_path = f"history/test_case_{test_case_id}_history.json"
            self.logger.info(f"转换后的相对路径: {relative_path}")
            
            # 更新数据库中的 history 路径和时间
            test_case = db.query(TestCase).filter(TestCase.id == test_case_id).first()
            if test_case:
                test_case.history_path = relative_path
                test_case.history_updated_at = beijing_now()
                db.commit()
                self.logger.info(f"✅ 已保存测试用例 {test_case_id} 的 history 到 {relative_path}")
                self.logger.info(f"数据库更新时间: {test_case.history_updated_at}")
            else:
                self.logger.warning(f"未找到测试用例 {test_case_id}，无法更新数据库")
            
            self.logger.info(f"=== 测试用例 {test_case_id} 的 history 缓存保存完成 ===")
            return relative_path
        except Exception as e:
            self.logger.error(f"保存 history 失败: {e}")
            import traceback
            self.logger.error(f"保存 history 详细错误: {traceback.format_exc()}")
            return ""
    
    def invalidate_history(self, test_case_id: int, db) -> None:
        """使 history 失效"""
        try:
            self.logger.info(f"=== 开始使测试用例 {test_case_id} 的 history 失效 ===")
            test_case = db.query(TestCase).filter(TestCase.id == test_case_id).first()
            if test_case:
                old_history_path = test_case.history_path
                old_updated_at = test_case.history_updated_at
                
                test_case.history_path = None
                test_case.history_updated_at = None
                db.commit()
                
                self.logger.info(f"✅ 已使测试用例 {test_case_id} 的 history 失效")
                self.logger.info(f"原 history_path: {old_history_path}")
                self.logger.info(f"原 history_updated_at: {old_updated_at}")
            else:
                self.logger.warning(f"未找到测试用例 {test_case_id}，无法使 history 失效")
        except Exception as e:
            self.logger.error(f"使 history 失效失败: {e}")
            import traceback
            self.logger.error(f"使 history 失效详细错误: {traceback.format_exc()}")
        finally:
            self.logger.info(f"=== 测试用例 {test_case_id} 的 history 失效操作完成 ===")
    
    def force_refresh_history(self, test_case_id: int) -> bool:
        """强制刷新指定测试用例的 history 缓存"""
        try:
            self.logger.info(f"=== 开始强制刷新测试用例 {test_case_id} 的 history 缓存 ===")
            db = SessionLocal()
            try:
                test_case = db.query(TestCase).filter(TestCase.id == test_case_id).first()
                if test_case:
                    self.logger.info(f"找到测试用例 {test_case_id}，当前 history_path: {test_case.history_path}")
                    self.logger.info(f"当前 history_updated_at: {test_case.history_updated_at}")
                    
                    self.invalidate_history(test_case_id, db)
                    self.logger.info(f"✅ 已强制刷新测试用例 {test_case_id} 的 history 缓存")
                    return True
                else:
                    self.logger.warning(f"测试用例 {test_case_id} 不存在")
                    return False
            finally:
                db.close()
        except Exception as e:
            self.logger.error(f"强制刷新 history 缓存失败: {e}")
            import traceback
            self.logger.error(f"强制刷新 history 缓存详细错误: {traceback.format_exc()}")
            return False
        finally:
            self.logger.info(f"=== 测试用例 {test_case_id} 的 history 缓存强制刷新操作完成 ===")
    
    def cleanup_expired_history(self, max_days: int = 30) -> int:
        """清理过期的 history 文件"""
        try:
            self.logger.info(f"=== 开始清理过期的 history 文件，最大保留天数: {max_days} ===")
            db = SessionLocal()
            try:
                cutoff_date = beijing_now() - timedelta(days=max_days)
                self.logger.info(f"清理截止日期: {cutoff_date}")
                
                # 查找过期的测试用例
                expired_test_cases = db.query(TestCase).filter(
                    TestCase.history_path.isnot(None),
                    TestCase.history_updated_at < cutoff_date
                ).all()
                
                self.logger.info(f"找到 {len(expired_test_cases)} 个过期的测试用例")
                
                cleaned_count = 0
                for test_case in expired_test_cases:
                    try:
                        self.logger.info(f"清理测试用例 {test_case.id} 的过期 history")
                        self.logger.info(f"history_path: {test_case.history_path}")
                        self.logger.info(f"history_updated_at: {test_case.history_updated_at}")
                        
                        # 删除文件
                        full_history_path = self.get_history_path_from_relative(test_case.history_path)
                        if full_history_path and full_history_path.exists():
                            full_history_path.unlink()
                            self.logger.info(f"已删除过期文件: {full_history_path}")
                        
                        # 更新数据库
                        test_case.history_path = None
                        test_case.history_updated_at = None
                        cleaned_count += 1
                        
                        self.logger.info(f"✅ 已清理过期的 history 文件: {test_case.history_path}")
                    except Exception as e:
                        self.logger.warning(f"清理 history 文件失败 {test_case.history_path}: {e}")
                
                db.commit()
                self.logger.info(f"=== 过期 history 文件清理完成，共清理 {cleaned_count} 个 ===")
                return cleaned_count
                
            finally:
                db.close()
        except Exception as e:
            self.logger.error(f"清理过期的 history 文件失败: {e}")
            import traceback
            self.logger.error(f"清理过期 history 文件详细错误: {traceback.format_exc()}")
            return 0
    
    def get_history_stats(self) -> Dict[str, Any]:
        """获取 history 缓存统计信息"""
        try:
            db = SessionLocal()
            try:
                total_cases = db.query(TestCase).filter(TestCase.is_deleted == False).count()
                cached_cases = db.query(TestCase).filter(
                    TestCase.history_path.isnot(None),
                    TestCase.is_deleted == False
                ).count()
                
                # 获取缓存大小
                cache_size = 0
                if self.history_cache_dir.exists():
                    for file_path in self.history_cache_dir.glob("*.json"):
                        cache_size += file_path.stat().st_size
                
                return {
                    "total_cases": total_cases,
                    "cached_cases": cached_cases,
                    "cache_hit_rate": (cached_cases / total_cases * 100) if total_cases > 0 else 0,
                    "cache_size_bytes": cache_size,
                    "cache_size_mb": round(cache_size / (1024 * 1024), 2)
                }
            finally:
                db.close()
        except Exception as e:
            self.logger.error(f"获取 history 统计信息失败: {e}")
            return {}
