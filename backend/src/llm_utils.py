from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from pydantic import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser
import logging

# 定义结构化输出模型
class QuestionOutput(BaseModel):
    question_title: str = Field(description="题目标题")
    description: str = Field(description="题目描述")
    answer_sql: str = Field(description="参考答案SQL语句")

class SQLAnalysisOutput(BaseModel):
    """
    用户sql分析结果模型
    """
    correctness_analysis: str = Field(description="答案正确性")
    optimization_suggestions: str = Field(description="优化建议")
    thinking_difference: str = Field(description="与标准答案的思路异同")

class LLMHelper:
    def __init__(self, api_key, base_url):
        self.llm = ChatOpenAI(
            api_key=api_key,
            base_url=base_url,
            model="deepseek-reasoner",
            temperature=0.5
        )
        self.output_parser = JsonOutputParser(pydantic_object=QuestionOutput)
        self.logger = logging.getLogger("LLMHelper")
        if not self.logger.handlers:
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
        1. 题目标题: 长度8-15字
        2. 题目描述: 不少于30字，说明明确
        3. 参考答案SQL: 完整可执行
        4. 所有字段不能为空

        输出格式:
        {format_instructions}
        
        你是一位专业的SQL考试命题专家，请基于以下数据库模式设计一道综合性SQL考题：

        ### 数据库模式
        {schema}
        
        ### 命题要求
        1. **题目深度**：必须综合考察以下所有知识点：{points}
        2. **场景真实性**：题目需模拟真实业务场景（如电商分析/金融风控/用户行为追踪）
        3. **参考答案SQL要求**：完整可执行
        
        ### 输出格式（严格执行）
        {format_instructions}
        
        ### 验证清单（生成后自检）
        - [ ] 题目标题是否清晰体现查询目标（8-15字）
        - [ ] 题目描述是否包含：业务背景+数据难点+输出要求（≥30字）
        - [ ] SQL答案是否包含：  
          ▪️ 完整可执行语句  
        - [ ] 所有字段是否100%完整（无空值）
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

            result['question_title'] = result.get('question_title') or "未命名题目"
            result['description'] = result.get('description') or "题目描述生成失败"
            result['answer_sql'] = result.get('answer_sql') or ""

            self.logger.debug(f"生成题目标题: {result['question_title']}")
            self.logger.debug(f"生成题目描述: {result['description'][:50]}...")
            self.logger.debug(f"生成SQL语句: {result['answer_sql'][:50]}...")

            return result
        except Exception as e:
            # 添加错误处理
            self.logger.error(f"LLM调用失败: {str(e)}", exc_info=True)
            return {
                "question_title": "生成失败",
                "description": "题目生成失败，请重试",
                "answer_sql": ""
            }
    
    def analyze_sql(self, question_description, schema_definition, student_sql, answer_sql, student_result, answer_result, is_correct):
        """
        将用户输入和标准答案交予LLM分析（未附上执行结果）
        参数：
            question_description：问题描述
            schema_definition：模式定义
            student_sql：用户提交的sql
            answer_sql：标准答案
        """
        prompt_template = """
            你是一位专业的SQL导师，请对学生的SQL答案进行详细分析。要求包括以下部分：

            1. 正确性分析：
               - 即使系统已经判断了正确性，也请详细解释学生的SQL是否满足题目要求，并指出可能存在的问题（如果有）。

            2. 优化方向：
               - 从性能（如索引使用）、可读性、简洁性等方面提出优化建议。

            3. 思路异同（与参考答案比较）：
               - 比较学生SQL和参考答案在实现思路上的异同，例如使用的关键词、子查询、连接方式等。

            
            数据库模式定义:
            {schema_definition}

            题目描述：
            {question_description}
            
            题目参考答案:
            {answer_sql}

            学生提交的SQL:
            {student_sql}
            
            学生提交的SQL查询结果：
            {student_result}
            
            标准答案的SQL查询结果：
            {answer_result}
            
            答案是否正确：
            {is_correct}

            请以JSON格式输出分析结果，包含以下字段：
            - "correctness_analysis": 字符串类型，正确性分析内容
            - "optimization_suggestions": 字符串类型，优化建议
            - "thinking_difference": 字符串类型，思路异同分析
            
            安全性要求：
            如果结果为False，请不要再分析中透露标准答案SQL的细节，仅仅做提示启发即可。
            """
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["question_description", "schema_definition", "student_sql", "answer_sql", "student_result", "answer_result", "is_correct"]
        )

        analyze_parser = JsonOutputParser(pydantic_object=SQLAnalysisOutput)

        chain = prompt | self.llm | analyze_parser

        try:
            result = chain.invoke({
                "question_description": question_description,
                "schema_definition": schema_definition,
                "student_sql": student_sql,
                "answer_sql": answer_sql,
                "student_result": student_result,
                "answer_result": answer_result,
                "is_correct": str(is_correct)
            })
            return result
        except Exception as e:
            self.logger.error(f"LLM分析失败: {str(e)}")
            return {
                "correctness_analysis": "分析失败",
                "optimization_suggestions": "分析失败",
                "thinking_difference": "分析失败",
                "learning_analysis": "分析失败"
            }