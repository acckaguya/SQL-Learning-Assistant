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
    # 初始化详细错误信息收集器
    detailed_errors = []

    # 1. 语法验证
    try:
        parsed_student = sqlparse.parse(student_sql)
        if not parsed_student:
            detailed_errors.append("语法错误：无法解析SQL语句")
            return SQLValidationResult(
                is_correct=False,
                error_type="syntax_error",
                detailed_errors=detailed_errors
            )
    except Exception as e:
        detailed_errors.append(f"语法解析错误：{str(e)}")
        logger.error(f"SQL语法解析错误: {str(e)}")
        return SQLValidationResult(
            is_correct=False,
            error_type="syntax_error",
            detailed_errors=detailed_errors
        )

    # 2. 语义验证
    try:
        # 2.1 表名验证
        available_tables = []
        table_details = {}

        for table in schema_definition.get("tables", []):
            full_name = table["name"]
            simple_name = full_name.split('.')[-1]  # 提取简单表名
            available_tables.append(full_name)
            available_tables.append(simple_name)
            table_details[full_name] = table
            table_details[simple_name] = table

            # 收集表内的所有列
            columns = [col["name"] for col in table.get("columns", [])]
            table_details[simple_name + "_columns"] = columns
            table_details[full_name + "_columns"] = columns

        parser = Parser(student_sql)
        student_tables = parser.tables
        invalid_tables = []

        for table in set(student_tables):
            if '.' in table:
                schema_part, table_part = table.split('.', 1)
                # 检查模式是否匹配
                if schema_part != schema_name:
                    invalid_tables.append({
                        "table": table,
                        "reason": f"表所在的模式 '{schema_part}' 与预期模式 '{schema_name}' 不匹配"
                    })
                # 检查表是否存在
                elif table_part not in table_details:
                    invalid_tables.append({
                        "table": table,
                        "reason": f"表 '{table_part}' 在模式 '{schema_name}' 中不存在",
                        "available_tables": [t for t in table_details.keys() if '.' not in t]
                    })
            elif table not in table_details:
                invalid_tables.append({
                    "table": table,
                    "reason": f"表 '{table}' 不存在",
                    "available_tables": list(set([t for t in table_details.keys() if '.' in t] +
                                                 [t.split('.')[-1] for t in table_details.keys() if '.' in t]))
                })

        if invalid_tables:
            detailed_errors.append({
                "message": "表验证失败",
                "invalid_tables": invalid_tables
            })

        # 2.2 列名验证
        student_columns = parser.columns
        invalid_columns = []
        referenced_tables = set()

        # 提取所有引用的表和列
        for column_ref in student_columns:
            if '.' in column_ref:
                table_part, column_name = column_ref.split('.', 1)
                referenced_tables.add(table_part)
            else:
                column_name = column_ref

        # 检查列是否存在
        for column_ref in student_columns:
            if '.' in column_ref:
                table_name, column_name = column_ref.split('.', 1)
                table = table_details.get(table_name)
                if not table:
                    invalid_columns.append({
                        "column": column_ref,
                        "reason": f"关联表 '{table_name}' 不存在",
                        "available_tables": list(referenced_tables)
                    })
                else:
                    table_columns = table.get("columns", [])
                    column_names = [col["name"] for col in table_columns]
                    if column_name not in column_names:
                        detailed_type = next((col["type"] for col in table_columns if col["name"] == column_name), None)
                        if detailed_type:
                            type_hint = f"（应使用类型 {detailed_type}）"
                        else:
                            type_hint = ""

                        invalid_columns.append({
                            "column": column_ref,
                            "reason": f"表 '{table_name}' 中不存在列 '{column_name}'{type_hint}",
                            "available_columns": column_names
                        })
            else:
                column_found = False
                # 尝试在所有引用的表中查找列
                for table_name in referenced_tables:
                    table = table_details.get(table_name)
                    if table and column_ref in [col["name"] for col in table.get("columns", [])]:
                        column_found = True
                        break

                if not column_found:
                    invalid_columns.append({
                        "column": column_ref,
                        "reason": "存在歧义的列引用",
                        "suggestion": f"请使用表名前缀（如 'table.{column_ref}'）明确指定列",
                        "possible_tables": list(referenced_tables)
                    })

        if invalid_columns:
            detailed_errors.append({
                "message": "列验证失败",
                "invalid_columns": invalid_columns
            })

        # 如果表或列验证失败，直接返回
        if detailed_errors:
            return SQLValidationResult(
                is_correct=False,
                error_type="semantic_error",
                detailed_errors=detailed_errors
            )

    except Exception as e:
        detailed_errors.append(f"语义验证异常：{str(e)}")
        logger.error(f"SQL语义验证异常: {str(e)}", exc_info=True)
        return SQLValidationResult(
            is_correct=False,
            error_type="logic_error",
            detailed_errors=detailed_errors
        )

    # 3. 结果验证
    try:
        # 创建数据库连接
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            # 设置当前schema
            try:
                conn.execute(text(f"SET search_path TO {schema_name}"))
            except Exception as e:
                detailed_errors.append(f"无法设置搜索路径：{str(e)}")
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
                    "message": "学生SQL执行失败",
                    "sql": student_sql,
                    "error": str(e)
                })
                return SQLValidationResult(
                    is_correct=False,
                    error_type="runtime_error",
                    detailed_errors=detailed_errors
                )

            # 执行参考答案SQL
            try:
                answer_result = conn.execute(text(answer_sql)).fetchall()
                answer_columns = list(conn.execute(text(answer_sql)).keys())
            except Exception as e:
                detailed_errors.append({
                    "message": "参考答案SQL执行失败",
                    "sql": answer_sql,
                    "error": str(e)
                })
                return SQLValidationResult(
                    is_correct=False,
                    error_type="runtime_error",
                    detailed_errors=detailed_errors
                )

            # 列结构检查
            if student_columns != answer_columns:
                detailed_errors.append({
                    "message": "结果列不匹配",
                    "student_columns": student_columns,
                    "answer_columns": answer_columns,
                    "difference": [col for col in student_columns if col not in answer_columns] +
                                  [col for col in answer_columns if col not in student_columns]
                })

            # 行数检查
            if len(student_result) != len(answer_result):
                detailed_errors.append({
                    "message": "结果行数不同",
                    "student_rows": len(student_result),
                    "answer_rows": len(answer_result),
                    "difference": abs(len(student_result) - len(answer_result))
                })

            # 根据顺序敏感标志进行详细对比
            student_df = pd.DataFrame(student_result, columns=student_columns)
            answer_df = pd.DataFrame(answer_result, columns=answer_columns)

            if order_sensitive:
                # 顺序敏感模式下的详细比较
                mismatch_details = []

                min_rows = min(len(student_df), len(answer_df))
                max_rows = max(len(student_df), len(answer_df))

                for i in range(max_rows):
                    if i >= min_rows:
                        status = "缺失行" if i >= len(student_df) else "多余行"
                        mismatch_details.append({
                            "row": i + 1,
                            "status": status,
                            "student_data": None if i >= len(student_df) else dict(student_df.iloc[i]),
                            "answer_data": None if i >= len(answer_df) else dict(answer_df.iloc[i])
                        })
                        continue

                    student_row = student_df.iloc[i]
                    answer_row = answer_df.iloc[i]

                    if not student_row.equals(answer_row):
                        row_diff = {}
                        for col in student_columns:
                            if student_row[col] != answer_row[col]:
                                row_diff[col] = {
                                    "student_value": student_row[col],
                                    "answer_value": answer_row[col]
                                }

                        mismatch_details.append({
                            "row": i + 1,
                            "status": "不匹配",
                            "differences": row_diff
                        })

                if mismatch_details:
                    detailed_errors.append({
                        "message": "顺序敏感模式，结果不匹配",
                        "comparison_type": "逐行比较（行顺序必须完全匹配）",
                        "details": mismatch_details
                    })
            else:
                # 顺序无关模式下的详细比较
                # 先检查列结构是否相同
                if set(student_columns) != set(answer_columns):
                    detailed_errors.append({
                        "message": "顺序无关模式下列结构不同",
                        "student_columns": student_columns,
                        "answer_columns": answer_columns,
                        "missing_in_student": list(set(answer_columns) - set(student_columns)),
                        "missing_in_answer": list(set(student_columns) - set(answer_columns))
                    })
                else:
                    # 使用集合操作进行差异检测
                    # 学生有但参考答案没有的行
                    extra_in_student = student_df.merge(
                        answer_df, how='left', indicator=True
                    ).loc[lambda x: x['_merge'] == 'left_only']

                    # 参考答案有但学生没有的行
                    missing_in_student = answer_df.merge(
                        student_df, how='left', indicator=True
                    ).loc[lambda x: x['_merge'] == 'left_only']

                    if not extra_in_student.empty or not missing_in_student.empty:
                        detailed_errors.append({
                            "message": "顺序无关模式，结果不匹配",
                            "comparison_type": "集合比较（仅比较数据内容，忽略顺序）",
                            "extra_rows_in_student": extra_in_student.drop(columns=['_merge']).to_dict(
                                orient='records'),
                            "missing_rows_in_student": missing_in_student.drop(columns=['_merge']).to_dict(
                                orient='records')
                        })

        # 如果没有错误，则SQL正确
        if detailed_errors:
            return SQLValidationResult(
                is_correct=False,
                error_type="result_mismatch",
                detailed_errors=detailed_errors
            )
        else:
            return SQLValidationResult(is_correct=True)

    except Exception as e:
        detailed_errors.append({
            "message": "执行期间发生意外错误",
            "error": str(e),
            "suggestion": "请检查SQL语法和数据库连接"
        })
        logger.error(f"SQL验证异常: {str(e)}", exc_info=True)
        return SQLValidationResult(
            is_correct=False,
            error_type="runtime_error",
            detailed_errors=detailed_errors
        )