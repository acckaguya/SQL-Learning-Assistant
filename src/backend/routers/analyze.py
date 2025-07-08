from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from src.backend import crud, llm_utils
from src.backend.database import get_db
from src.backend.config import settings
from src.backend import schemas
from src.backend.utils import convert_result_to_str

router = APIRouter()

@router.post("/sql")
def analyze_sql(
    attempt: schemas.Attempt,
    db: Session = Depends(get_db),
):
    # 获取题目
    question = crud.get_question(db, attempt.question_id)
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")

    # 获取数据库模式
    schema = crud.get_schema(db, question.schema_id)
    if not schema:
        raise HTTPException(status_code=404, detail="数据库模式未找到")

    # 执行sql获得str结果
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        conn.execute(text(f"SET search_path TO {schema.schema_name}"))
        # 获得用户提交sql的str结果
        student_result = conn.execute(text(attempt.student_sql)).fetchall()
        student_columns = list(conn.execute(text(attempt.student_sql)).keys())
        student_result_str = convert_result_to_str(student_result, student_columns)

        # 获得参考答案sql的str结果
        answer_result = conn.execute(text(question.answer_sql)).fetchall()
        answer_columns = list(conn.execute(text(question.answer_sql)).keys())
        answer_result_str = convert_result_to_str(answer_result, answer_columns)


    # 初始化LLMHelper
    llm_helper = llm_utils.LLMHelper(settings.OPENAI_API_KEY, settings.MODEL_BASE_URL)

    # 调用LLM进行分析
    analysis_result = llm_helper.analyze_sql(
        question_description=str(question.description),
        schema_definition=str(schema.schema_definition),
        student_sql=attempt.student_sql,
        answer_sql=question.answer_sql,
        student_result=student_result_str,
        answer_result=answer_result_str,
        is_correct=attempt.is_correct
    )

    return analysis_result