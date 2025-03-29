from database import Base
from sqlalchemy import Column, Integer, String, Boolean, Float, Text
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint


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