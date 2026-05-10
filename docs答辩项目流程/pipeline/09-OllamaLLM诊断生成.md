# 09 — Ollama 本地 LLM 诊断生成

**相关文件**: `application/routes/ollama_used.py` + `config.py`

## 作用

ResNet 输出的是四个数值（如 [1, 0, 0, 0]），需要转成自然语言诊断建议。这里调用了本地运行的 Deepseek-R1 模型，把数值特征翻译成中医诊断。

## 调用链路

```
model_api.py 获取到特征 → 格式化为文字 → 调 Ollama → 流式返回
```

## 特征格式化

```python
# model_api.py 中
def format_tongue_features(tongue_color, coating_color, thickness, rot_greasy):
    color_map = ["淡白舌", "淡红舌", "红舌", "绛舌", "青紫舌"]
    coating_map = ["白苔", "黄苔", "灰黑苔"]
    thickness_map = ["薄", "厚"]
    rot_map = ["正常", "腐腻"]
    
    return f"舌色：{color_map[tongue_color]}；苔色：{coating_map[coating_color]}；" \
           f"舌体厚薄：{thickness_map[thickness]}；腐腻情况：{rot_map[rot_greasy]}"
```

## Ollama 调用

**文件**: `routes/ollama_used.py`

```python
async def call_ollama_stream(user_input, feature_text, session_id, db):
    # 构造系统提示词（自定义老中医角色）
    system_prompt = settings.SYSTEM_PROMPT  # 见下方
    
    # 构造请求 payload
    payload = {
        "model": settings.LLM_NAME,  # deepseek-r1:8b
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"舌象特征：{feature_text}\n用户主诉：{user_input}"}
        ],
        "stream": True,
        "options": {"num_predict": settings.OLLAMA_NUM_PREDICT}
    }
    
    # POST 到本地 Ollama
    async with httpx.AsyncClient() as client:
        async with client.stream("POST", settings.OLLAMA_PATH, json=payload) as response:
            async for chunk in response.aiter_lines():
                yield chunk  # SSE 格式返回
```

## 系统提示词（精心设计）

```python
# config.py
SYSTEM_PROMPT = (
    "你现在是一位精通中医舌诊的AI老中医。"
    "用户上传了舌象图片，我已经通过AI模型（YOLOv5+SAM+ResNet）自动分析并识别出了舌象特征，包括："
    "舌色、苔色、舌体厚薄、腐腻情况等。"
    "我会将这些AI分析得到的特征提供给你，同时还有用户的主诉。"
    "请你基于这些特征，运用中医舌诊的专业知识进行辨证分析，"
    "并给出个性化的调理建议（包括饮食、生活习惯、注意事项等）。"
    "请用亲切、专业的中文回答。"
)
```

**设计要点**：
- 明确告知 LLM "特征已经通过 AI 模型分析出来了"
- 让 LLM 回答看起来像"老中医"的调理建议
- 避免 LLM 说"我看不到图片"——这种回复对用户不友好

## 流式响应（SSE）

前端接收流式 token 逐字显示，体验更好：

```json lines
{"token": "根", "is_complete": false}
{"token": "据", "is_complete": false}
{"token": "您", "is_complete": false}
...
{"token": "", "is_complete": true}
```

## 配置

```python
# config.py
OLLAMA_PATH: str = "http://localhost:11434/api/chat"
LLM_NAME: str = "deepseek-r1:8b"
OLLAMA_NUM_PREDICT: int = 1200  # 最多生成 1200 个 token
```

## 亮点

- **完全本地运行**：不需要联网、不需要 API 费用、数据不出本地
- **流式体验**：不用等全部生成完，逐字显示降低等待感
- **可替换模型**：换 `LLM_NAME` 就能用其他 Ollama 模型（如 qwen2.5）
