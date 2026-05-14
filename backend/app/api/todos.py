from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from ..database import get_db
from ..models import Todo

router = APIRouter()


class TodoBase(BaseModel):
    content: str
    priority: int  # 3=高, 2=中, 1=低
    deadline: datetime
    skip_reminder: bool = False


class TodoCreate(TodoBase):
    pass


class TodoUpdate(BaseModel):
    content: Optional[str] = None
    priority: Optional[int] = None
    deadline: Optional[datetime] = None
    skip_reminder: Optional[bool] = None


class TodoResponse(TodoBase):
    id: int
    created_at: datetime
    completed: bool
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class StatsResponse(BaseModel):
    total: int
    completed: int
    pending: int
    overdue: int
    high_priority: int
    medium_priority: int
    low_priority: int


@router.get("", response_model=List[TodoResponse])
async def get_todos(completed: Optional[bool] = None, db: Session = Depends(get_db)):
    """获取所有待办事项"""
    query = db.query(Todo)
    if completed is not None:
        query = query.filter(Todo.completed == completed)
    
    # 按优先级(降序)和截止时间(升序)排序
    return query.order_by(Todo.priority.desc(), Todo.deadline.asc()).all()


@router.get("/stats", response_model=StatsResponse)
async def get_stats(db: Session = Depends(get_db)):
    """获取统计数据"""
    now = datetime.now()
    
    total = db.query(Todo).count()
    completed = db.query(Todo).filter(Todo.completed == True).count()
    pending = db.query(Todo).filter(Todo.completed == False).count()
    overdue = db.query(Todo).filter(Todo.completed == False, Todo.deadline < now).count()
    
    high = db.query(Todo).filter(Todo.priority == 3, Todo.completed == False).count()
    medium = db.query(Todo).filter(Todo.priority == 2, Todo.completed == False).count()
    low = db.query(Todo).filter(Todo.priority == 1, Todo.completed == False).count()
    
    return StatsResponse(
        total=total,
        completed=completed,
        pending=pending,
        overdue=overdue,
        high_priority=high,
        medium_priority=medium,
        low_priority=low
    )


@router.get("/{todo_id}", response_model=TodoResponse)
async def get_todo(todo_id: int, db: Session = Depends(get_db)):
    """获取单个待办事项"""
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=404, detail="待办事项不存在")
    return todo


@router.post("", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
async def create_todo(todo_data: TodoCreate, db: Session = Depends(get_db)):
    """创建待办事项"""
    todo = Todo(
        content=todo_data.content,
        priority=todo_data.priority,
        deadline=todo_data.deadline,
        skip_reminder=todo_data.skip_reminder,
        created_at=datetime.utcnow(),
        completed=False
    )
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return todo


@router.put("/{todo_id}", response_model=TodoResponse)
async def update_todo(todo_id: int, todo_data: TodoUpdate, db: Session = Depends(get_db)):
    """更新待办事项"""
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=404, detail="待办事项不存在")
    
    update_data = todo_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(todo, field, value)
    
    db.commit()
    db.refresh(todo)
    return todo


@router.post("/{todo_id}/complete", response_model=TodoResponse)
async def complete_todo(todo_id: int, db: Session = Depends(get_db)):
    """标记待办事项为完成"""
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=404, detail="待办事项不存在")
    
    todo.completed = True
    todo.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(todo)
    return todo


@router.post("/{todo_id}/toggle", response_model=TodoResponse)
async def toggle_todo(todo_id: int, db: Session = Depends(get_db)):
    """切换待办事项的完成状态（完成↔未完成）"""
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=404, detail="待办事项不存在")
    
    now = datetime.utcnow()
    
    # 如果是从完成状态恢复到未完成状态
    if todo.completed:
        # 检查是否已过期
        is_overdue = todo.deadline < now
        
        todo.completed = False
        todo.completed_at = None
        db.commit()
        db.refresh(todo)
        
        return {
            **todo.__dict__,
            'is_overdue': is_overdue
        }
    else:
        # 从未完成状态标记为完成
        todo.completed = True
        todo.completed_at = now
        db.commit()
        db.refresh(todo)
        
        return {
            **todo.__dict__,
            'is_overdue': False
        }


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    """删除待办事项"""
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=404, detail="待办事项不存在")
    
    db.delete(todo)
    db.commit()
