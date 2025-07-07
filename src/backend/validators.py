import logging
import pandas as pd
import sqlparse
from sql_metadata import Parser
from sqlalchemy import create_engine, text, exc
from src.backend.schemas import SQLValidationResult
from src.backend.config import settings

logger = logging.getLogger(__name__)


def validate_sql(
        student_sql: str,
        answer_sql: str,
        schema_definition: dict,
        schema_name: str,
        order_sensitive: bool
) -> SQLValidationResult:
    detailed_errors = []

    # 1. 语法检测
    try:
        parsed_student = sqlparse.parse(student_sql)
        if not parsed_student:
            detailed_errors.append({
                "error_type": "syntax_error",
                "message": "无法解析SQL语句"
            })
            return SQLValidationResult(
                is_correct=False,
                error_type="syntax_error",
                detailed_errors=detailed_errors
            )

        # 检查是否为SELECT语句（安全性检查）
        first_token = parsed_student[0].tokens[0].value.upper()
        if first_token != "SELECT":
            detailed_errors.append({
                "error_type": "security_error",
                "message": "非法的非查询语句",
                "details": "只允许SELECT查询语句"
            })
    except Exception as e:
        detailed_errors.append({
            "error_type": "syntax_error",
            "message": f"语法解析错误: {str(e)}"
        })
        logger.error(f"SQL语法解析错误: {str(e)}")
        return SQLValidationResult(
            is_correct=False,
            error_type="syntax_error",
            detailed_errors=detailed_errors
        )

    # 2. 语义检测
    try:
        # 提取可用表和列信息
        table_details = {}
        for table in schema_definition.get("tables", []):
            full_name = table["name"]
            simple_name = full_name.split('.')[-1]
            table_details[full_name] = table
            table_details[simple_name] = table
            table_details[simple_name + "_columns"] = [col["name"] for col in table.get("columns", [])]
            table_details[full_name + "_columns"] = [col["name"] for col in table.get("columns", [])]

        parser = Parser(student_sql)

        # 表验证
        invalid_tables = []
        for table in set(parser.tables):
            if '.' in table:
                schema_part, table_part = table.split('.', 1)
                if schema_part != schema_name:
                    invalid_tables.append({
                        "table": table,
                        "reason": f"模式不匹配: '{schema_part}' ≠ '{schema_name}'"
                    })
                elif table_part not in table_details:
                    invalid_tables.append({
                        "table": table,
                        "reason": f"表不存在: '{table_part}'"
                    })
            elif table not in table_details:
                invalid_tables.append({
                    "table": table,
                    "reason": f"表不存在: '{table}'"
                })

        if invalid_tables:
            detailed_errors.append({
                "error_type": "semantic_error",
                "message": "表验证失败",
                "invalid_tables": invalid_tables
            })

        # 列验证
        invalid_columns = []
        referenced_tables = set()
        for column_ref in parser.columns:
            if '.' in column_ref:
                table_part, column_name = column_ref.split('.', 1)
                referenced_tables.add(table_part)
                if table_part not in table_details:
                    invalid_columns.append({
                        "column": column_ref,
                        "reason": f"关联表不存在: '{table_part}'"
                    })
                elif column_name not in table_details[table_part + "_columns"]:
                    invalid_columns.append({
                        "column": column_ref,
                        "reason": f"列不存在: '{table_part}.{column_name}'"
                    })
            else:
                column_found = False
                for table_name in referenced_tables:
                    if column_ref in table_details.get(table_name + "_columns", []):
                        column_found = True
                        break
                if not column_found:
                    invalid_columns.append({
                        "column": column_ref,
                        "reason": "歧义的列引用",
                        "suggestion": "请使用表名前缀明确指定列"
                    })

        if invalid_columns:
            detailed_errors.append({
                "error_type": "semantic_error",
                "message": "列验证失败",
                "invalid_columns": invalid_columns
            })

        if detailed_errors:
            return SQLValidationResult(
                is_correct=False,
                error_type="semantic_error",
                detailed_errors=detailed_errors
            )
    except Exception as e:
        detailed_errors.append({
            "error_type": "semantic_error",
            "message": f"语义验证异常: {str(e)}"
        })
        logger.error(f"SQL语义验证异常: {str(e)}", exc_info=True)
        return SQLValidationResult(
            is_correct=False,
            error_type="semantic_error",
            detailed_errors=detailed_errors
        )

    # 3. 执行验证
    engine = create_engine(settings.DATABASE_URL)
    try:
        with engine.connect() as conn:
            # 设置当前schema
            try:
                conn.execute(text(f"SET search_path TO {schema_name}"))
            except Exception as e:
                detailed_errors.append({
                    "error_type": "runtime_error",
                    "message": f"设置搜索路径失败: {str(e)}"
                })
                return SQLValidationResult(
                    is_correct=False,
                    error_type="runtime_error",
                    detailed_errors=detailed_errors
                )

            # 执行学生SQL
            try:
                student_result = conn.execute(text(student_sql)).fetchall()
                student_columns = list(conn.execute(text(student_sql)).keys())
            except Exception as e:
                detailed_errors.append({
                    "error_type": "execution_error",
                    "message": "学生SQL执行失败",
                    "sql": student_sql,
                    "error": str(e)
                })
                return SQLValidationResult(
                    is_correct=False,
                    error_type="execution_error",
                    detailed_errors=detailed_errors
                )

            # 执行参考答案SQL
            try:
                answer_result = conn.execute(text(answer_sql)).fetchall()
                answer_columns = list(conn.execute(text(answer_sql)).keys())
            except Exception as e:
                detailed_errors.append({
                    "error_type": "execution_error",
                    "message": "参考答案SQL执行失败",
                    "sql": answer_sql,
                    "error": str(e)
                })
                return SQLValidationResult(
                    is_correct=False,
                    error_type="execution_error",
                    detailed_errors=detailed_errors
                )

            # 列结构检查
            if student_columns != answer_columns:
                detailed_errors.append({
                    "error_type": "result_mismatch",
                    "message": "结果列不匹配",
                    "student_columns": student_columns,
                    "answer_columns": answer_columns
                })

            # 顺序敏感查询的验证
            if order_sensitive:
                if len(student_result) != len(answer_result):
                    detailed_errors.append({
                        "error_type": "result_mismatch",
                        "message": "结果行数不同",
                        "student_rows": len(student_result),
                        "answer_rows": len(answer_result)
                    })

                # 逐行比较
                mismatch_details = []
                min_rows = min(len(student_result), len(answer_result))
                for i in range(min_rows):
                    student_row = student_result[i]
                    answer_row = answer_result[i]

                    if len(student_row) != len(answer_row):
                        mismatch_details.append({
                            "row": i + 1,
                            "status": "列数不匹配",
                            "student_columns": len(student_row),
                            "answer_columns": len(answer_row)
                        })
                        continue

                    row_diff = []
                    for j in range(len(student_row)):
                        if student_row[j] != answer_row[j]:
                            row_diff.append({
                                "column": student_columns[j],
                                "student_value": student_row[j],
                                "answer_value": answer_row[j]
                            })

                    if row_diff:
                        mismatch_details.append({
                            "row": i + 1,
                            "status": "行数据不匹配",
                            "differences": row_diff
                        })

                if mismatch_details:
                    detailed_errors.append({
                        "error_type": "result_mismatch",
                        "message": "顺序敏感模式结果不匹配",
                        "comparison_details": mismatch_details
                    })

            # 顺序不敏感查询的验证
            else:
                # 使用集合操作验证结果
                try:
                    # 创建临时视图
                    conn.execute(text(f"""
                        CREATE TEMPORARY VIEW student_results AS {student_sql};
                        CREATE TEMPORARY VIEW answer_results AS {answer_sql};
                    """))

                    # 检查差异
                    diff_result = conn.execute(text("""
                        (SELECT * FROM student_results EXCEPT SELECT * FROM answer_results)
                        UNION ALL
                        (SELECT * FROM answer_results EXCEPT SELECT * FROM student_results)
                    """)).fetchall()

                    if diff_result:
                        detailed_errors.append({
                            "error_type": "result_mismatch",
                            "message": "顺序不敏感模式结果不匹配",
                            "differences": diff_result,
                            "difference_count": len(diff_result)
                        })
                except Exception as e:
                    detailed_errors.append({
                        "error_type": "comparison_error",
                        "message": "结果比较失败",
                        "error": str(e)
                    })

            # 最终结果判断
            if not detailed_errors:
                return SQLValidationResult(is_correct=True)
            else:
                return SQLValidationResult(
                    is_correct=False,
                    error_type="result_mismatch",
                    detailed_errors=detailed_errors
                )

    except Exception as e:
        detailed_errors.append({
            "error_type": "runtime_error",
            "message": "执行期间发生意外错误",
            "error": str(e)
        })
        logger.error(f"SQL验证异常: {str(e)}", exc_info=True)
        return SQLValidationResult(
            is_correct=False,
            error_type="runtime_error",
            detailed_errors=detailed_errors
        )