import os
import json
from uuid import uuid4
from fastapi import APIRouter, UploadFile, File, HTTPException, Body
from typing import Dict, Optional
from pydantic import BaseModel
from typing import List

# langchain loaders
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader

router = APIRouter(prefix="/smart_contracts")

# 上传文件接口
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    try:
        file_id = str(uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        file_path = os.path.join(UPLOAD_DIR, f"{file_id}{file_extension}")
        with open(file_path, "wb") as f:
            f.write(await file.read())
        return {"file_id": file_id, "file_name": file.filename, "file_path": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

# 合同分析接口
DOC_DIR = "documents"
os.makedirs(DOC_DIR, exist_ok=True)

from openai import OpenAI
client = OpenAI(
    base_url="https://spark-api-open.xf-yun.com/v2/",
    api_key="kisSdbShVywMKBJBeQOB:NnYhpcXxfEPrptqnuIEL")

@router.post("/analyze_contract/")
async def analyze_contract(file: UploadFile = File(...)) -> Dict:
    import re
    try:
        file_path = os.path.join(DOC_DIR, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())
        if file.filename.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
        elif file.filename.endswith(".docx"):
            loader = Docx2txtLoader(file_path)
        elif file.filename.endswith(".txt"):
            loader = TextLoader(file_path, encoding="utf-8")
        else:
            raise HTTPException(status_code=400, detail="仅支持 .txt/.docx/.pdf 文件")
        docs = loader.load()
        content = "\n".join([doc.page_content for doc in docs])
        prompt = f"请分析以下合同内容，并以如下标准JSON格式返回：\n\n{content}\n\n返回格式示例：\n{{\n  \"合同摘要\": {{\n    \"借款人\": \"张三\",\n    \"出借人\": \"李四\",\n    \"借款金额\": \"1000元\",\n    \"借款期限\": \"一年\",\n    \"还款时间\": \"一年后\"\n  }},\n  \"潜在风险条款\": [\n    {{\n      \"风险类型\": \"利息约定不明确\",\n      \"描述\": \"合同未明确约定借款利息，可能引发争议。\"\n    }},\n    {{\n      \"风险类型\": \"还款方式缺失\",\n      \"描述\": \"未明确还款方式，可能导致还款凭证缺失风险。\"\n    }}\n  ]\n}}\n字段全部用中文，且不要返回markdown、代码块或字符串化JSON。"
        response = client.chat.completions.create(
            model="x1",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=1024
        )
        result = response.choices[0].message.content
        # 1. 尝试直接解析为JSON
        def try_json_loads(s):
            try:
                return json.loads(s)
            except Exception:
                return None
        # 2. 尝试去除markdown/代码块/字符串化JSON
        def extract_json_str(s):
            s = s.strip()
            # 提取```json ... ```
            match = re.search(r'```json([\s\S]*?)```', s)
            if match:
                return match.group(1).strip()
            # 提取``` ... ```
            match = re.search(r'```([\s\S]*?)```', s)
            if match:
                return match.group(1).strip()
            # 提取第一个大括号包裹的内容
            match = re.search(r'({[\s\S]*})', s)
            if match:
                return match.group(1).strip()
            return s
        # 3. key映射表
        key_map = {
            # 合同摘要
            "summary": "合同摘要", "contract_summary": "合同摘要", "摘要": "合同摘要", "合同摘要": "合同摘要",
            "borrower": "借款人", "lender": "出借人", "amount": "借款金额", "repayment_term": "还款期限", "contract_type": "合同类型", "signed_by": "签署情况", "核心内容": "核心内容",
            # 潜在风险条款
            "risk_clauses": "潜在风险条款", "risk_warnings": "潜在风险条款", "风险提示": "潜在风险条款", "潜在风险条款": "潜在风险条款", "risk_tips": "潜在风险条款", "potential_risks": "潜在风险条款",
            # 风险条款内字段
            "risk_type": "风险类型", "type": "风险类型", "风险类型": "风险类型",
            "description": "描述", "desc": "描述", "描述": "描述",
        }
        # 4. 递归key映射
        def normalize_keys(data):
            if isinstance(data, dict):
                new_data = {}
                for k, v in data.items():
                    k_cn = key_map.get(k.strip(), k.strip())
                    new_data[k_cn] = normalize_keys(v)
                return new_data
            elif isinstance(data, list):
                return [normalize_keys(i) for i in data]
            else:
                return data
        # 5. 尝试多轮清洗和解析
        analysis_data = try_json_loads(result)
        if not analysis_data:
            json_str = extract_json_str(result)
            analysis_data = try_json_loads(json_str)
        if not analysis_data and isinstance(result, str):
            # 再尝试去除多余前缀、后缀
            json_str = extract_json_str(result)
            analysis_data = try_json_loads(json_str)
        if not analysis_data:
            return {"analysis": {"原始内容": result}}
        # 6. 递归key映射，确保全部为中文key
        analysis_data = normalize_keys(analysis_data)
        # 7. 只保留标准结构
        std = {}
        if "合同摘要" in analysis_data:
            std["合同摘要"] = analysis_data["合同摘要"]
        else:
            # 兼容AI只返回了部分摘要字段
            summary_fields = ["借款人", "出借人", "借款金额", "借款期限", "还款时间", "合同类型", "签署情况", "核心内容"]
            summary_obj = {k: v for k, v in analysis_data.items() if k in summary_fields}
            if summary_obj:
                std["合同摘要"] = summary_obj
        if "潜在风险条款" in analysis_data:
            std["潜在风险条款"] = analysis_data["潜在风险条款"]
        else:
            # 兼容AI只返回了风险条款数组
            for k in analysis_data:
                if isinstance(analysis_data[k], list):
                    std["潜在风险条款"] = analysis_data[k]
                    break
        if not std:
            return {"analysis": {"原始内容": result}}
        return {"analysis": std}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")

# 多轮对话接口
class Message(BaseModel):
    role: str
    content: str

class ChatHistory(BaseModel):
    messages: List[Message]

@router.post("/chat/")
async def chat(history: ChatHistory):
    try:
        messages = [{"role": m.role, "content": m.content} for m in history.messages]
        response = client.chat.completions.create(
            model="x1",
            messages=messages,
            temperature=0.2,
            max_tokens=1024
        )
        reply = response.choices[0].message.content
        return {"reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"对话失败: {str(e)}")