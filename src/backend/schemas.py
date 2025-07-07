"""
定义了一些列Pydantic模型，用于处理数据验证和序列化
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel





class UserBase(BaseModel):
    """用户基类"""
    username: str

class UserCreate(UserBase):
    """用户创建"""
    password: str
    role: str  # 两种角色："teacher" or "student"


class UserLogin(BaseModel):
    """用户登录"""
    username: str
    password: str

class User(UserBase):
    """用户"""
    user_id: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True





class SampleSchemaBase(BaseModel):
    """样例模式基类"""
    schema_name: str                        # 模式名称
    schema_definition: dict                 # 用JSON定义的模式描述
    init_sql: Optional[str] = ""            # 模式初始sql语句

class SampleSchemaCreate(SampleSchemaBase):
    """创建样例模式"""
    pass

class SampleSchemaUpdate(BaseModel):
    """更新样例模式"""
    schema_name: Optional[str] = None
    schema_definition: Optional[dict] = None
    schema_sql: Optional[str] = None

class SampleSchema(SampleSchemaBase):
    """样例模式"""
    schema_id: str
    created_at: datetime

    class Config:
        from_attributes = True

class QuestionBase(BaseModel):
    """问题基类"""
    description: str                        # 问题描述
    answer_sql: str                         # 问题参考答案
    basic_query: bool = False               # 从此处开始往下为知识点tag
    where_clause: bool = False
    aggregation: bool = False
    group_by: bool = False
    order_by: bool = False
    limit_clause: bool = False
    joins: bool = False
    subqueries: bool = False
    null_handling: bool = False
    execution_order: bool = False           # 从此处往上为知识点tag
    order_sensitive: bool = False           # 是否顺序敏感，用于后续判断sql语句结果对错
    schema_id: str                          # 问题对应的样例模式的id

class QuestionCreate(QuestionBase):
    """创建问题"""
    pass

class Question(QuestionBase):
    """问题"""
    question_id: str                        # 问题id
    created_at: datetime                    # 问腿创建时间
    updated_at: datetime                    # 问题更新时间

    class Config:
        from_attributes = True





class AttemptBase(BaseModel):
    """用户每一次提交的答案（练习）的基类"""
    student_sql: str                        # 提交的sql
    is_correct: bool                        # 该次尝试是否正确
    error_type: Optional[str] = None        # 错误类型
    error_analysis: Optional[str] = None    # 错误分析

class AttemptSubmit(BaseModel):
    """提交答案（练习）"""
    student_sql: str                        # 提交的sql
    question_id: str                        # 问题id

class AttemptCreate(AttemptBase):
    """创建答案（练习）"""
    user_id: str                            # 用户id
    question_id: str                        # 问题id

class Attempt(AttemptBase):
    """答案（练习）类"""
    attempt_id: str                         # id
    question_id: str                        # 问题id
    user_id: str                            # 用户id
    submitted_at: datetime                  # 提交时间

    class Config:
        from_attributes = True





class SQLValidationResult(BaseModel):
    """提交的sql验证结果类"""
    is_correct: bool                        # 是否正确
    error_type: Optional[str] = None        # 错误类型
    result_diff: Optional[str] = None       # 差异