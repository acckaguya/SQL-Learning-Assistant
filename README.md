# SQL智能学习助手

## 项目概述
这是一个用于SQL学习和练习的智能平台，包含：
- 学生端：练习SQL题目、查看历史记录和错题本
- 教师端：管理题目、数据库模式和查看学生练习情况
- 后端API：基于FastAPI的接口
- 数据库：PostgreSQL存储数据

## 环境要求
- Python 3.12
- PostgreSQL 15
- LLM APIKEY
- uv 0.7.9

## 安装步骤

### 1. 克隆仓库
```
git clone https://github.com/acckaguya/SQL-Learning-Assistant.git
cd SQL-Learning-Assistant
```

### 2. 创建虚拟环境
```
uv venv .venv
```

### 3. 激活虚拟环境
```
source .venv/bin/activate  # Linux/Mac
.\.venv\Scripts\activate  # Windows
```

### 4. 安装依赖
```
uv add -r requirements.txt
```

### 5. 初始化
创建.env文件并添加以下配置：
```
OPENAI_API_KEY="your_llm_api_key"
BASE_URL="llm_base_model"
DATABASE_URL="your_database_url"
```

## 运行服务

### 1. 启动后端API
```
uvicorn src.backend.main:app
```

### 2. 启动前端服务

教师前端
```commandline
streamlit run src\frontend\teacher.py
```
学生前端
```
streamlit run src\frontend\student.py
```

## 功能说明
### 学生功能
- 按知识点练习SQL题目
- 提交答案并获取即时反馈
- 查看练习历史和错题本
- 接收AI生成的优化建议
### 教师功能
- 生成和编辑SQL题目
- 管理数据库模式
- 查看学生练习情况
- 分析学生整体正确率