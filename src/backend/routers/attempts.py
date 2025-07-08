from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from src.backend import crud, schemas, validators
from src.backend.database import get_db
from src.backend.security import get_current_user


router = APIRouter()

# 提交答案
@router.post("/submit", response_model=schemas.Attempt)
def submit_answer(
        attempt_submit: schemas.AttemptSubmit,
        db: Session = Depends(get_db),
        current_user: schemas.User = Depends(get_current_user)
):
    question = crud.get_question(db, attempt_submit.question_id)
    schema = crud.get_schema(db, question.schema_id)

    validation_result = validators.validate_sql(
        student_sql=attempt_submit.student_sql,
        answer_sql=question.answer_sql,
        schema_definition=schema.schema_definition,
        schema_name=schema.schema_name,
        order_sensitive=question.order_sensitive
    )

    # 创建练习记录
    db_attempt = crud.create_attempt(db, schemas.AttemptCreate(
        user_id=current_user.user_id,
        question_id=attempt_submit.question_id,
        student_sql=attempt_submit.student_sql,
        is_correct=validation_result.is_correct,
        error_type=validation_result.error_type,
        detailed_errors=validation_result.detailed_errors
    ))
    return db_attempt

# 获取练习历史
@router.get("/history", response_model=List[schemas.Attempt])
def get_attempt_history(
    user_id: str = None,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user)
):
    # 学生只能查看自己的历史
    if current_user.role == "student":
        user_id = current_user.user_id
    return crud.get_user_attempts(db, user_id)

@router.get("/all_history", response_model=List[schemas.AttemptWithUser])
def get_all_history(
        db: Session = Depends(get_db),
        current_user: schemas.User = Depends(get_current_user)
):
    if current_user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有教师可以获取所有练习历史"
        )
    attempts = crud.get_all_attempts(db)
    return [{
        "student_sql": a.student_sql,
        "is_correct": a.is_correct,
        "error_type": a.error_type,
        "detailed_errors": a.detailed_errors,
        "attempt_id": a.attempt_id,
        "question_id": a.question_id,
        "user_id": a.user_id,
        "submitted_at": a.submitted_at,
        "username": u
    } for a, u in attempts]

# 获取错题本
@router.get("/mistakes", response_model=list[schemas.Question])
def get_mistake_questions(
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user)
):
    # 学生只能查看自己的错题
    if current_user.role == "student":
        return crud.get_user_mistake_questions(db, current_user.user_id)
    
    # 教师可以查看所有错题
    return crud.get_all_mistake_questions(db)

@router.get("/by_question/{question_id}", response_model=List[schemas.Attempt])
def get_attempts_by_question(
    question_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user)
):
    """
    获取当前用户对指定题目的所有尝试记录
    """
    return crud.get_attempts_by_question_and_user(
        db,
        question_id=question_id,
        user_id=current_user.user_id
    )