from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from src.backend import crud, schemas, llm_utils
from src.backend.database import get_db
from src.backend.security import get_current_user
from src.backend.config import settings
import src.backend.models as models

router = APIRouter()


@router.post("/generate", response_model=schemas.Question)
def generate_question(
        request_data: dict,  # 接收JSON请求体
        db: Session = Depends(get_db),
        current_user: schemas.User = Depends(get_current_user)
):

    # 权限验证
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="只有教师可以生成题目")

    # 参数提取与验证
    knowledge_points = request_data.get("knowledge_points", [])
    schema_id = request_data.get("schema_id")
    if not knowledge_points or not schema_id:
        raise HTTPException(status_code=400, detail="缺少必要参数: knowledge_point或schema_id")

    # 知识点有效性检查
    valid_points = ["basic_query", "where_clause", "aggregation", "group_by",
                    "order_by", "limit_clause", "joins", "subqueries",
                    "null_handling", "execution_order"]
    for point in knowledge_points:
        if point not in valid_points:
            raise HTTPException(400, detail=f"无效的知识点: {point}")

    # 获取数据库模式
    schema = crud.get_schema(db, schema_id)
    if not schema:
        raise HTTPException(status_code=404, detail="数据库模式未找到")

    # 调用LLM生成题目
    llm_helper = llm_utils.LLMHelper(settings.OPENAI_API_KEY, settings.MODEL_BASE_URL)
    try:
        generated = llm_helper.generate_question(
            str(schema.schema_definition),
            knowledge_points  # 传递列表而非单个知识点
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM生成失败: {str(e)}")

    # 创建题目并关联知识点
    question_data = {
        "question_title": generated['question_title'],
        "description": generated['description'],
        "answer_sql": generated['answer_sql'],
        "schema_id": schema_id,
        **{point: True for point in knowledge_points}
    }
    return crud.create_question(db, schemas.QuestionCreate(**question_data))

@router.get("/get")
def get_questions(
    point: str = None,
    db: Session = Depends(get_db)
):
    if point:
        # 知识点白名单检查
        valid_points = [
            "basic_query", "where_clause", "aggregation", "group_by",
            "order_by", "limit_clause", "joins", "subqueries",
            "null_handling", "execution_order"
        ]
        if point not in valid_points:
            raise HTTPException(400, "无效的知识点")
        return crud.get_questions_by_knowledge_point(db, point)
    return crud.get_questions(db)

# 根据question_id查找question
@router.get("/get/{question_id}", response_model=schemas.Question)
def get_question_by_is(
        db: Session = Depends(get_db),
        question_id: str = None
):
    return crud.get_question(db, question_id)


@router.get("/get/random", response_model=schemas.Question)
def get_random_question(
    point: str = None,  # 参数名改为point，类型为str
    db: Session = Depends(get_db)
):
    return crud.get_random_question(db, point)  # 传递知识点名称


@router.post("/get/batch", response_model=List[schemas.Question])
def get_questions_batch(
        question_ids: list[str],
        db: Session = Depends(get_db)
):
    # 1. 安全处理空值
    if not question_ids:
        return []

    # 3. 查询数据库
    questions = db.query(models.Question).filter(
        models.Question.question_id.in_(question_ids)
    ).all()

    # 4. 转换为Pydantic模型
    return [
        schemas.Question(
            question_id=q.question_id,
            question_title=q.question_title,
            description=q.description,
            answer_sql=q.answer_sql,
            basic_query=q.basic_query,
            where_clause=q.where_clause,
            aggregation=q.aggregation,
            group_by=q.group_by,
            order_by=q.order_by,
            limit_clause=q.limit_clause,
            joins=q.joins,
            subqueries=q.subqueries,
            null_handling=q.null_handling,
            execution_order=q.execution_order,
            order_sensitive=q.order_sensitive,
            schema_id=q.schema_id,
            created_at=q.created_at,
            updated_at=q.updated_at
        ) for q in questions
    ]

@router.put("/update/{question_id}", response_model=schemas.Question)
def update_question(
    question_id: str,
    question: schemas.QuestionCreate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user)
):
    if current_user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有教师可以修改题目"
        )
    return crud.update_question(db, question_id, question)

@router.delete("/{question_id}", response_model=schemas.Question)
def delete_question(
    question_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user)
):
    if current_user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,  # 修复3
            detail="只有教师可以删除题目"
        )
    return crud.delete_question(db, question_id)