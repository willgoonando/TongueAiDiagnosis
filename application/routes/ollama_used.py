"""与本地 LLM（通过 Ollama 接口）进行流式对话的客户端

本模块不直接暴露 HTTP 路由，而是作为 services/chat_service.py 的下层“LLM 客户端”：
- 封装对 settings.OLLAMA_PATH（默认 http://localhost:11434/api/chat）的请求
- 提供两种流式对话方式：
  - chat_stream_first：新会话首次提问，传入舌象特征 + 用户主诉
  - chat_stream_add：在已有会话基础上追加历史对话继续提问
- 返回 Starlette 的 StreamingResponse，前端以 NDJSON（一行一个 JSON）方式消费 token

同时，它在流式输出结束后，会异步把完整回答写入 ChatRecord 表。
"""

import requests
import json
from starlette.responses import JSONResponse, StreamingResponse
from ..orm import create_new_chat_records, get_chat_record
from ..config import settings


class OllamaStreamChatter:
    def __init__(self, model=settings.LLM_NAME,
                 system_prompt=None
                 ):
        self.url = settings.OLLAMA_PATH
        self.headers = {"Content-Type": "application/json"}
        self.messages = []
        self.model = model

        if system_prompt:
            self.messages.append({
                "role": "system",
                "content": system_prompt
            })

    def chat_stream_first(self, user_input, feature, id, db, session_new_id):
        self.messages = []
        self.messages.append({"role": "user", "content": "The characteristics of the tongue are" + feature + "," + user_input + ". Answer in English"})
        data = {
            "model": self.model,
            "messages": self.messages,
            "stream": True
        }
        try:
            response = requests.post(
                self.url,
                headers=self.headers,
                json=data,
                stream=True
            )
            response.raise_for_status()

            def generate():
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        chunk = json.loads(line.decode('utf-8'))
                        if 'message' in chunk:
                            content = chunk['message']['content']
                            full_response += content
                            yield json.dumps({
                                "token": content,
                                "session_id": session_new_id,
                                "is_complete": False
                            }) + "\n"
                yield json.dumps({
                    "token": full_response,
                    "session_id": session_new_id,
                    "is_complete": True
                }) + "\n"
                self._save_to_db_async(db, full_response, session_new_id)
            return StreamingResponse(
                generate(),
                media_type='application/x-ndjson'
            )
        except requests.exceptions.RequestException as e:
            return JSONResponse(
                status_code=500,
                content={"error": f"请求失败: {str(e)}"}
            )

    def chat_stream_add(self, id, db, session_id):
        chat_record = get_chat_record(ID=id, sessionid=session_id, db=db)
        records = []
        for record in chat_record:
            role = "user" if record.role == 1 else "assistant"
            records.append({"role": role, "content": record.content})
        self.messages = records
        data = {
            "model": self.model,
            "messages": self.messages,
            "stream": True
        }
        try:
            response = requests.post(self.url, headers=self.headers, json=data, stream=True)
            response.raise_for_status()

            def generate():
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        chunk = json.loads(line.decode('utf-8'))
                        if 'message' in chunk:
                            content = chunk['message']['content']
                            full_response += content
                            yield json.dumps({
                                "token": content,
                                "session_id": session_id,
                                "is_complete": False
                            }) + "\n"
                yield json.dumps({
                    "token": full_response,
                    "session_id": session_id,
                    "is_complete": True
                }) + "\n"
                self._save_to_db_async(db, full_response, session_id)
            return StreamingResponse(
                generate(),
                media_type='application/x-ndjson'
            )
        except requests.exceptions.RequestException as e:
            return JSONResponse(
                status_code=500,
                content={"error": f"请求失败: {str(e)}"}
            )

    def chat_stream_messages(self, messages, db, session_id):
        """
        通用的流式对话接口（扩展功能使用）：
        - messages: OpenAI 风格的消息列表 [{"role": "...", "content": "..."}]
        - 返回 NDJSON 流式 token，并在结束后把完整回答异步写入 ChatRecord(role=2)
        """
        self.messages = messages
        data = {
            "model": self.model,
            "messages": self.messages,
            "stream": True
        }
        try:
            response = requests.post(self.url, headers=self.headers, json=data, stream=True)
            response.raise_for_status()

            def generate():
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        chunk = json.loads(line.decode('utf-8'))
                        if 'message' in chunk:
                            content = chunk['message']['content']
                            full_response += content
                            yield json.dumps({
                                "token": content,
                                "session_id": session_id,
                                "is_complete": False
                            }) + "\n"
                yield json.dumps({
                    "token": full_response,
                    "session_id": session_id,
                    "is_complete": True
                }) + "\n"
                self._save_to_db_async(db, full_response, session_id)
            return StreamingResponse(
                generate(),
                media_type='application/x-ndjson'
            )
        except requests.exceptions.RequestException as e:
            return JSONResponse(
                status_code=500,
                content={"error": f"请求失败: {str(e)}"}
            )

    def _save_to_db_async(self, db, content, session_id):
        import threading
        def save_task():
            try:
                create_new_chat_records(
                    db=db,
                    content=content,
                    session_id=session_id,
                    role=2
                )
            except Exception as e:
                print(f"数据库保存失败: {e}")

        threading.Thread(target=save_task).start()
