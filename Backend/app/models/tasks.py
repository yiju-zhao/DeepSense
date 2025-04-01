# 定义任务状态枚举
import datetime
import enum
from typing import Dict, List, Optional, Any

from pydantic import BaseModel
from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime, timedelta, timezone
from sqlalchemy import Column, JSON, Enum



class TaskStatus(enum.Enum):
    pending = "pending"
    running = "running"
    stopped = "stopped"
    failed = "failed"
    completed = "completed"

class TaskExecution(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, description="执行记录ID, 主键, 自增")
    task_id: int = Field(foreign_key="crawlertask.id", description="关联的任务ID")
    status: str = Field(..., sa_column=Column(Enum(TaskStatus), nullable=False), description="执行状态，例如 pending、running、completed 等")
    start_time: Optional[datetime] = Field(default=None, description="执行开始时间")
    end_time: Optional[datetime] = Field(default=None, description="执行结束时间")
    log: Optional[str] = Field(default=None, description="执行日志")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="记录创建时间")
    # 关联任务
    task: "CrawlerTask" = Relationship(back_populates="executions")
    def __repr__(self):
        return f"<TaskExecution(id={self.id}, ntask_idame={self.task_id}, status={self.status.value})>"
    
class CrawlerTask(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, description="任务ID,主键,自增")
    name: str = Field(..., index=True, max_length=255, description="任务名称")
    function_name: str = Field(..., max_length=255, description="执行函数名称")
    parameters: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON), description="任务执行参数，存储为 JSON 格式")
    description: Optional[str] = Field(default=None, description="任务描述")
    status: TaskStatus = Field(..., sa_column=Column(Enum(TaskStatus), nullable=False), description="任务状态，例如 pending、running、completed 等")
    start_time: Optional[datetime] = Field(default=None, description="任务开始时间")
    end_time: Optional[datetime] = Field(default=None, description="任务结束时间")
    last_run_time: Optional[datetime] = Field(default=None, description="上次运行时间")
    next_run_time: Optional[datetime] = Field(default=None, description="下次运行时间")
    repeat_type: Optional[str] = Field(default=None, max_length=50, description="重复类型，如 daily、weekly 等")
    repeat_interval: Optional[int] = Field(default=None, description="重复间隔（单位由业务决定）")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="创建时间")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="更新时间")
    # 关联任务执行记录
    executions: list["TaskExecution"] = Relationship(back_populates="task")
    
    def __repr__(self):
        return f"<CrawlerTask(id={self.id}, name={self.name}, status={self.status.value})>"

    def update_next_run_time(self):
        """更新下次运行时间，根据 repeat_type 来计算"""
        now = datetime.now()
        if self.repeat_type == 'hourly':
            # 默认每小时执行一次，如果 repeat_interval 存在，则间隔为该值（单位：小时）
            delta = timedelta(hours=self.repeat_interval or 1)
        elif self.repeat_type == 'daily':
            delta = timedelta(days=self.repeat_interval or 1)
        elif self.repeat_type == 'weekly':
            delta = timedelta(weeks=self.repeat_interval or 1)
        else:
            return None
        self.next_run_time = (self.next_run_time or now) + delta
        
    def __repr__(self):
        return f"<CrawlerTask(id={self.id}, name={self.name}, status={self.status.value})>"

class ArxivPaper(SQLModel, table=True):    
    id: Optional[int] = Field(default=None, primary_key=True, description="任务ID,主键,自增")
    arxiv_id: str = Field(
        ..., 
        max_length=255, unique=True, index=True, 
        description="唯一的 arXiv 论文ID"
    )
    title: str = Field(..., max_length=500, description="论文标题")
    published: Optional[datetime] = Field(default=None, description="论文发布时间")
    summary: Optional[str] = Field(default=None, description="论文摘要")
    authors: Optional[List[str]] = Field(default=None, sa_column=Column(JSON), description="作者列表")
    primery_category: Optional[str] = Field(default=None, description="主要分类")
    categories: Optional[List[str]] = Field(default=None, sa_column=Column(JSON), description="分类列表")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="创建时间")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="更新时间")

    class Config:
        from_attributes = True
    
    def __repr__(self):
        return f"<ArxivPaper(arxiv_id='{self.arxiv_id}', title='{self.title}')>"
   
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

class TaskExecutionResponse(BaseModel):
    id: int
    task_id: int
    status: str
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    log: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
class TaskExecutionList(BaseModel):
    data: List[TaskExecutionResponse]
    count: int
    
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

    class Config:
        from_attributes = True

# 更新任务时使用的 Pydantic 模型
class CrawlerTaskUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    function_name: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[str] = None  # 如果允许手动更新状态，可放开；否则可以移除
    repeat_type: Optional[str] = None
    repeat_interval: Optional[int] = None
    next_run_time: Optional[datetime] = None

class CrawlerTaskList(BaseModel):
    data: list[CrawlerTaskResponse]
    count: int

class CrawlerTaskActionResponse(BaseModel):
    message: str
    task_id: int