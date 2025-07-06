import streamlit as st
import pandas as pd
import json
from utils import api_request, display_schema_definition, login
from datetime import datetime


# 新增工具函数：格式化错误详情
def format_error_detail(error_type, detail):
    """格式化错误详情为易于理解的文本"""

    if error_type == "syntax_error":
        return f"""
        **语法错误**
        ⚠️ 您的SQL语句存在语法问题，请检查：
        - 关键字拼写是否正确（如SELECT、FROM、WHERE等）
        - 括号是否匹配
        - 引号是否正确闭合
        - 逗号分隔是否正确

        **错误详情**: {detail}
        """

    elif error_type == "semantic_error":
        errors = []
        for section in detail:
            if "invalid_tables" in section:
                errors.append("**表引用错误**")
                for table_err in section["invalid_tables"]:
                    errors.append(f"- 表 `{table_err['table']}`: {table_err['reason']}")
                    if "available_tables" in table_err:
                        errors.append(f"  可用表: {', '.join(table_err['available_tables'])}")

            if "invalid_columns" in section:
                errors.append("**列引用错误**")
                for col_err in section["invalid_columns"]:
                    errors.append(f"- 列 `{col_err['column']}`: {col_err['reason']}")
                    if "available_columns" in col_err:
                        errors.append(f"  可用列: {', '.join(col_err['available_columns'])}")

        return "\n\n".join(errors)

    elif error_type == "result_mismatch":
        errors = []
        for diff in detail:
            if diff["message"] == "结果列不匹配":
                errors.append("**结果列不匹配**")
                student_cols = ", ".join(diff.get("student_columns", []))
                answer_cols = ", ".join(diff.get("answer_columns", []))
                errors.append(f"- 您的查询返回列: `{student_cols}`")
                errors.append(f"- 参考答案返回列: `{answer_cols}`")
                missing = diff.get("missing_in_student", [])
                extra = diff.get("missing_in_answer", [])

                if missing:
                    errors.append(f"- 缺少的列: `{', '.join(missing)}`")
                if extra:
                    errors.append(f"- 多余的列: `{', '.join(extra)}`")

            elif diff["message"] == "结果行数不同":
                errors.append("**结果行数不匹配**")
                errors.append(f"- 您的查询返回 {diff.get('student_rows', 0)} 行")
                errors.append(f"- 参考答案返回 {diff.get('answer_rows', 0)} 行")
                errors.append(f"- 差异: {diff.get('difference', 0)} 行")

            elif diff.get("comparison_type", "") == "逐行比较（行顺序必须完全匹配）":
                errors.append("**结果行内容不匹配**")
                errors.append("请检查以下行号的数据是否与预期一致:")

                for detail in diff.get("details", []):
                    row_msg = f"行 {detail['row']}: "
                    if detail["status"] == "缺失行":
                        errors.append(f"{row_msg}缺少了这一行")
                    elif detail["status"] == "多余行":
                        errors.append(f"{row_msg}包含多余的行")
                    elif detail["status"] == "不匹配":
                        col_errors = []
                        for col, vals in detail["differences"].items():
                            student_val = vals["student_value"]
                            answer_val = vals["answer_value"]

                            # 处理日期类型
                            if isinstance(student_val, datetime):
                                student_val = student_val.strftime("%Y-%m-%d")
                            if isinstance(answer_val, datetime):
                                answer_val = answer_val.strftime("%Y-%m-%d")

                            col_errors.append(f"  - 列 `{col}`: 您的值 `{student_val}`, 预期值 `{answer_val}`")

                        if col_errors:
                            errors.append(f"{row_msg}")
                            errors.extend(col_errors)

            elif diff.get("comparison_type", "") == "集合比较（仅比较数据内容，忽略顺序）":
                errors.append("**结果集内容不匹配**")

                if diff.get("extra_rows_in_student"):
                    errors.append("- 您的查询包含多余的行:")
                    for row in diff["extra_rows_in_student"]:
                        errors.append(f"  - {row}")

                if diff.get("missing_rows_in_student"):
                    errors.append("- 您的查询缺少以下行:")
                    for row in diff["missing_rows_in_student"]:
                        errors.append(f"  - {row}")

    return "\n".join(errors)


