"""
时间工具模块
"""
from datetime import datetime, timezone, timedelta
from typing import Optional

# 设置时区为北京时间
BEIJING_TZ = timezone(timedelta(hours=8))

def beijing_now() -> datetime:
    """获取北京时间"""
    return datetime.now(BEIJING_TZ)

def ensure_timezone_aware(dt: Optional[datetime]) -> Optional[datetime]:
    """确保 datetime 对象有时区信息"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        # 如果没有时区信息，假设是北京时间
        return dt.replace(tzinfo=BEIJING_TZ)
    return dt
