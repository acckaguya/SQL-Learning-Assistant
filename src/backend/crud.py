from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.backend import models, schemas
from datetime import datetime
import uuid
import sqlparse
import random

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate, hash_func):
    db_user = models.User(
        user_id=str(uuid.uuid4()),
        username=user.username,
        password_hash=hash_func(user.password),
        role=user.role,
        created_at=datetime.now()
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def execute_sql_with_current_connection(db: Session, sql_statements: str):
    try:
        # 使用SQLAlchemy的原始连接执行
        connection = db.connection()
        for statement in sqlparse.split(sql_statements):  # 使用sqlparse智能分割
            if statement.strip():
                db.execute(text(statement))
        return True, None
    except Exception as e:
        return False, str(e)

def create_schema(db: Session, schema: schemas.SampleSchemaCreate):
    try:
        db_schema = models.SampleSchema(
            schema_id=str(uuid.uuid4()),
            schema_name=schema.schema_name,
            schema_definition=schema.schema_definition,
            init_sql=schema.init_sql,
            created_at=datetime.now()
        )
        db.add(db_schema)

        # 先不提交，保持事务
        if schema.init_sql:
            # 直接使用当前连接执行SQL
            success, error_msg = execute_sql_with_current_connection(
                db, schema.init_sql
            )
            if not success:
                raise Exception(f"初始化SQL执行失败: {error_msg}")

        db.commit()  # 所有操作成功后才提交
        db.refresh(db_schema)
        return db_schema
    except Exception as e:
        db.rollback()  # 发生异常时回滚整个事务
        raise e

def get_schema(db: Session, schema_id: str):
    return db.query(models.SampleSchema).filter(models.SampleSchema.schema_id == schema_id).first()

def update_schema(db: Session, schema_id: str, schema: schemas.SampleSchemaUpdate):
    db_schema = db.query(models.SampleSchema).filter(models.SampleSchema.schema_id == schema_id).first()
    if db_schema:
        for key, value in schema.dict().items():
            setattr(db_schema, key, value)
        db.commit()
        db.refresh(db_schema)
    return db_schema

def delete_schema(db: Session, schema_id: str):
    schema = db.query(models.SampleSchema).filter(models.SampleSchema.schema_id == schema_id).first()
    if not schema:
        return None

    try:
        #直接通过模式名删除整个数据库模式
        schema_name = schema.schema_name  # 从元数据中获取模式名
        drop_schema_sql = f"DROP SCHEMA IF EXISTS {schema_name} CASCADE;"

        #执行删除命令
        success, error_msg = execute_sql_with_current_connection(db, drop_schema_sql)
        if not success:
            raise Exception(f"模式删除失败: {error_msg}")

        #删除元数据记录
        db.delete(schema)
        db.commit()
        return schema
    except Exception as e:
        db.rollback()
        raise e

def create_question(db: Session, question: schemas.QuestionCreate):
    db_question = models.Question(
        question_id=str(uuid.uuid4()),
        description=question.description,
        answer_sql=question.answer_sql,

        basic_query=question.basic_query,
        where_clause=question.where_clause,
        aggregation=question.aggregation,
        group_by=question.group_by,
        order_by=question.order_by,
        limit_clause=question.limit_clause,
        joins=question.joins,
        subqueries=question.subqueries,
        null_handling=question.null_handling,
        execution_order=question.execution_order,
        schema_id=question.schema_id,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question

def get_question(db: Session, question_id: str):
    return db.query(models.Question).filter(models.Question.question_id == question_id).first()

def update_question(db: Session, question_id: str, question: schemas.QuestionCreate):
    db_question = db.query(models.Question).filter(models.Question.question_id == question_id).first()
    if db_question:
        for key, value in question.dict().items():
            setattr(db_question, key, value)
        db_question.updated_at = datetime.now()
        db.commit()
        db.refresh(db_question)
    return db_question

def get_questions_by_knowledge_point(db: Session, point_name: str):
    """根据具体知识点名称查询题目"""
    point_mapping = {
        "basic_query": models.Question.basic_query,
        "where_clause": models.Question.where_clause,
        "aggregation": models.Question.aggregation,
        "group_by": models.Question.group_by,
        "order_by": models.Question.order_by,
        "limit_clause": models.Question.limit_clause,
        "joins": models.Question.joins,
        "subqueries": models.Question.subqueries,
        "null_handling": models.Question.null_handling,
        "execution_order": models.Question.execution_order
    }
    if point_name in point_mapping:
        return db.query(models.Question).filter(point_mapping[point_name] == True).all()
    return None

def get_random_question(db: Session, point_name: str = None):
    query = db.query(models.Question)

    if point_name is not None:
        # 使用知识点名称直接过滤（非tag_前缀）
        point_mapping = {
            "basic_query": models.Question.basic_query,
            "where_clause": models.Question.where_clause,
            "aggregation": models.Question.aggregation,
            "group_by": models.Question.group_by,
            "order_by": models.Question.order_by,
            "limit_clause": models.Question.limit_clause,
            "joins": models.Question.joins,
            "subqueries": models.Question.subqueries,
            "null_handling": models.Question.null_handling,
            "execution_order": models.Question.execution_order
        }

        if point_name in point_mapping:
            query = query.filter(point_mapping[point_name] == True)
        else:
            # 处理无效知识点名称
            return None

    count = query.count()
    return query.offset(random.randint(0, count - 1)).first() if count > 0 else None

def create_attempt(db: Session, attempt: schemas.AttemptCreate):
    db_attempt = models.Attempt(
        attempt_id=str(uuid.uuid4()),
        user_id=attempt.user_id,
        question_id=attempt.question_id,
        student_sql=attempt.student_sql,
        is_correct=attempt.is_correct,
        error_type=attempt.error_type,
        submitted_at=datetime.now()
    )
    db.add(db_attempt)
    db.commit()
    db.refresh(db_attempt)
    return db_attempt

def get_user_attempts(db: Session, user_id: str):
    return db.query(models.Attempt).filter(models.Attempt.user_id == user_id).order_by(models.Attempt.submitted_at.desc()).all()

def get_schemas(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.SampleSchema).offset(skip).limit(limit).all()

def get_questions(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Question).offset(skip).limit(limit).all()

def delete_question(db: Session, question_id: str):
    question = db.query(models.Question).filter(models.Question.question_id == question_id).first()
    if question:
        db.delete(question)
        db.commit()
    return question

def get_user_mistake_questions(db: Session, user_id: str):
    # 获取用户的所有错题（题目ID列表）
    mistake_question_ids = db.query(models.Attempt.question_id).filter(
        models.Attempt.user_id == user_id,
        models.Attempt.is_correct == False
    ).distinct().all()
    
    # 提取题目ID
    question_ids = [q[0] for q in mistake_question_ids]
    
    # 获取题目详情
    return db.query(models.Question).filter(
        models.Question.question_id.in_(question_ids)
    ).all()

def get_all_mistake_questions(db: Session):
    # 获取所有错题（题目ID列表）
    mistake_question_ids = db.query(models.Attempt.question_id).filter(
        models.Attempt.is_correct == False
    ).distinct().all()
    
    # 提取题目ID
    question_ids = [q[0] for q in mistake_question_ids]
    
    # 获取题目详情
    return db.query(models.Question).filter(
        models.Question.question_id.in_(question_ids)
    ).all()


def get_attempts_by_question_and_user(
        db: Session,
        question_id: str,
        user_id: str,
        is_correct: bool = False
) -> List[models.Attempt]:
    """
    获取用户对特定题目的尝试记录（默认只返回错误尝试）
    """
    query = db.query(models.Attempt).filter(
        models.Attempt.question_id == question_id,
        models.Attempt.user_id == user_id
    )

    if is_correct is not None:
        query = query.filter(models.Attempt.is_correct == is_correct)

    return query.order_by(models.Attempt.submitted_at.desc()).all()