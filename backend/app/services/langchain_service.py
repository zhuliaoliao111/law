import sqlite3
import os
from typing import Optional, List, Dict
import httpx
from pathlib import Path
import logging
import uuid
#python -m uvicorn app.main:app --reload

# 数据库初始化
DB_PATH = Path(__file__).parent.parent.parent.parent / 'ai_legal_history.db'
logging.debug(f"数据库路径：{DB_PATH}")
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    model TEXT,
    question TEXT,
    answer TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)''')
conn.commit()
conn.close()

# 定义MODEL_CONFIG字典
MODEL_CONFIG = {
    '通义千问': {
        'api_key': 'sk-b6e2d7265f074523b730f7fcd4d9901c',
        'endpoint': 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation',
        'model': 'qwen-turbo',
    },
    '星火大模型': {
        'api_key': 'ca9932b6d57bda0f180f1d89c3095379:Mjc5ZTg3N2Q5Njg5MjA2YjA4MzllMGU4',
        'endpoint': 'https://spark-api-open.xf-yun.com/v2/chat/completions',
        'model': 'x1',
    },
    '文心一言': {
        'api_key': 'bce-v3/ALTAK-nyvpC0PgBgMaNoosj1u1A/fecf04dccf162e50a875bda264225ca649ad53d9',
        'endpoint': 'https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions',
        'model': 'ernie-3.5-8k',
    },
    'deepseek': {
        'api_key': 'sk-797153ca196f4976819ae4eeb4c0751b',
        'endpoint': 'https://api.deepseek.com/v1/chat/completions',
        'model': 'deepseek-chat',
    },
    '智谱':{
        'endpoint':'https://open.bigmodel.cn/api/paas/v4/chat/completions',
        'api_key':'eb686c9b124449619183a615a57497f5.Qes2AeKa07ZqsAjl',
        'model': 'glm-4',
},

}

# 1. 保存历史
def save_history(session_id: str, model: str, question: str, answer: str):
    logging.debug(f"保存数据：session_id={session_id}, model={model}, question={question}")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO chat_history (session_id, model, question, answer) VALUES (?, ?, ?, ?)',
              (session_id, model, question, answer))
    conn.commit()
    conn.close()

# 2. 获取历史
def get_history(session_id: str) -> List[Dict]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT question, answer, model, timestamp FROM chat_history WHERE session_id=? ORDER BY id', (session_id,))
    rows = c.fetchall()
    conn.close()
    return [{'question': r[0], 'answer': r[1], 'model': r[2], 'timestamp': r[3]} for r in rows]


def ai_legal_qa_function(question: str, model: str = 'qwen-turbo', session_id: Optional[str] = None) -> dict:
    if session_id is None:
        session_id = str(uuid.uuid4())
    logging.debug(f"[DEBUG] 收到的 session_id: {session_id}")
    import re
    history = get_history(session_id) if session_id else []

    #构建提示词
    # 3. 构造prompt时，将最近历史问答内容拼接到prompt前面
    history_prompt = ''
    if history:
        for idx, h in enumerate(history[-3:]):
            history_prompt += f"\n历史问题{idx+1}: {h['question']}\n历史回答{idx+1}: {h['answer']}\n"
    prompt = (
        f"请你作为专业法律助手，严格参考用户的历史提问，结合历史问题的关键词，再结合当前问题，严格按照以下格式分四部分输出：\n"
        f"{history_prompt}"
        f"当前问题：{question}\n"
        f"1. 法律条文依据：\n[在这里详细列出相关的法律条文和依据]\n\n"
        f"2. 参考案例：\n[在这里提供相关的参考案例]\n\n"
        f"3. 实际解决办法：\n[在这里提供具体的解决步骤和建议]\n"
        f"4. 总结回答：\n[在这里总结总体的回答，包括法律条文依据、参考案例和实际解决办法，并针对问���给出具体的回答]\n"
    )
    answer = ''
    if model == '通义千问':
        headers = {
            'Authorization': f"Bearer {MODEL_CONFIG[model]['api_key']}",
            'Content-Type': 'application/json'
        }
        payload = {
            'model': MODEL_CONFIG[model]['model'],
            'input': {'prompt': prompt},
            'parameters': {'result_format': 'message'}
        }
        try:
            resp = httpx.post(MODEL_CONFIG[model]['endpoint'], headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            answer = resp.json().get('output', {}).get('text', resp.text)
        except Exception as e:
            answer = f"通义千问接口异常: {e}"
    elif model == '星火大模型':
        headers = {
            'Authorization': f"Bearer {MODEL_CONFIG[model]['api_key']}",
            'Content-Type': 'application/json'
        }
        payload = {
            'model': MODEL_CONFIG[model]['model'],
            'messages': [{'role': 'user', 'content': prompt}],
            'parameters': {'result_format': 'message'}
        }
        
        # 重试机制
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # 设置更长的超时时间
                resp = httpx.post(
                    MODEL_CONFIG[model]['endpoint'], 
                    headers=headers, 
                    json=payload, 
                    timeout=60.0  # 统一设置60秒超时
                )
                resp.raise_for_status()
                answer = resp.json().get('choices', [{}])[0].get('message', {}).get('content', resp.text)
                break  # 成功则跳出重试循环
            except httpx.TimeoutException as e:
                if attempt == max_retries - 1:  # 最后一次重试
                    answer = f"星火接口超时异常（已重试{max_retries}次）: {e}"
                else:
                    continue  # 继续重试
            except Exception as e:
                answer = f"星火接口异常: {e}"
                break
    elif model == '智谱':
        headers = {
            'Authorization': f"Bearer {MODEL_CONFIG[model]['api_key']}",
            'Content-Type': 'application/json'
        }
        payload = {
            'model': MODEL_CONFIG[model]['model'],
            'messages': [{'role': 'user', 'content': prompt}]
        }
        try:
            resp = httpx.post(MODEL_CONFIG[model]['endpoint'], headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            answer = resp.json()['choices'][0]['message']['content']
        except Exception as e:
            answer = f"智谱接口异常: {e}"
    elif model == 'deepseek':
        headers = {
            'Authorization': f"Bearer {MODEL_CONFIG[model]['api_key']}",
            'Content-Type': 'application/json'
        }
        payload = {
            'model': MODEL_CONFIG[model]['model'],
            'messages': [{'role': 'user', 'content': prompt}]
        }
        try:
            resp = httpx.post(MODEL_CONFIG[model]['endpoint'], headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            answer = resp.json()['choices'][0]['message']['content']
        except Exception as e:
            answer = f"deepseek接口异常: {e}"
    else:
        answer = f"暂未实现对{model}的API集成。"
        
    # 自动分段解析
    def parse_answer(ans):
        law, case, solution, summary = '', '', '', ''
        # 优化分割逻辑，兼容更多格式
        patterns = [
            r'1[、.、．]? ?法律条文依据[:：]?\s*(.*?)(?:\n|\r|$)2[、.、．]? ?参考案例[:：]?\s*(.*?)(?:\n|\r|$)3[、.、．]? ?实际解决办法[:：]?\s*(.*?)(?:\n|\r|$)4[、.、．]? ?总结回答[:：]?\s*(.*)',
            r'1[、.、．]? ?法律条文依据[:：]?\s*(.*?)(?:2[、.、．]? ?参考案例[:：]?)(.*?)(?:3[、.、．]? ?实际解决办法[:：]?)(.*?)(?:4[、.、．]? ?总结回答[:：]?)(.*)',
            r'1[、.、．]? ?(.*?)(2[、.、．]? ?)(.*?)(3[、.、．]? ?)(.*?)(4[、.、．]? ?)(.*)'
        ]
        for pattern in patterns:
            m = re.search(pattern, ans, re.S)
            if m:
                if len(m.groups()) == 4:
                    law = m.group(1).strip()
                    case = m.group(2).strip()
                    solution = m.group(3).strip()
                    summary = m.group(4).strip()
                elif len(m.groups()) == 5:
                    law = m.group(1).strip()
                    case = m.group(2).strip()
                    solution = m.group(3).strip()
                    summary = m.group(5).strip()
                elif len(m.groups()) == 7:
                    law = m.group(1).strip()
                    case = m.group(3).strip()
                    solution = m.group(5).strip()
                    summary = m.group(7).strip()
                break
        # 2. 如果没有分割成功，尝试按换行和数字分割
        if not law and not case:
            parts = re.split(r'\n?\d+[、.、．]?[. ]?', ans)
            parts = [p.strip() for p in parts if p.strip()]
            if len(parts) >= 4:
                law = parts[0]
                case = parts[1]
                solution = parts[2]
                summary = parts[3]
            elif len(parts) == 3:
                law = parts[0]
                case = parts[1]
                solution = parts[2]
            elif len(parts) == 2:
                law = parts[0]
                solution = parts[1]
            elif len(parts) == 1:
                solution = parts[0]
        # 3. 如果还是没有，尝试按关键词分割
        if not law and not case:
            law_match = re.search(r'法律条文依据[:：]?\s*(.*?)(参考案例[:：]?|实际解决办法[:：]?|总结回答[:：]?|$)', ans, re.S)
            if law_match:
                law = law_match.group(1).strip()
            case_match = re.search(r'参考案例[:：]?\s*(.*?)(实际解决办法[:：]?|总结回答[:：]?|$)', ans, re.S)
            if case_match:
                case = case_match.group(1).strip()
            solution_match = re.search(r'实际解决��法[:：]?\s*(.*?)(总结回答[:：]?|$)', ans, re.S)
            if solution_match:
                solution = solution_match.group(1).strip()
            summary_match = re.search(r'总结回答[:：]?\s*(.*)', ans, re.S)
            if summary_match:
                summary = summary_match.group(1).strip()
        return law, case, solution, summary
    def clean_text(text):
        import re
        # 去除markdown标题、粗体、列表等符号
        text = re.sub(r'[#*`>\-]+', '', text)
        # 去除AI返回的JSON片段和usage等调试信息
        text = re.sub(r'\{\s*"total_tokens"[\s\S]*?\}', '', text)
        text = re.sub(r'"usage"[\s\S]*?\}', '', text)
        text = re.sub(r'"request_id"[\s\S]*?\}', '', text)
        text = re.sub(r'\{\s*"cached_tokens"[\s\S]*?\}', '', text)
        # 将\n或\\n等转为真正换行
        text = text.replace('\\n', '\n').replace('\\r', '').replace('\r', '').replace('\n', '\n')
        # 连续多行空行合并为一个
        text = re.sub(r'\n{2,}', '\n', text)
        # 去除首尾空白
        text = text.strip()
        # 去除通义千问答案结尾的'}}]},,'等异常符号
        text = re.sub(r'"[}}\]\]},,]+$','', text)
        return text
    law, case, solution, summary = map(clean_text, parse_answer(answer))
    if session_id:
        save_history(session_id, model, question, answer)
    else:
        return {
            'law': law,
            'case': case,
            'solution': solution,
            'summary': summary,
            'history': [],
            'msg': '未传递session_id，无法实现记忆功能。请确保每次问答都传递同一个session_id。'
        }
    return {
        'law': law,
        'case': case,
        'solution': solution,
        'summary': summary,
        'history': history + [{'question': question, 'answer': answer, 'model': model}]
    }
