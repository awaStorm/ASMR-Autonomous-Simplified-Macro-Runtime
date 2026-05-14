from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from .database import Base


class Todo(Base):
    """待办事项模型（去除了 user_id 和 group_id）"""
    __tablename__ = "todos"
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    content = Column(String, nullable=False)
    priority = Column(Integer, nullable=False)  # 3=高, 2=中, 1=低
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    deadline = Column(DateTime(timezone=True), nullable=False)
    skip_reminder = Column(Boolean, default=False)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # 提醒标志位（高优先级）
    notified_20 = Column(Boolean, default=False)
    notified_40 = Column(Boolean, default=False)
    notified_60 = Column(Boolean, default=False)
    notified_80 = Column(Boolean, default=False)
    
    # 提醒标志位（中优先级）
    notified_12h = Column(Boolean, default=False)
    
    # 提醒标志位（低优先级）
    notified_24h = Column(Boolean, default=False)