def student_dashboard():
    st.title("SQL智能练习平台 - 学生端")

    # 知识点映射
    knowledge_points = {
        "basic_query": "基础查询",
        "where_clause": "条件查询",
        "aggregation": "聚合函数",
        "group_by": "分组查询",
        "order_by": "排序查询",
        "limit_clause": "分页查询",
        "joins": "多表连接",
        "subqueries": "子查询",
        "null_handling": "NULL处理",
        "execution_order": "执行顺序"
    }

    # 导航菜单
    menu = ["开始练习", "练习历史", "错题本"]
    choice = st.sidebar.selectbox("菜单", menu)

    # 当前用户信息
    user = st.session_state.get("user", {})

    # 开始练习
    if choice == "开始练习":
        st.header("SQL练习")

        # 选择知识点
        selected_point = st.selectbox(
            "选择知识点",
            options=list(knowledge_points.keys()),
            format_func=lambda x: knowledge_points[x]
        )

        # 获取该知识点的所有题目
        questions = api_request(f"/questions/get?point={selected_point}") or []

        if not questions:
            st.warning("该知识点暂无题目")
            st.stop()

        # 选择具体题目
        question_options = {f"{q['description'][:50]}...": q for q in questions}
        selected_desc = st.selectbox(
            "选择题目",
            options=list(question_options.keys())
        )
        question = question_options[selected_desc]

        # 显示题目
        st.subheader("题目描述")
        st.markdown(question["description"])

        # 显示数据库模式
        schema = api_request(f"/sample-schemas/get/{question['schema_id']}")
        if schema:
            with st.expander("查看数据库模式"):
                st.markdown(display_schema_definition(schema["schema_definition"]))

        # SQL输入
        student_sql = st.text_area("请输入你的SQL答案", height=150,
                                   placeholder="在此输入SQL语句...")

        # 提交答案
        if st.button("提交答案"):
            if not student_sql.strip():
                st.warning("请输入SQL语句")
            else:
                # 保存当前SQL
                st.session_state.last_sql = student_sql

                result = api_request(
                    "/attempts/submit",
                    method="POST",
                    data={
                        "student_sql": student_sql,
                        "question_id": question["question_id"]
                    }
                )
                if result:
                    # 显示整体结果
                    if result["is_correct"]:
                        st.success("✅ 答案正确！")
                    else:
                        st.error(f"❌ 答案错误: {result['error_type']}")

                        # 详细错误展示
                        error_detail = result.get("detailed_errors")
                        if error_detail:
                            with st.expander("查看详细错误分析", expanded=True):
                                # 使用列布局
                                col1, col2 = st.columns([3, 1])

                                with col1:
                                    st.subheader("错误分析")
                                    st.markdown(f"**错误类型**: `{result['error_type']}`")

                                    # 显示格式化后的错误详情
                                    if isinstance(error_detail, list):
                                        formatted = format_error_detail(result["error_type"], error_detail)
                                        st.markdown(formatted)
                                    else:
                                        st.json(error_detail)

                                with col2:
                                    st.subheader("您的SQL")
                                    st.code(student_sql, language="sql")
                                    st.subheader("参考答案")
                                    st.code(question["answer_sql"], language="sql")

                            # 错误类型专项提示
                            if result["error_type"] == "syntax_error":
                                st.info("💡 **语法提示**: 使用SQL格式化工具可以帮助您检查语法错误")
                            elif result["error_type"] == "semantic_error":
                                st.info("💡 **语义提示**: 请确认您使用的表和列名称与数据库模式匹配")
                            elif result["error_type"] == "result_mismatch":
                                if question.get("order_sensitive"):
                                    st.info("🔔 该题目对结果顺序敏感，请确保结果顺序与题目要求一致")
                                else:
                                    st.info("🔔 该题目只关注结果内容，顺序不影响评分")

                            # 添加重试按钮
                            if st.button("↩️ 修改后重新提交"):
                                # 清除提交结果但保留当前SQL
                                st.rerun()
                        else:
                            st.warning("无详细错误信息")
                else:
                    st.error("提交答案失败，请检查网络连接")

    # 练习历史
    elif choice == "练习历史":
        st.header("我的练习历史")
        attempts = api_request("/attempts/history") or []

        if attempts:
            # 统计信息
            correct_count = sum(1 for a in attempts if a["is_correct"])
            total_attempts = len(attempts)
            accuracy = (correct_count / total_attempts * 100) if total_attempts else 0

            col1, col2, col3 = st.columns(3)
            col1.metric("总练习次数", total_attempts)
            col2.metric("正确次数", correct_count)
            col3.metric("正确率", f"{accuracy:.1f}%")

            # 练习日期分布（直方图）
            try:
                dates = [pd.to_datetime(a["submitted_at"]).date() for a in attempts]
                date_counts = pd.Series(dates).value_counts().sort_index()

                st.subheader("练习分布")
                st.bar_chart(date_counts)
            except:
                pass

            # 详细记录表格
            st.subheader("详细记录")
            expanded_attempt_id = st.session_state.get("expanded_attempt_id", None)

            # 获取所有题目ID
            question_ids = {a["question_id"] for a in attempts if a["question_id"]}

            # 批量获取题目详情
            questions_map = {}
            for qid in question_ids:
                question = api_request(f"/questions/get/{qid}")  # 使用题目详情端点
                if question:
                    questions_map[qid] = question

            for i, attempt in enumerate(attempts):
                if attempt["question_id"] is None:
                    continue
                # 从映射中获取题目详情
                question_detail = questions_map.get(attempt["question_id"], {})

                with st.container():
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        # 使用题目详情而不是ID
                        if "description" in question_detail:
                            st.markdown(f"**题目**: {question_detail['description'][:50]}...")
                        else:
                            st.markdown(f"**题目ID**: {attempt['question_id']}")
                    with col2:
                        st.markdown(f"**结果**: {'✅ 正确' if attempt['is_correct'] else '❌ 错误'}")
                    with col3:
                        if st.button(f"详情 {i + 1}", key=f"btn_{attempt['attempt_id']}"):
                            if expanded_attempt_id == attempt["attempt_id"]:
                                st.session_state.expanded_attempt_id = None
                            else:
                                st.session_state.expanded_attempt_id = attempt["attempt_id"]

                # 展开详情
                if expanded_attempt_id == attempt["attempt_id"]:
                    with st.expander("查看详情", expanded=True):
                        if "description" in question_detail:
                            st.subheader("题目描述")
                            st.markdown(question_detail["description"])

                        col1, col2 = st.columns(2)
                        with col1:
                            st.subheader("您的SQL")
                            st.code(attempt["student_sql"], language="sql")
                        with col2:
                            st.subheader("参考答案")
                            st.code(question_detail["answer_sql"], language="sql")

                        # 错误详情展示
                        if not attempt["is_correct"]:
                            st.subheader("错误分析")

                            error_type = attempt.get("error_type")
                            error_detail = attempt.get("detailed_errors")

                            if error_detail:
                                st.markdown(f"**错误类型**: `{error_type}`")
                                st.markdown(format_error_detail(error_type, error_detail))

                                if error_type == "result_mismatch" and question.get("order_sensitive"):
                                    st.info("🔔 注意：该题目对结果顺序有严格要求")
                            else:
                                st.warning("无详细错误信息")
        else:
            st.info("暂无练习记录")

    # 错题本
    elif choice == "错题本":
        st.header("我的错题本")
        questions = api_request("/attempts/mistakes") or []

        if questions:
            st.subheader(f"您有 {len(questions)} 道错题需要复习")

            # 按知识点统计错题
            point_counts = {}
            for q in questions:
                for point in knowledge_points:
                    if q.get(point):
                        point_counts.setdefault(point, 0)
                        point_counts[point] += 1

            # 显示知识点分布
            if point_counts:
                st.markdown("### 错题知识点分布")
                for point, count in point_counts.items():
                    label = knowledge_points[point]
                    st.progress(count / 5, text=f"{label}: {count}题")

            # 错题详情
            for question in questions:
                # 使用容器代替expander，避免嵌套问题
                with st.container():
                    st.subheader(f"题目: {question['description'][:50]}...")

                    st.markdown(question["description"])

                    # 显示数据库模式 - 使用复选框代替嵌套的expander
                    if st.checkbox("查看数据库模式", key=f"schema_{question['question_id']}"):
                        schema = api_request(f"/sample-schemas/get/{question['schema_id']}")
                        if schema:
                            st.markdown(display_schema_definition(schema["schema_definition"]))

                    st.subheader("参考答案")
                    st.code(question["answer_sql"], language="sql")

                    # 获取该题目的错误尝试记录
                    attempts = api_request(
                        f"/attempts/by_question/{question['question_id']}"
                    ) or []

                    if attempts:
                        st.subheader("我的错误尝试")
                        for attempt in attempts:
                            if attempt["is_correct"]:
                                continue  # 跳过正确尝试

                            with st.container():
                                st.markdown(f"**提交时间**: {attempt['submitted_at']}")
                                st.markdown(f"**错误类型**: {attempt.get('error_type', '未知错误')}")

                                col1, col2 = st.columns([1, 3])
                                with col1:
                                    st.code(attempt["student_sql"], language="sql")
                                with col2:
                                    # 详细错误分析
                                    error_detail = attempt.get("detailed_errors")
                                    if error_detail:
                                        st.markdown(format_error_detail(
                                            attempt.get("error_type"),
                                            error_detail
                                        ))
                                    else:
                                        st.warning("无详细错误信息")
                    else:
                        st.info("暂无错误尝试记录")
        else:
            st.info("暂无错题记录")


# 学生界面入口
def main():
    if "user" not in st.session_state or st.session_state.user.get("role") != "student":
        st.warning("请以学生身份登录")
        login_form()
    else:
        student_dashboard()


def login_form():
    st.title("学生登录")
    username = st.text_input("用户名")
    password = st.text_input("密码", type="password")
    if st.button("登录"):
        if login(username, password):
            if st.session_state.user["role"] == "student":
                st.experimental_rerun()
            else:
                st.error("请使用学生账号登录")
        else:
            st.error("登录失败")


if __name__ == "__main__":
    main()