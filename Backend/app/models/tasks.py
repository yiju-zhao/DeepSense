# 定义任务状态枚举
import datetime
import enum
from typing import Dict, List, Optional, Any

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Float,
    Text,
    JSON,
    Enum,
    ForeignKey,
    DateTime,
    Date,
)
from sqlalchemy.orm import relationship
from database import Base
from datetime import date, datetime, timedelta, timezone
from pydantic import BaseModel


class TaskStatus(enum.Enum):
    pending = "pending"
    running = "running"
    stopped = "stopped"
    failed = "failed"
    completed = "completed"


class CrawlerTask(Base):
    __tablename__ = "crawlertask"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    function_name = Column(String(255), nullable=False)
    parameters = Column(JSON)
    description = Column(Text)
    status = Column(Enum(TaskStatus), nullable=False)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    last_run_time = Column(DateTime)
    next_run_time = Column(DateTime)
    repeat_type = Column(String(50))
    repeat_interval = Column(Integer)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    executions = relationship(
        "TaskExecution", back_populates="task", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return (
            f"<CrawlerTask(id={self.id}, name={self.name}, status={self.status.value})>"
        )

    def update_next_run_time(self):
        """更新下次运行时间，根据 repeat_type 来计算"""
        now = datetime.now()
        if self.repeat_type == "hourly":
            # 默认每小时执行一次，如果 repeat_interval 存在，则间隔为该值（单位：小时）
            delta = timedelta(hours=self.repeat_interval or 1)
        elif self.repeat_type == "daily":
            delta = timedelta(days=self.repeat_interval or 1)
        elif self.repeat_type == "weekly":
            delta = timedelta(weeks=self.repeat_interval or 1)
        else:
            return None
        self.next_run_time = (self.next_run_time or now) + delta


class TaskExecution(Base):
    __tablename__ = "taskexecution"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("crawlertask.id"), nullable=False)
    status = Column(Enum(TaskStatus), nullable=False)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    log = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    task = relationship("CrawlerTask", back_populates="executions")

    def __repr__(self):
        return f"<TaskExecution(id={self.id}, task_id={self.task_id}, status={self.status.value})>"


class ArxivPaper(Base):
    __tablename__ = "arxivpaper"

    id = Column(Integer, primary_key=True, autoincrement=True)
    arxiv_id = Column(String(255), nullable=False, unique=True, index=True)
    title = Column(String(500), nullable=False)
    pdf_url = Column(String(255))
    published = Column(DateTime)
    summary = Column(Text)
    authors = Column(JSON)
    primary_category = Column(String(255))
    categories = Column(JSON)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self):
        return f"<ArxivPaper(arxiv_id='{self.arxiv_id}', title='{self.title}')>"


class Publication(Base):
    __tablename__ = "publication"

    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(String(255), nullable=False, unique=True, index=True)
    instance_id = Column(Integer)
    title = Column(String(500), nullable=False)
    year = Column(Integer)
    publish_date = Column(Date)
    tldr = Column(Text)
    abstract = Column(Text)
    keywords = Column(String(500))
    research_topics = Column(String(500))
    conclusion = Column(Text)
    triage_qa = Column(JSON)
    content_raw_text = Column(Text)
    reference_raw_text = Column(Text)
    pdf_path = Column(String(255))
    citation_count = Column(Integer)
    award = Column(String(255))
    doi = Column(String(255))
    url = Column(String(255))
    pdf_url = Column(String(255))
    attachment_url = Column(String(255))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    scores = relationship("PaperScores", back_populates="publication", uselist=False)

    def __repr__(self):
        return f"<Publication(id='{self.id}', title='{self.title}')>"


class SOTAContext(Base):
    __tablename__ = "sotacontext"

    id = Column(Integer, primary_key=True, autoincrement=True)
    keyword = Column(String(255), nullable=False)
    description = Column(Text)
    research_context = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self):
        return f"<SOTAContext(id='{self.id}', keyword='{self.keyword}')>"


