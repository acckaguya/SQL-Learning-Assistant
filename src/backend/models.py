from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from src.backend.database import Base

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String)  # "teacher" or "student"
    created_at = Column(DateTime)

class SampleSchema(Base):
    __tablename__ = "sample_schemas"
    
    schema_id = Column(String, primary_key=True, index=True)
    schema_name = Column(String)
    schema_definition = Column(JSONB)
    init_sql = Column(String)
    created_at = Column(DateTime)


class Question(Base):
    __tablename__ = "questions"

    question_id = Column(String, primary_key=True, index=True)
    description = Column(Text)
    answer_sql = Column(Text)
    basic_query = Column(Boolean, default=False)                            # 知识点1: 基础查询
    where_clause = Column(Boolean, default=False)                           # 知识点2: 条件查询
    aggregation = Column(Boolean, default=False)                            # 知识点3: 聚合函数
    group_by = Column(Boolean, default=False)                               # 知识点4: 分组查询
    order_by = Column(Boolean, default=False)                               # 知识点5: 排序查询
    limit_clause = Column(Boolean, default=False)                           # 知识点6: 分页查询
    joins = Column(Boolean, default=False)                                  # 知识点7: 多表连接
    subqueries = Column(Boolean, default=False)                             # 知识点8: 子查询
    null_handling = Column(Boolean, default=False)                          # 知识点9: NULL处理
    execution_order = Column(Boolean, default=False)                        # 知识点10: 执行顺序
    order_sensitive = Column(Boolean, default=False)                        # 顺序敏感标识
    schema_id = Column(String, ForeignKey("sample_schemas.schema_id"))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    
    schema = relationship("SampleSchema")

class Attempt(Base):
    __tablename__ = "attempts"
    
    attempt_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id"))
    question_id = Column(String, ForeignKey("questions.question_id"))
    student_sql = Column(Text)
    is_correct = Column(Boolean)
    error_type = Column(String)
    submitted_at = Column(DateTime)
    
    user = relationship("User")
    question = relationship("Question")