from database import Base
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Float,
    Text,
    ForeignKey,
    DateTime,
)
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint
from datetime import datetime


# 会议实例表（例如某届会议）
class ConferenceInstance(Base):
    __tablename__ = "conference_instance"

    instance_id = Column(Integer, primary_key=True, autoincrement=True)  # 主键，自增
    conference_id = Column(
        Integer, ForeignKey("conference.conference_id"), nullable=False
    )  # 关联的会议ID
    year = Column(Integer, nullable=False)  # 年份
    location = Column(String(255))  # 地点
    start_date = Column(DateTime)  # 开始日期
    end_date = Column(DateTime)  # 结束日期
    url = Column(String(255))  # 会议网站
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 与会议的关系
    conference_to_instance = relationship(
        "Conference", back_populates="instance_to_conference"
    )

    def __repr__(self):
        return f"<ConferenceInstance(id={self.instance_id}, conference_id={self.conference_id}, year={self.year})>"


# 会议信息表
class Conference(Base):
    __tablename__ = "conference"

    conference_id = Column(Integer, primary_key=True, autoincrement=True)  # 主键，自增
    name = Column(String(255), nullable=False, unique=True)  # 会议名称，唯一，不能为空
    type = Column(String(255))  # 会议类型
    description = Column(Text)  # 会议描述，允许为空

    instance_to_conference = relationship(
        "ConferenceInstance",
        back_populates="conference_to_instance",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        # 这是数据库级别的唯一约束
        UniqueConstraint("name", name="unique_conference_name"),
    )

    def __repr__(self):
        return f"<Conference(id={self.conference_id}, name={self.name})>"
