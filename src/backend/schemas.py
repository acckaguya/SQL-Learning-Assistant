from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str
    role: str  # "teacher" or "student"


class UserLogin(BaseModel):
    username: str
    password: str

class User(UserBase):
    user_id: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

class SampleSchemaBase(BaseModel):
    schema_name: str
    schema_definition: dict  # JSON格式
    init_sql: Optional[str] = ""

class SampleSchemaCreate(SampleSchemaBase):
    pass

class SampleSchemaUpdate(BaseModel):
    schema_name: Optional[str] = None
    schema_definition: Optional[dict] = None
    schema_sql: Optional[str] = None

class SampleSchema(SampleSchemaBase):
    schema_id: str
    created_at: datetime

    class Config:
        from_attributes = True

class QuestionBase(BaseModel):
    description: str
    answer_sql: str
    basic_query: bool = False
    where_clause: bool = False
    aggregation: bool = False
    group_by: bool = False
    order_by: bool = False
    limit_clause: bool = False
    joins: bool = False
    subqueries: bool = False
    null_handling: bool = False
    execution_order: bool = False
    order_sensitive: bool = False
    schema_id: str

class QuestionCreate(QuestionBase):
    pass

class Question(QuestionBase):
    question_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AttemptBase(BaseModel):
    student_sql: str
    is_correct: bool
    error_type: Optional[str] = None
    error_analysis: Optional[str] = None

class AttemptSubmit(BaseModel):  # 专用提交模型
    student_sql: str
    question_id: str

class AttemptCreate(AttemptBase):
    user_id: str
    question_id: str

class Attempt(AttemptBase):
    attempt_id: str
    question_id: str
    user_id: str
    submitted_at: datetime

    class Config:
        from_attributes = True

class SQLValidationResult(BaseModel):
    is_correct: bool
    error_type: Optional[str] = None
    result_diff: Optional[str] = None