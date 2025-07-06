import pandas as pd
import sqlparse
from sql_metadata import Parser
from src.backend.schemas import SQLValidationResult
from sqlalchemy import create_engine, text
from src.backend.config import settings


def validate_sql(
        student_sql: str,
        answer_sql: str,
        schema_definition: dict,
        schema_name: str,
        order_sensitive: bool
) -> SQLValidationResult:
    # 1. 语法验证
    try:
        parsed_student = sqlparse.parse(student_sql)
        if not parsed_student:
            return SQLValidationResult(is_correct=False, error_type="syntax_error")
    except Exception:
        return SQLValidationResult(is_correct=False, error_type="syntax_error")

    # 2. 语义验证
    try:
        student_tables = Parser(student_sql).tables
        student_columns = Parser(student_sql).columns

        available_tables = [table["name"] for table in schema_definition.get("tables", [])]
        for table in student_tables:
            if table not in available_tables:
                return SQLValidationResult(
                    is_correct=False,
                    error_type="logic_error",
                    result_diff=f"表 '{table}' 不存在"
                )

        available_columns = {}
        for table in schema_definition.get("tables", []):
            for col in table.get("columns", []):
                available_columns[col["name"]] = table["name"]

        for col in student_columns:
            if col not in available_columns:
                return SQLValidationResult(
                    is_correct=False,
                    error_type="logic_error",
                    result_diff=f"列 '{col}' 不存在"
                )
    except Exception as e:
        return SQLValidationResult(is_correct=False, error_type="logic_error", result_diff=str(e))

    # 3. 结果验证（实际执行）
    try:
        # 创建到目标数据库的连接
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            # 设置当前schema
            conn.execute(text(f"SET search_path TO {schema_name}"))

            # 执行学生SQL
            student_result = conn.execute(text(student_sql)).fetchall()

            # 执行参考答案SQL
            answer_result = conn.execute(text(answer_sql)).fetchall()

            # 检查列是否匹配
            student_columns = [col for col in conn.execute(text(student_sql)).keys()]
            answer_columns = [col for col in conn.execute(text(answer_sql)).keys()]

            if student_columns != answer_columns:
                return SQLValidationResult(
                    is_correct=False,
                    error_type="result_mismatch",
                    result_diff=f"结果列不匹配: 学生返回{student_columns}, 参考答案{answer_columns}"
                )

            # 根据顺序敏感标志选择验证方式
            if order_sensitive:
                # 顺序敏感：逐行比较
                if len(student_result) != len(answer_result):
                    return SQLValidationResult(
                        is_correct=False,
                        error_type="result_mismatch",
                        result_diff=f"结果行数不同: 学生返回{len(student_result)}行, 参考答案{len(answer_result)}行"
                    )

                # 转换为DataFrame进行比较
                student_df = pd.DataFrame(student_result, columns=student_columns)
                answer_df = pd.DataFrame(answer_result, columns=answer_columns)

                # 逐行比较
                diff_rows = []
                for i in range(len(answer_df)):
                    student_row = student_df.iloc[i] if i < len(student_df) else None
                    answer_row = answer_df.iloc[i]

                    if student_row is None or not student_row.equals(answer_row):
                        diff_rows.append({
                            "行号": i + 1,
                            "学生结果": student_row.values if student_row is not None else None,
                            "参考答案": answer_row.values
                        })

                if diff_rows:
                    diff_df = pd.DataFrame(diff_rows)
                    return SQLValidationResult(
                        is_correct=False,
                        error_type="result_mismatch",
                        result_diff=f"顺序敏感模式，结果差异:\n{diff_df.to_markdown(index=False)}"
                    )
            else:
                # 顺序无关：使用集合操作验证
                # 将两个结果集作为子查询进行差集运算
                set_query = f"""
                    (SELECT * FROM ({student_sql}) AS student
                    EXCEPT
                    SELECT * FROM ({answer_sql}) AS answer)
                    UNION
                    (SELECT * FROM ({answer_sql}) AS answer
                    EXCEPT
                    SELECT * FROM ({student_sql}) AS student)
                """

                diff_result = conn.execute(text(set_query)).fetchall()
                if diff_result:
                    # 转换为DataFrame进行比较
                    student_df = pd.DataFrame(student_result, columns=student_columns)
                    answer_df = pd.DataFrame(answer_result, columns=answer_columns)

                    # 使用pandas计算差异
                    merged = pd.merge(
                        student_df, answer_df,
                        how='outer', indicator=True
                    )
                    diff = merged[merged['_merge'] != 'both']

                    return SQLValidationResult(
                        is_correct=False,
                        error_type="result_mismatch",
                        result_diff=f"顺序无关模式，结果差异:\n{diff.to_markdown(index=False)}"
                    )

        return SQLValidationResult(is_correct=True)

    except Exception as e:
        return SQLValidationResult(
            is_correct=False,
            error_type="runtime_error",
            result_diff=f"执行错误: {str(e)}"
        )