"""
数据库的四个表的定义
"""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from src.backend.database import Base

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(String, primary_key=True, index=True)                  # 用户id（主码），自动生成
    username = Column(String, unique=True, index=True)                      # 用户名
    password_hash = Column(String)                                          # 密码
    role = Column(String)                                                   # 用户角色："teacher" or "student"
    created_at = Column(DateTime)                                           # 创建时间

class SampleSchema(Base):
    __tablename__ = "sample_schemas"
    
    schema_id = Column(String, primary_key=True, index=True)                # 模式id（主码），自动生成
    schema_name = Column(String)                                            # 模式名称
    schema_definition = Column(JSONB)                                       # 模式定义
    init_sql = Column(String)                                               # 初始化模式的sql语句
    created_at = Column(DateTime)                                           # 创建时间


class Question(Base):
    __tablename__ = "questions"

    question_id = Column(String, primary_key=True, index=True)              # 问题id（主码），自动生成
    question_title = Column(Text)                                           # 题目标题
    description = Column(Text)                                              # 问题描述
    answer_sql = Column(Text)                                               # 参考答案
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
    schema_id = Column(String, ForeignKey("sample_schemas.schema_id"))      # 关联的模式id
    created_at = Column(DateTime)                                           # 创建时间
    updated_at = Column(DateTime)                                           # 更新时间
    
    schema = relationship("SampleSchema")                                   # 关联SampleSchema表

class Attempt(Base):
    __tablename__ = "attempts"
    
    attempt_id = Column(String, primary_key=True, index=True)               # attemptid（主码），自动生成
    user_id = Column(String, ForeignKey("users.user_id"))                   # 用户id
    question_id = Column(String, ForeignKey("questions.question_id"))       # 问题id
    student_sql = Column(Text)                                              # 用户提交的sql语句
    is_correct = Column(Boolean)                                            # 是否正确
    error_type = Column(String)                                             # 错误类型
    submitted_at = Column(DateTime)                                         # 提交日期
    detailed_errors = Column(JSONB)                                         # 详细错误信息

    user = relationship("User")                                             # 关联User
    question = relationship("Question")                                     # 关联Question