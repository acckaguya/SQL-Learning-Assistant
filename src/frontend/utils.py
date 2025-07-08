import requests
import streamlit as st
import pandas as pd
import logging
from datetime import datetime

logging.basicConfig(level=logging.DEBUG)
BASE_URL = "http://localhost:8000"  # FastAPI后端地址


def login(username, password):
    """用户登录"""
    response = requests.post(
        f"{BASE_URL}/users/login",
        json={"username": username, "password": password},
        headers={"Content-Type": "application/json",
                 "accept": "application/json"}
    )
    logging.info(response.status_code)
    if response.status_code == 200:
        token = response.json()["access_token"]
        st.session_state.token = token
        user_info = get_current_user(token)
        st.session_state.user = user_info
        return True
    return False


def get_current_user(token):
    """获取当前用户信息"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/users/me", headers=headers)
    return response.json() if response.status_code == 200 else None


def api_request(endpoint, method="GET", data=None):
    """发送API请求"""
    if "token" not in st.session_state:
        st.error("请先登录")
        return None

    headers = {
        "Authorization": f"Bearer {st.session_state.token}",
        "Content-Type": "application/json"
    }

    try:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
        elif method == "POST":
            response = requests.post(f"{BASE_URL}{endpoint}", json=data, headers=headers)
        elif method == "PUT":
            response = requests.put(f"{BASE_URL}{endpoint}", json=data, headers=headers)
        elif method == "DELETE":
            response = requests.delete(f"{BASE_URL}{endpoint}", headers=headers)

        if 200 <= response.status_code < 300:
            return response.json()
        else:
            st.error(f"请求错误: {response.status_code} - {response.text}")
    except Exception as e:
        st.error(f"网络错误: {str(e)}")
    return None


def display_schema_definition(schema_def):
    """可视化数据库模式定义"""
    if not schema_def or "tables" not in schema_def:
        return "无模式定义"

    output = []
    for table in schema_def["tables"]:
        output.append(f"### 表: {table['name']}")
        cols = ["列名 | 类型 | 主键", "---|---|---"]
        for col in table["columns"]:
            cols.append(f"{col['name']} | {col['type']} | {'是' if col.get('primary') else '否'}")
        output.append("\n".join(cols))

        if "sample_data" in table:
            output.append("\n示例数据:")
            df = pd.DataFrame(table["sample_data"], columns=[col["name"] for col in table["columns"]])
            output.append(df.to_markdown(index=False))

    return "\n\n".join(output)

def format_error_detail(error_type, detailed_errors):
    """格式化错误详情为易于理解的文本"""
    formatted = []

    if error_type == "syntax_error":
        formatted.append("### ❌ 语法错误")
        for error in detailed_errors:
            if "message" in error:
                formatted.append(f"- **错误信息**: {error['message']}")

    elif error_type == "semantic_error":
        formatted.append("### ❌ 语义错误")
        for error in detailed_errors:
            if "invalid_tables" in error:
                formatted.append("#### 表引用错误")
                for table_err in error["invalid_tables"]:
                    formatted.append(f"- 表 `{table_err['table']}`: {table_err['reason']}")

            if "invalid_columns" in error:
                formatted.append("#### 列引用错误")
                for col_err in error["invalid_columns"]:
                    formatted.append(f"- 列 `{col_err['column']}`: {col_err['reason']}")

    elif error_type == "result_mismatch":
        formatted.append("### ❌ 结果不匹配")

        for error in detailed_errors:
            # 列结构检查错误
            if "student_columns" in error:
                formatted.append("#### 结果列不匹配")
                formatted.append(f"- 你的查询返回列: `{', '.join(error['student_columns'])}`")
                formatted.append(f"- 参考答案返回列: `{', '.join(error['answer_columns'])}`")

            # 行数不匹配错误
            elif "student_rows" in error:
                formatted.append("#### 结果行数不同")
                formatted.append(f"- 你的查询返回 {error['student_rows']} 行")
                formatted.append(f"- 参考答案返回 {error['answer_rows']} 行")

            # 行内容不匹配错误
            elif "comparison_details" in error:
                formatted.append("#### 行数据不匹配")
                for mismatch in error["comparison_details"]:
                    formatted.append(f"- 第 {mismatch['row']} 行:")
                    for diff in mismatch["differences"]:
                        formatted.append(
                            f"  - 列 `{diff['column']}`: 你的值 `{diff['student_value']}`, 参考答案值 `{diff['answer_value']}`")

    return "\n".join(formatted)