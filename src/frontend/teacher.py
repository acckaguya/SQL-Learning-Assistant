import streamlit as st
import pandas as pd
from utils import api_request, display_schema_definition, login, format_error_detail
import json
import logging

logging.basicConfig(level=logging.DEBUG)


def teacher_dashboard():
    st.title("SQL智能练习平台 - 教师端")

    # 导航菜单
    menu = ["题库管理", "样例数据库", "学生练习情况"]
    choice = st.sidebar.selectbox("菜单", menu)

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
    knowledge_fields = [
        "basic_query", "where_clause", "aggregation", "group_by", "order_by",
        "limit_clause", "joins", "subqueries", "null_handling", "execution_order"
    ]

    # 题库管理
    if choice == "题库管理":
        st.header("题目管理")

        # 生成题目
        with st.expander("生成新题目"):
            schemas = api_request("/sample-schemas/get/schemas") or []
            schema_options = {s["schema_name"]: s["schema_id"] for s in schemas}
            selected_schema = st.selectbox("选择数据库模式", list(schema_options.keys()))
            selected_points = st.multiselect(
                "选择知识点（可多选）",
                list(knowledge_points.values()),
                key="knowledge_points_selector"
            )

            if st.button("生成题目") and selected_points:
                schema_id = schema_options[selected_schema]
                point_names = []
                for point_cn in selected_points:
                    for en, cn in knowledge_points.items():
                        if cn == point_cn:
                            point_names.append(en)
                # 构建JSON请求体，包含知识点和模式ID
                payload = {
                    "knowledge_points": point_names,  # 传递知识点列表
                    "schema_id": schema_id
                }
                logging.info(payload)
                # 发送POST请求时传递JSON数据
                result = api_request(
                    "/questions/generate",
                    method="POST",
                    data=payload
                )
                logging.info(result)
                if result:
                    st.success("题目生成成功！")
                else:
                    st.error("题目生成失败，请检查后端日志")

        # 题目列表
        st.subheader("题目列表")
        questions = []  # 初始化空列表
        selected_point = st.selectbox("按知识点筛选", ["全部"] + list(knowledge_points.values()))

        if selected_point != "全部":
            point_id = [k for k, v in knowledge_points.items() if v == selected_point][0]
            response = api_request(f"/questions/get?point={point_id}")
            questions = response if response else []
        else:
            response = api_request("/questions/get")  # 获取所有题目
            questions = response if response else []

        if questions:
            df = pd.DataFrame([{
                "ID": q["question_id"],
                "标题": q["question_title"],
                "描述": q["description"],
                "知识点": ", ".join([
                    str(i + 1) for i, field in enumerate(knowledge_fields)
                    if q.get(field)
                ]),
                "创建时间": q["created_at"]
            } for q in questions])
            st.dataframe(df)

            # 题目操作
            question_options = [f"{q['question_id']} - {q['question_title']}" for q in questions]
            selected_option = st.selectbox("选择题目操作", [""] + question_options)
            if selected_option:
                # 从选项字符串中提取题目ID
                selected_id = selected_option.split(" - ")[0]
                question = next((q for q in questions if q["question_id"] == selected_id), None)
                if question:
                    st.subheader("题目详情")
                    st.markdown(f"**{question['question_title']}**")
                    st.markdown(f"**描述**: {question['description']}")
                    st.code(question["answer_sql"], language="sql")

                    # 知识点标签
                    st.subheader("知识点标签")
                    tags = {}
                    cols = st.columns(2)
                    for i, field in enumerate(knowledge_fields):
                        with cols[i % 2]:  # 交替放在两列中
                            tags[field] = st.checkbox(
                                f"知识点{i + 1} ({knowledge_points[field]})",
                                value=question.get(field, False)
                            )
                    order_sensitive = st.checkbox(
                        "顺序敏感（结果顺序必须完全匹配）",
                        value=question.get("order_sensitive", False)
                    )

                    # 更新题目
                    update_question_title = st.text_area("题目标题", value=question["question_title"])
                    update_description = st.text_area("题目描述", value=question["description"], height=200)
                    update_answer_sql = st.text_area("参考答案", value=question["answer_sql"])

                    if st.button("更新题目"):
                        update_data = {
                            "question_title": update_question_title,
                            "description": update_description,
                            "answer_sql": update_answer_sql,
                            "schema_id": question["schema_id"],
                            "order_sensitive": order_sensitive,
                            **tags
                        }
                        result = api_request(f"/questions/update/{selected_id}", method="PUT", data=update_data)
                        if result:
                            st.success("题目更新成功！")

                    # 删除题目
                    if st.button("删除题目"):
                        result = api_request(f"/questions/{selected_id}", method="DELETE")
                        if result:
                            st.success("题目删除成功！")
        else:
            st.info("暂无题目")

    # 样例数据库管理
    elif choice == "样例数据库":
        st.header("样例数据库管理")

        # 创建新数据库模式
        with st.expander("创建新数据库模式"):
            schema_name = st.text_input("模式名称")
            schema_def = st.text_area("模式定义 (JSON格式)", height=200)
            init_sql = st.text_area("初始数据SQL",
                help="INSERT语句生成示例数据，如: INSERT INTO users VALUES (1, 'Alice')")
            if st.button("创建模式") and schema_name and schema_def:
                try:
                    json_data = json.loads(schema_def)
                    result = api_request("/sample-schemas/create", method="POST", data={
                        "schema_name": schema_name,
                        "schema_definition": json_data,
                        "init_sql": init_sql
                    })
                    if result:
                        st.success("数据库模式创建成功！")
                except json.JSONDecodeError as e:
                    st.error(f"JSON格式错误: {str(e)}")

        # 数据库列表
        schemas = api_request("/sample-schemas/get/schemas") or []
        if schemas:
            for schema in schemas:
                with st.expander(f"数据库: {schema['schema_name']} (ID: {schema['schema_id']})"):
                    st.markdown(display_schema_definition(schema["schema_definition"]))
                    if st.button(f"删除{schema['schema_name']}", key=f"del_{schema['schema_id']}"):
                        result = api_request(f"/sample-schemas/delete/{schema['schema_id']}", method="DELETE")
                        if result:
                            st.success("数据库模式删除成功！")
        else:
            st.info("暂无数据库模式")

    # 学生练习情况
    elif choice == "学生练习情况":
        st.header("学生练习情况分析")
        # 调用新接口获取所有练习记录
        attempts = api_request("/attempts/all_history") or []

        if attempts:
            # 正确率计算
            correct_count = sum(1 for a in attempts if a["is_correct"])
            accuracy = correct_count / len(attempts) * 100 if attempts else 0

            col1, col2 = st.columns(2)
            col1.metric("总练习次数", len(attempts))
            col2.metric("正确率", f"{accuracy:.1f}%")

            # 错误类型分析
            error_types = {}
            for attempt in attempts:
                if not attempt["is_correct"]:
                    error_type = attempt.get("error_type", "unknown")
                    error_types[error_type] = error_types.get(error_type, 0) + 1

            if error_types:
                st.subheader("错误类型分布")
                st.bar_chart(pd.DataFrame({
                    "错误类型": list(error_types.keys()),
                    "次数": list(error_types.values())
                }).set_index("错误类型"))

            # 详细记录
            st.subheader("练习记录详情")
            # 收集所有题目ID
            question_ids = list(set([str(attempt["question_id"]) for attempt in attempts]))

            # 批量获取题目详情
            questions_data = {}
            if question_ids:
                # 调用批量获取接口
                questions_response = api_request(
                    "/questions/get/batch",
                    method="POST",
                    data=question_ids
                )
                if questions_response:
                    questions_data = {q["question_id"]: q for q in questions_response}

            # 添加用户信息和题目信息字段
            df_data = []
            for attempt in attempts:
                question_info = questions_data.get(attempt["question_id"], {})
                df_data.append({
                    "学生": attempt["username"],
                    "题目ID": attempt["question_id"],
                    "题目标题": question_info.get("question_title", "未知题目"),
                    "提交SQL": attempt["student_sql"],
                    "是否正确": "✓" if attempt["is_correct"] else "✗✗",
                    "错误类型": attempt.get("error_type", ""),
                    "提交时间": attempt["submitted_at"]
                })

            df = pd.DataFrame(df_data)
            st.dataframe(df)

            # 题目详情展示
            question_options = [f"{q['question_id']} - {q['question_title']}" for q in questions_response]
            selected_option = st.selectbox("查看题目详情", [""] + question_options)
            if selected_option:
                # 从选项字符串中提取题目ID
                selected_id = selected_option.split(" - ")[0]
                question = questions_data.get(selected_id)
                if question:
                    st.subheader("题目详情")
                    st.markdown(f"**{question['question_title']}**")
                    st.markdown(f"**描述**: {question['description']}")
                    st.code(question["answer_sql"], language="sql")

                    # 显示数据库模式
                    schema = api_request(f"/sample-schemas/get/{question['schema_id']}")
                    if schema:
                        with st.expander("查看数据库模式"):
                            st.markdown(display_schema_definition(schema["schema_definition"]))
                else:
                    st.warning("未找到题目详情")
        else:
            st.info("暂无练习记录")

# 教师界面入口
def main():
    if "user" not in st.session_state or st.session_state.user.get("role") != "teacher":
        st.warning("请以教师身份登录")
        return

    teacher_dashboard()


if __name__ == "__main__":
    if "user" not in st.session_state:
        st.title("教师登录")
        with st.form(key="login_form"):
            username = st.text_input("用户名")
            password = st.text_input("密码", type="password")
            submit_button = st.form_submit_button("登录")

            if submit_button:
                if login(username, password):
                    if st.session_state.user["role"] == "teacher":
                        st.experimental_rerun()
                    else:
                        st.error("⚠️ 请使用教师账号登录")
                else:
                    st.error("❌❌ 登录失败，请检查凭证")
    else:
        main()