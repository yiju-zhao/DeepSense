# 定义任务状态枚举
import datetime
import enum
from typing import Dict, List, Optional, Any

from pydantic import BaseModel
from sqlmodel import Field, Relationship, SQLModel
from datetime import date, datetime, timedelta, timezone
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
    id: Optional[int] = Field(default=None, primary_key=True, description="ID,主键,自增")
    arxiv_id: str = Field(
        ..., 
        max_length=255, unique=True, index=True, 
        description="唯一的 arXiv 论文ID"
    )
    title: str = Field(..., max_length=500, description="论文标题")
    pdf_url: Optional[str] = Field(default=None, description="论文pdf下载地址")
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

class Publication(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, description="ID,主键,自增")
    paper_id: str = Field(
        ..., 
        max_length=255, unique=True, index=True, 
        description="唯一的论文ID"
    )
    instance_id: Optional[int] = Field(default=None, description="实例的唯一标识符，外键关联期刊或者会议")
    title: str = Field(..., max_length=500, description="论文标题")
    year: Optional[int] = Field(default=None, description="论文发表的年份")
    publish_date: Optional[date] = Field(default=None, description="论文的具体发表日期")
    tldr: Optional[str] = Field(default=None, description="论文的简要概述，TL;DR（Too Long; Didn't Read）")
    abstract: Optional[str] = Field(default=None, description="论文的摘要")
    keywords: Optional[str] = Field(default=None, description="论文的关键词列表,以逗号分隔")
    research_topics: Optional[str] = Field(default=None, description="论文的研究主题,以逗号分隔")
    conclusion: Optional[str] = Field(default=None, description="论文的结论部分")
    triage_qa: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON), description="预设问答的结果，存储为 JSON 格式")
    content_raw_text: Optional[str] = Field(default=None, description="论文的原始文本内容")
    reference_raw_text: Optional[str] = Field(default=None, description="论文引用部分的原始文本")
    pdf_path: Optional[str] = Field(default=None, max_length=255, description="PDF 文件的存储路径，最大长度为255字符")
    citation_count: Optional[int] = Field(default=None, description="论文被引用的次数")
    award: Optional[str] = Field(default=None, max_length=255, description="论文获得的奖项信息，最大长度为255字符")
    doi: Optional[str] = Field(default=None, max_length=255, description="论文的数字对象唯一标识符，最大长度为255字符")
    url: Optional[str] = Field(default=None, max_length=255, description="论文的在线访问链接，最大长度为255字符")
    pdf_url: Optional[str] = Field(default=None, max_length=255, description="PDF 文件的在线下载链接，最大长度为255字符")
    attachment_url: Optional[str] = Field(default=None, max_length=255, description="附件的在线访问链接，最大长度为255字符")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="创建时间")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="更新时间")
    class Config:
        from_attributes = True
    
    def __repr__(self):
         return f"<Publication(id='{self.id}', title='{self.title}')>"

class SOTAContext(SQLModel, table=True):
    """
    表示知识库条目的模型。
    """
    id: Optional[int] = Field(default=None, primary_key=True, description="ID,主键,自增")
    keyword: str = Field(..., description="技术主题或研究方向的关键字")
    description: Optional[str] = Field(default=None, description="关键字对应的描述")
    research_context: Optional[str] = Field(default=None, description="关键字对应的最新研究成果")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="创建时间")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="更新时间")
    class Config:
        from_attributes = True
    
    def __repr__(self):
         return f"<SOTAContext(id='{self.id}', keyword='{self.keyword}')>"

class PaperScores(SQLModel, table=True):
    """
    存储论文评分信息的模型。
    """
    id: Optional[int] = Field(default=None, primary_key=True, description="ID,主键,自增")
    paper_id: str = Field(
        ..., 
        max_length=255, unique=True, index=True, 
        description="唯一的论文ID"
    )
    title: str = Field(..., description="论文的标题")
    innovation_score: Optional[float] = Field(default=None, ge=0.0, le=10.0, description="创新性评分，范围为0到10")
    innovation_reason: Optional[str] = Field(default=None, description="创新性评分的理由")
    performance_score: Optional[float] = Field(default=None, ge=0.0, le=10.0,description="性能评分，范围为0到10")
    performance_reason: Optional[str] = Field(default=None, description="性能评分的理由")
    simplicity_score: Optional[float] = Field(default=None, ge=0.0, le=10.0,description="简洁性评分，范围为0到10")
    simplicity_reason: Optional[str] = Field(default=None, description="简洁性评分的理由")
    reusability_score: Optional[float] = Field(default=None, ge=0.0, le=10.0,description="可重用性评分，范围为0到10")
    reusability_reason: Optional[str] = Field(default=None, description="可重用性评分的理由")
    authority_score: Optional[float] = Field(default=None, ge=0.0, le=10.0, description="权威性评分，范围为0到10")
    authority_reason: Optional[str] = Field(default=None, description="权威性评分的理由")
    weighted_score: Optional[float] = Field(default=None, ge=0.0, le=10.0, description="综合得分，范围为0到10")
    recommend: bool = Field(..., description="是否推荐此论文")
    recommend_reason: Optional[str] = Field(default=None, description="推荐或不推荐的理由")
    who_should_read: Optional[str] = Field(default=None, description="适合阅读此论文的目标读者")
    ai_reviewer: Optional[str] = Field(default=None, description="哪些ai reviewer 分析过该文章,以逗号i隔")
    confidence_score: Optional[float] = Field(default=None, ge=0.0, le=1, description="信心评分，范围为0到1")
    review_status: Optional[str] = Field(default=None, description="评审状态，例如 pending、completed, error 等")
    error_message: Optional[str] = Field(default=None, description="错误信息")
    log: Optional[str] = Field(default=None, description="执行日志")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="创建时间")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="更新时间")
    
    class Config:
        from_attributes = True
    
    def get_review_status(self) -> str:
        """
        获取评审状态的详细信息，包括各项评分、推荐情况和错误日志（如果有）。

        返回:
            str: 评审状态的详细信息字符串。
        """
        status_info = [
            f"Review Status: {self.review_status}",
            f"Error Message: {self.error_message}" if self.error_message else None,
            f"Innovation Score: {self.innovation_score} (Reason: {self.innovation_reason})" if self.innovation_score is not None else None,
            f"Performance Score: {self.performance_score} (Reason: {self.performance_reason})" if self.performance_score is not None else None,
            f"Simplicity Score: {self.simplicity_score} (Reason: {self.simplicity_reason})" if self.simplicity_score is not None else None,
            f"Reusability Score: {self.reusability_score} (Reason: {self.reusability_reason})" if self.reusability_score is not None else None,
            f"Authority Score: {self.authority_score} (Reason: {self.authority_reason})" if self.authority_score is not None else None,
            f"Weighted Score: {self.weighted_score}" if self.weighted_score is not None else None,
            f"Recommend: {'Yes' if self.recommend else 'No'}",
            f"Recommend Reason: {self.recommend_reason}" if self.recommend_reason else None,
            f"Who Should Read: {self.who_should_read}" if self.who_should_read else None,
            f"Confidence Score: {self.confidence_score}" if self.confidence_score is not None else None,
            f"AI Reviewer: {self.ai_reviewer}" if self.ai_reviewer else None,]
        # 过滤掉值为 None 的项，并用换行符连接
        return "\n".join(filter(None, status_info))
    
    def __repr__(self):
         return f"<PaperScores(id='{self.id}', paper_id='{self.paper_id}', title='{self.title}')>"

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

class StandardResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
    task_id: Optional[str] = None  # Make task_id optional

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