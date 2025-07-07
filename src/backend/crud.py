"""
数据库访问对象层，包含用户管理、模式管理、题目管理和练习管理等模块
"""
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.backend import models, schemas
from datetime import datetime
import uuid
import sqlparse
import random





# 用户管理模块
def get_user_by_username(db: Session, username: str):
    """
    通过用户名返回用户
    参数：
        db: 数据库会话
        username: 用户名称
    返回：
        models.User: 用户实例
    """
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate, hash_func):
    """
    创建新用户
    参数：
        db：数据库会话
        user：用户创建类，包含用户名、密码和角色
    返回:
        models.User: 用户实例
    """
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





# 模式管理模块
def execute_sql_with_current_connection(db: Session, sql_statements: str):
    """
    在当前链接上执行sql语句
    参数：
        db：数据库
        sql_statements：要执行的sql语句
    返回：
        元组（是否执行成功，错误消息）
    """
    try:
        for statement in sqlparse.split(sql_statements):  # 使用sqlparse智能分割
            if statement.strip():
                db.execute(text(statement))
        return True, None
    except Exception as e:
        return False, str(e)

def create_schema(db: Session, schema: schemas.SampleSchemaCreate):
    """
    创建模式
    参数：
        db：数据库
        schema：模式创建类包含模式名称、模式定义和初始化模式的sql语句
    返回：
        models.SampleSchema：模式实例
    """
    try:
        db_schema = models.SampleSchema(
            schema_id=str(uuid.uuid4()),
            schema_name=schema.schema_name,
            schema_definition=schema.schema_definition,
            init_sql=schema.init_sql,
            created_at=datetime.now()
        )
        db.add(db_schema)

        if schema.init_sql:
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
    """
    根据模式id获得模式定义
    参数：
        db：数据库
        schema_id：模式id
    返回：
        models.SampleSchema：模式实例
    """
    return db.query(models.SampleSchema).filter(models.SampleSchema.schema_id == schema_id).first()

def update_schema(db: Session, schema_id: str, schema: schemas.SampleSchemaUpdate):
    """
    根据模式id和模式更新类进行模式更新
    参数：
        db：数据库
        schema_id：模式id
        schema：新的模式信息，模式更新类SampleSchemaUpdate
    返回：
        models.SampleSchema：更新后的模式实例
    """
    db_schema = db.query(models.SampleSchema).filter(models.SampleSchema.schema_id == schema_id).first()
    if db_schema:
        for key, value in schema.dict().items():
            setattr(db_schema, key, value)
        db.commit()
        db.refresh(db_schema)
    return db_schema

def delete_schema(db: Session, schema_id: str):
    """
    根据模式id删除指定模式
    参数：
        db：数据库Session
        schema_id：模式id
    返回：
        models.SampleSchema or None
    """
    schema = db.query(models.SampleSchema).filter(models.SampleSchema.schema_id == schema_id).first()
    if not schema:
        return None

    try:
        #删除模式信息的同时删除创建的模式
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

def get_schemas(db: Session, skip: int = 0, limit: int = 100):
    """
    返回所有的模式
    参数：
        db：数据库
        skip：
        limit：上限
    返回：
        list[models.SampleSchema]模式实例列表
    """
    return db.query(models.SampleSchema).offset(skip).limit(limit).all()






# 题目管理模块
def create_question(db: Session, question: schemas.QuestionCreate):
    """
    创建题目
    参数：
        db：数据库
        question：题目创建类（schemas.QuestionCreate）
    返回：
        models.Question：题目实例
    """
    db_question = models.Question(
        question_id=str(uuid.uuid4()),
        question_title=question.question_title,
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
    """
    根据question_id获取题目定义
    参数：
        db：数据库
        question_id：问题id
    返回：
        models.Question：问题实例
    """
    return db.query(models.Question).filter(models.Question.question_id == question_id).first()

def update_question(db: Session, question_id: str, question: schemas.QuestionCreate):
    """
    根据题目id和题目类进行题目更新
    参数：
        db：数据库
        question_id：题目id
        question：题目类
    返回：
        models.Question：更新后的题目实例
    """
    db_question = db.query(models.Question).filter(models.Question.question_id == question_id).first()
    if db_question:
        for key, value in question.dict().items():
            setattr(db_question, key, value)
        db_question.updated_at = datetime.now()
        db.commit()
        db.refresh(db_question)
    return db_question

def get_questions_by_knowledge_point(db: Session, point_name: str):
    """
    根据具体知识点名称查询题目
    参数：
        db：数据库
        point_name：知识点名称
    返回：
        models.Question：题目实例
    """
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
    """
    根据知识点随机获得题目（暂时弃用）
    参数：
        db：数据库
        point_name：知识点名称
    返回：
        models.Question：题目实例
    """
    query = db.query(models.Question)

    if point_name is not None:
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

def get_questions(db: Session, skip: int = 0, limit: int = 100):
    """
    获得题目列表
    参数：
        db：数据库
        skip：
        limit：限制
    返回：
        list[models.Question]：题目列表
    """
    return db.query(models.Question).offset(skip).limit(limit).all()

def delete_question(db: Session, question_id: str):
    """
    删除指定question_id的题目
    参数：
        db：数据库
        question_id：题目id
    返回：
        models.Question or None
    """
    question = db.query(models.Question).filter(models.Question.question_id == question_id).first()
    if question:
        db.delete(question)
        db.commit()
    return question





# 练习管理模块
def create_attempt(db: Session, attempt: schemas.AttemptCreate):
    """
    创建练习
    参数：
        db：数据库
        attempt：创建练习类
    返回：
        models.Schema：练习实例
    """
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
    """
    获得指定user的所有练习
    参数：
        db：数据库
        user_id：用户id
    返回：
        list[models.Attempt]：练习实例列表
    """
    return db.query(models.Attempt).filter(models.Attempt.user_id == user_id).order_by(models.Attempt.submitted_at.desc()).all()

def get_user_mistake_questions(db: Session, user_id: str):
    """
    获取用户的所有错题
    参数：
        db：数据库
        user_id：用户id
    返回：
        list[models.Attempt]：练习实例列表
    """
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
    """
    获取所有错题
    参数：
        db：数据库
    返回：
        list[models.Attempt]：练习实例列表
    """
    mistake_question_ids = db.query(models.Attempt.question_id).filter(
        models.Attempt.is_correct == False
    ).distinct().all()
    
    # 提取题目ID
    question_ids = [q[0] for q in mistake_question_ids]
    
    # 获取题目详情
    return db.query(models.Question).filter(
        models.Question.question_id.in_(question_ids)
    ).all()

def get_attempts_by_question_and_user(db: Session, question_id: str, user_id: str, is_correct: bool = False) -> List[models.Attempt]:
    """
    获取用户对特定题目的尝试记录（默认只返回错误尝试）
    参数：
        db：数据库
        question_id：题目id
        user_id：用户id
    返回：
        list[models.Attempt]：练习实例列表
    """
    query = db.query(models.Attempt).filter(
        models.Attempt.question_id == question_id,
        models.Attempt.user_id == user_id
    )

    if is_correct is not None:
        query = query.filter(models.Attempt.is_correct == is_correct)

    return query.order_by(models.Attempt.submitted_at.desc()).all()