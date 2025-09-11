"""
截图服务模块
"""
import base64
import logging
from pathlib import Path
from typing import List, Optional

from ..core.time_utils import beijing_now
from ..config_manager import ConfigManager

class ScreenshotService:
    """截图服务"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config_manager = ConfigManager()
    
    def save_screenshots(self, history, execution_id: int) -> List[str]:
        """保存截图到指定目录"""
        screenshots = self._extract_screenshots(history)
        if not screenshots:
            return []
        
        output_dir = self.config_manager.get_screenshots_directory() / f"execution_{execution_id}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        saved_paths = []
        timestamp = beijing_now().strftime("%Y%m%d_%H%M%S")
        
        for i, screenshot in enumerate(screenshots):
            if screenshot and isinstance(screenshot, str):
                try:
                    saved_path = self._save_single_screenshot(screenshot, output_dir, timestamp, i)
                    if saved_path:
                        saved_paths.append(saved_path)
                except Exception as e:
                    self.logger.error(f"保存截图 {i+1} 失败: {e}")
                    continue
        
        return saved_paths
    
    def _extract_screenshots(self, history) -> List[str]:
        """从历史记录中提取截图"""
        if isinstance(history, list):
            all_screenshots = []
            for action in history:
                if hasattr(action, 'attachments') and action.attachments:
                    all_screenshots.extend(action.attachments)
                # 也可以从其他属性中提取截图信息
                if hasattr(action, 'extracted_content') and action.extracted_content:
                    # 这里可以解析 extracted_content 中的截图信息
                    pass
            return all_screenshots
        else:
            # 处理单个对象的情况
            return history.screenshots() if hasattr(history, 'screenshots') else []
    
    def _save_single_screenshot(self, screenshot: str, output_dir: Path, timestamp: str, index: int) -> Optional[str]:
        """保存单个截图"""
        if screenshot.startswith('data:image'):
            return self._save_base64_screenshot(screenshot, output_dir, timestamp, index)
        elif screenshot.startswith('/') or ':' in screenshot:
            return self._save_file_screenshot(screenshot, output_dir, timestamp, index)
        return None
    
    def _save_base64_screenshot(self, screenshot: str, output_dir: Path, timestamp: str, index: int) -> Optional[str]:
        """保存base64编码的截图"""
        try:
            header, data = screenshot.split(',', 1)
            image_data = base64.b64decode(data)
            
            if 'png' in header:
                ext = 'png'
            elif 'jpeg' in header or 'jpg' in header:
                ext = 'jpg'
            else:
                ext = 'png'
            
            filename = f"screenshot_{timestamp}_{index+1:03d}.{ext}"
            filepath = output_dir / filename
            
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            return str(filepath)
        except Exception as e:
            self.logger.error(f"保存base64截图失败: {e}")
            return None
    
    def _save_file_screenshot(self, screenshot: str, output_dir: Path, timestamp: str, index: int) -> Optional[str]:
        """保存文件路径的截图"""
        try:
            source_path = Path(screenshot)
            if source_path.exists():
                filename = f"screenshot_{timestamp}_{index+1:03d}{source_path.suffix}"
                dest_path = output_dir / filename
                
                import shutil
                shutil.copy2(source_path, dest_path)
                return str(dest_path)
        except Exception as e:
            self.logger.error(f"保存文件截图失败: {e}")
        return None
