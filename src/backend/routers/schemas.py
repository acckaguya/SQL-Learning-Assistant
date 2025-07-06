from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.backend import crud, schemas
from src.backend.database import get_db
from src.backend.security import get_current_user

router = APIRouter()

@router.post("/create", response_model=schemas.SampleSchema)
def create_sample_schema(
    schema: schemas.SampleSchemaCreate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user)
):
    # 只有教师可以创建数据库模式
    if current_user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有教师可以创建数据库模式"
        )
    try:
        return crud.create_schema(db, schema)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/get/schemas", response_model=list[schemas.SampleSchema])
def get_sample_schemas(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return crud.get_schemas(db, skip=skip, limit=limit)

@router.get("/get/{schema_id}", response_model=schemas.SampleSchema)
def get_sample_schema(
    schema_id: str,
    db: Session = Depends(get_db)
):
    schema = crud.get_schema(db, schema_id)
    if not schema:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="数据库模式未找到"
        )
    return schema

@router.put("/update/{schema_id}", response_model=schemas.SampleSchema)
def update_sample_schema(
    schema_id: str,
    schema: schemas.SampleSchemaUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user)
):
    if current_user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有教师可以更新数据库模式"
        )
    return crud.update_schema(db, schema_id, schema)


@router.delete("/delete/{schema_id}", response_model=schemas.SampleSchema)
def delete_sample_schema(
        schema_id: str,
        db: Session = Depends(get_db),
        current_user: schemas.User = Depends(get_current_user)
):
    """删除数据库模式（教师权限）"""
    if current_user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有教师可以删除数据库模式"
        )

    # 调用CRUD操作删除模式
    try:
        deleted_schema = crud.delete_schema(db, schema_id)
        if not deleted_schema:
            raise HTTPException(status_code=404, detail="数据库模式未找到")
        return deleted_schema
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"删除失败: {str(e)}"
        )