class PaperScores(Base):
    __tablename__ = "paperscores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(
        String(255),
        ForeignKey("publication.paper_id"),
        nullable=False,
        unique=True,
        index=True,
    )
    title = Column(String(500), nullable=False)
    innovation_score = Column(Float)
    innovation_reason = Column(Text)
    performance_score = Column(Float)
    performance_reason = Column(Text)
    simplicity_score = Column(Float)
    simplicity_reason = Column(Text)
    reusability_score = Column(Float)
    reusability_reason = Column(Text)
    authority_score = Column(Float)
    authority_reason = Column(Text)
    weighted_score = Column(Float)
    recommend = Column(Boolean, nullable=False)
    recommend_reason = Column(Text)
    who_should_read = Column(Text)
    ai_reviewer = Column(String(255))
    confidence_score = Column(Float)
    review_status = Column(String(50))
    error_message = Column(Text)
    log = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    publication = relationship("Publication", back_populates="scores")

    def get_review_status(self) -> str:
        """
        获取评审状态的详细信息，包括各项评分、推荐情况和错误日志（如果有）。

        返回:
            str: 评审状态的详细信息字符串。
        """
        status_info = [
            f"Review Status: {self.review_status}",
            f"Error Message: {self.error_message}" if self.error_message else None,
            (
                f"Innovation Score: {self.innovation_score} (Reason: {self.innovation_reason})"
                if self.innovation_score is not None
                else None
            ),
            (
                f"Performance Score: {self.performance_score} (Reason: {self.performance_reason})"
                if self.performance_score is not None
                else None
            ),
            (
                f"Simplicity Score: {self.simplicity_score} (Reason: {self.simplicity_reason})"
                if self.simplicity_score is not None
                else None
            ),
            (
                f"Reusability Score: {self.reusability_score} (Reason: {self.reusability_reason})"
                if self.reusability_score is not None
                else None
            ),
            (
                f"Authority Score: {self.authority_score} (Reason: {self.authority_reason})"
                if self.authority_score is not None
                else None
            ),
            (
                f"Weighted Score: {self.weighted_score}"
                if self.weighted_score is not None
                else None
            ),
            f"Recommend: {'Yes' if self.recommend else 'No'}",
            (
                f"Recommend Reason: {self.recommend_reason}"
                if self.recommend_reason
                else None
            ),
            (
                f"Who Should Read: {self.who_should_read}"
                if self.who_should_read
                else None
            ),
            (
                f"Confidence Score: {self.confidence_score}"
                if self.confidence_score is not None
                else None
            ),
            f"AI Reviewer: {self.ai_reviewer}" if self.ai_reviewer else None,
        ]
        # 过滤掉值为 None 的项，并用换行符连接
        return "\n".join(filter(None, status_info))

    def __repr__(self):
        return f"<PaperScores(id='{self.id}', paper_id='{self.paper_id}', title='{self.title}')>"


# Pydantic models for API responses - these stay the same
class CrawlerTaskCreate(BaseModel):
    name: str
    description: Optional[str] = None
    function_name: str
    parameters: Optional[Dict[str, Any]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    repeat_type: Optional[str] = None
    repeat_interval: Optional[int] = None
    next_run_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class CrawlerTaskUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    function_name: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    status: Optional[TaskStatus] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    repeat_type: Optional[str] = None
    repeat_interval: Optional[int] = None
    next_run_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class CrawlerTaskResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    function_name: str
    parameters: Optional[Dict[str, Any]] = None
    status: TaskStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    last_run_time: Optional[datetime] = None
    next_run_time: Optional[datetime] = None
    repeat_type: Optional[str] = None
    repeat_interval: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CrawlerTaskList(BaseModel):
    data: List[CrawlerTaskResponse]
    count: int


class CrawlerTaskActionResponse(BaseModel):
    success: bool
    message: str
    task_id: int


class TaskExecutionResponse(BaseModel):
    id: int
    task_id: int
    status: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    log: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TaskExecutionList(BaseModel):
    data: List[TaskExecutionResponse]
    count: int


class StandardResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
    task_id: Optional[str] = None
