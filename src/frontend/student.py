import streamlit as st
import pandas as pd
import json
from utils import api_request, display_schema_definition, login


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

    # 开始练习
    if choice == "开始练习":
        st.header("SQL练习")

        # 选择知识点
        selected_point = st.selectbox(
            "选择知识点",
            options=list(knowledge_points.keys()),
            format_func=lambda x: knowledge_points[x]
        )

        # 获取题目
        if st.button("随机获取题目"):
            question = api_request(f"/questions/get/random?tag={selected_point}")
            if question:
                st.session_state.current_question = question
            else:
                st.error("获取题目失败")

        # 显示题目
        if "current_question" in st.session_state:
            question = st.session_state.current_question
            st.subheader("题目描述")
            st.markdown(question["description"])

            # 显示数据库模式
            schema = api_request(f"/sample-schemas/get/{question['schema_id']}")
            if schema:
                with st.expander("查看数据库模式"):
                    st.markdown(display_schema_definition(schema["schema_definition"]))

            # SQL输入
            student_sql = st.text_area("请输入你的SQL答案", height=200)

            # 提交答案
            if st.button("提交答案"):
                if not student_sql:
                    st.warning("请输入SQL语句")
                else:
                    result = api_request(
                        "/attempts/submit",
                        method="POST",
                        data={
                            "student_sql": student_sql,
                            "question_id": question["question_id"]
                        }
                    )
                    if result:
                        if result["is_correct"]:
                            st.success("答案正确！")
                        else:
                            st.error(f"答案错误: {result['error_type']}")
                            # 显示错误分析
                            if result.get("error_analysis"):
                                with st.expander("错误分析"):
                                    st.markdown(result["error_analysis"])

    # 练习历史
    elif choice == "练习历史":
        st.header("我的练习历史")
        attempts = api_request("/attempts/history") or []

        if attempts:
            # 统计信息
            correct_count = sum(1 for a in attempts if a["is_correct"])
            accuracy = correct_count / len(attempts) * 100 if attempts else 0

            col1, col2 = st.columns(2)
            col1.metric("总练习次数", len(attempts))
            col2.metric("正确率", f"{accuracy:.1f}%")

            # 详细记录
            df = pd.DataFrame([{
                "题目ID": attempt.get("question_id", "N/A"),
                "提交SQL": attempt["student_sql"],
                "是否正确": "✓" if attempt["is_correct"] else "✗",
                "错误类型": attempt["error_type"] or "",
                "提交时间": attempt["submitted_at"]
            } for attempt in attempts])
            st.dataframe(df)
        else:
            st.info("暂无练习记录")

    # 错题本
    elif choice == "错题本":
        st.header("我的错题本")
        questions = api_request("/attempts/mistakes") or []

        if questions:
            for question in questions:
                with st.expander(f"题目: {question['description']}"):
                    st.subheader("参考答案")
                    st.code(question["answer_sql"], language="sql")

                    # 显示我的错误尝试
                    attempts = api_request(f"/attempts/by_question/{question['question_id']}")
                    if attempts:
                        st.subheader("我的错误尝试")
                        for attempt in attempts:
                            st.markdown(f"**提交时间**: {attempt['submitted_at']}")
                            st.code(attempt["student_sql"], language="sql")
                            if attempt["error_type"]:
                                st.error(f"错误类型: {attempt['error_type']}")
                            if attempt.get("error_analysis"):
                                st.warning(f"错误分析: {attempt['error_analysis']}")
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