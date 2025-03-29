# 定义任务状态枚举
import datetime
import enum
from typing import Dict, Optional, Any

from pydantic import BaseModel
from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime
from sqlalchemy import Column, JSON, Enum



class TaskStatus(enum.Enum):
    pending = "pending"
    running = "running"
    stopped = "stopped"
    failed = "failed"
    completed = "completed"

class CrawlerTask(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, description="任务ID,主键,自增")
    name: str = Field(..., index=True, max_length=255, description="任务名称")
    function_name: str = Field(..., max_length=255, description="执行函数名称")
    parameters: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON), description="任务执行参数，存储为 JSON 格式")
    description: Optional[str] = Field(default=None, description="任务描述")
    status: str = Field(..., sa_column=Column(Enum(TaskStatus), nullable=False), description="任务状态，例如 pending、running、completed 等")
    start_time: Optional[datetime] = Field(default=None, description="任务开始时间")
    end_time: Optional[datetime] = Field(default=None, description="任务结束时间")
    last_run_time: Optional[datetime] = Field(default=None, description="上次运行时间")
    next_run_time: Optional[datetime] = Field(default=None, description="下次运行时间")
    repeat_type: Optional[str] = Field(default=None, max_length=50, description="重复类型，如 daily、weekly 等")
    repeat_interval: Optional[int] = Field(default=None, description="重复间隔（单位由业务决定）")
    log: Optional[str] = Field(default=None, description="任务日志")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")
    
    def __repr__(self):
        return f"<CrawlerTask(id={self.id}, name={self.name}, status={self.status.value})>"

    def update_next_run_time(self):
        """更新下次运行时间，根据 repeat_type 来计算"""
        now = datetime.datetime.now()
        if self.repeat_type == 'hourly':
            # 默认每小时执行一次，如果 repeat_interval 存在，则间隔为该值（单位：小时）
            delta = datetime.timedelta(hours=self.repeat_interval or 1)
        elif self.repeat_type == 'daily':
            delta = datetime.timedelta(days=self.repeat_interval or 1)
        elif self.repeat_type == 'weekly':
            delta = datetime.timedelta(weeks=self.repeat_interval or 1)
        else:
            return None
        self.next_run_time = (self.next_run_time or now) + delta
        
    def __repr__(self):
        return f"<CrawlerTask(id={self.id}, name={self.name}, status={self.status.value})>"
    
# Shared properties
class CrawlerTaskCreate(BaseModel):
    name: str
    description: Optional[str]
    function_name: str
    parameters: Optional[Dict[str, Any]]
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    repeat_type: Optional[str]
    repeat_interval: Optional[int]
    next_run_time: Optional[datetime]

class CrawlerTaskResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    function_name: str
    parameters: Optional[Dict[str, Any]]
    status: str
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    last_run_time: Optional[datetime]
    next_run_time: Optional[datetime]
    repeat_type: Optional[str]
    repeat_interval: Optional[int]
    log: Optional[str]

    class Config:
        from_attributes = True

class CrawlerTaskList(BaseModel):
    data: list[CrawlerTaskResponse]
    count: int

class CrawlerTaskActionResponse(BaseModel):
    message: str
    task_id: int