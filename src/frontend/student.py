import streamlit as st
from utils import api_request, display_schema_definition, login, format_error_detail


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
                        if result.get("detailed_errors"):
                            with st.expander("查看详细错误分析", expanded=True):
                                st.subheader("你的SQL")
                                st.code(student_sql, language="sql")

                                # 显示格式化后的错误详情
                                formatted_errors = format_error_detail(
                                    result["error_type"],
                                    result["detailed_errors"]
                                )
                                st.markdown(formatted_errors)

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
                        else:
                            st.warning("无详细错误信息")
                else:
                    st.error("提交答案失败，请检查网络连接")

                # 调用LLM分析答案
                with st.spinner("AI分析中，请稍等..."):
                    analysis_result = api_request(
                        "/analyze/sql",
                        method="POST",
                        data=result
                    )
                # 显示分析结果
                if analysis_result:
                    st.subheader("AI分析报告")
                    st.markdown("### 1. 正确性分析")
                    st.write(analysis_result.get("correctness_analysis", "无"))
                    st.markdown("### 2. 优化建议")
                    st.write(analysis_result.get("optimization_suggestions", "无"))
                    st.markdown("### 3. 思路异同")
                    st.write(analysis_result.get("thinking_difference", "无"))
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

            # 详细记录表格
            st.subheader("详细记录")
            expanded_attempt_id = st.session_state.get("expanded_attempt_id", None)

            for i, attempt in enumerate(attempts):
                # 获取题目详情
                question = api_request(f"/questions/get/{attempt['question_id']}") or {}

                with st.container():
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.markdown(f"**题目**: {question.get('description', '未知题目')[:50]}...")
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
                        st.subheader("你的SQL")
                        st.code(attempt["student_sql"], language="sql")

                        # 错误详情展示
                        if not attempt["is_correct"]:
                            st.subheader("错误分析")

                            if attempt.get("detailed_errors"):
                                formatted_errors = format_error_detail(
                                    attempt.get("error_type"),
                                    attempt["detailed_errors"]
                                )
                                st.markdown(formatted_errors)
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

            # 错题详情
            for question in questions:
                with st.expander(f"{question['description'][:50]}..."):
                    st.markdown(question["description"])

                    # 显示数据库模式
                    if st.checkbox("查看数据库模式", key=f"schema_{question['question_id']}"):
                        schema = api_request(f"/sample-schemas/get/{question['schema_id']}")
                        if schema:
                            st.markdown(display_schema_definition(schema["schema_definition"]))


                    # 获取该题目的错误尝试记录
                    attempts = api_request(
                        f"/attempts/by_question/{question['question_id']}"
                    ) or []

                    if attempts:
                        st.subheader("我的错误尝试")
                        for attempt in attempts:
                            if attempt["is_correct"]:
                                continue

                            st.markdown(f"**提交时间**: {attempt['submitted_at']}")
                            st.markdown(f"**错误类型**: {attempt.get('error_type', '未知错误')}")

                            col1, col2 = st.columns([1, 2])
                            with col1:
                                st.code(attempt["student_sql"], language="sql")
                            with col2:
                                if attempt.get("detailed_errors"):
                                    formatted_errors = format_error_detail(
                                        attempt.get("error_type"),
                                        attempt["detailed_errors"]
                                    )
                                    st.markdown(formatted_errors)
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