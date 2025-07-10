import logging
import sqlparse
from sql_metadata import Parser
from sqlalchemy import create_engine, text, exc
from src.schemas import SQLValidationResult
from src.config import settings
from decimal import Decimal


def convert_result_to_str(result, columns=None):
    """
    将SQL查询结果转换为易读的字符串
    参数：
        result：行列表
        columns：列名
    返回：
        str：结果字符串
    """
    if not result:
        return "空结果集"

        # 转换列名
    if columns:
        header = " | ".join(columns) + "\n"
        header += "-" * (len(" | ".join(columns)) + 5) + "\n"
    else:
        header = ""

        # 转换行数据
    rows = []
    for row in result:
        # 处理Row对象或元组
        if hasattr(row, '_asdict'):
            row_data = [str(v) if v is not None else "NULL" for v in row]
        else:  # 如果是普通元组
            row_data = [str(v) if v is not None else "NULL" for v in row]

        rows.append(" | ".join(row_data))

    return header + "\n".join(rows)