from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema import StrOutputParser
from pydantic import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser
import logging

# 定义结构化输出模型
class QuestionOutput(BaseModel):
    description: str = Field(description="题目描述")
    answer_sql: str = Field(description="参考答案SQL语句")

class LLMHelper:
    def __init__(self, api_key, base_url):
        self.llm = ChatOpenAI(
            api_key=api_key,
            base_url=base_url,
            model="deepseek-chat",
            temperature=0.5
        )
        self.output_parser = JsonOutputParser(pydantic_object=QuestionOutput)
        self.logger = logging.getLogger("LLMHelper")
        if not self.logger.handlers:  # 只添加一次handler
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.DEBUG)


    def generate_question(self, schema_definition: str, knowledge_points: list) -> dict:
        # 记录输入参数
        self.logger.debug("开始题目生成流程")
        self.logger.info(f"知识点列表: {', '.join(knowledge_points)}")
        self.logger.debug(f"数据库模式定义: {schema_definition[:100]}...")  # 显示前100字符

        # 构建多知识点prompt
        points_str = "、".join(knowledge_points)
        prompt_template = """
            基于以下数据库模式:
            {schema}

            请生成一个包含以下知识点的SQL题目: {points}
            要求:
            1. 题目描述清晰明确
            2. 难度适中
            3. 参考答案语法正确

            输出格式:
            {format_instructions}
            """

        # 记录生成的prompt
        self.logger.debug("生成完整提示模板:")
        self.logger.debug(prompt_template)

        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["schema", "points"],
            partial_variables={
                "format_instructions": self.output_parser.get_format_instructions()  # 添加格式指令
            }
        )

        chain = prompt | self.llm | self.output_parser

        # 调用前记录
        self.logger.info("调用LLM生成题目内容...")

        try:
            result = chain.invoke({
                "schema": schema_definition,
                "points": points_str
            })

            self.logger.debug(f"生成题目描述: {result['description'][:50]}...")
            self.logger.debug(f"生成SQL语句: {result['answer_sql'][:50]}...")

            return result
        except Exception as e:
            # 添加错误处理
            self.logger.error(f"LLM调用失败: {str(e)}", exc_info=True)
            return {
                "description": "题目生成失败，请重试",
                "answer_sql": ""
            }
    
    def analyze_answer(self, sql: str) -> str:
        prompt = PromptTemplate.from_template(
            "分析以下SQL语句的执行逻辑:\n\n{sql}\n\n"
            "请解释它的功能、关键步骤和可能的输出结果。"
        )
        chain = prompt | self.llm | StrOutputParser()
        return chain.invoke({"sql": sql})
    
    def diagnose_error(self, student_sql: str, answer_sql: str, schema_definition: str) -> str:
        prompt = PromptTemplate.from_template(
            "学生提交的SQL:\n{student_sql}\n\n"
            "参考答案:\n{answer_sql}\n\n"
            "数据库模式:\n{schema}\n\n"
            "请分析学生SQL可能存在的错误类型（语法错误、逻辑错误、结果不匹配），"
            "并给出具体的改进建议。"
        )
        chain = prompt | self.llm | StrOutputParser()
        return chain.invoke({
            "student_sql": student_sql,
            "answer_sql": answer_sql,
            "schema": schema_definition
        })