"""全局配置定义模块

本模块提供后端用到的关键配置项（类似 Java 中的 application.yml / 配置类），包括：
- 访问令牌过期时间、JWT 密钥和算法
- 图片保存路径（磁盘路径 + 数据库存储相对路径）
- 本地 LLM 服务（Ollama）的访问地址与模型名称
- FastAPI 应用监听端口

这些配置会在 application.core.authentication、services 和 routes 等模块中使用。
"""

class Settings:
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    SECRET_KEY: str = "f2e1f1b1c1a1"
    ALGORITHMS: str = "HS256"
    IMG_PATH: str = "frontend/public/tongue"
    IMG_DB_PATH: str = "tongue"
    OLLAMA_PATH: str = "http://localhost:11434/api/chat"
    #SYSTEM_PROMPT: str = "You are now an AI traditional Chinese medicine doctor specializing in tongue diagnosis. At the very beginning, I will show you four image features of the user's tongue. Please use your knowledge of traditional Chinese medicine to give the user some suggestions. Answer in English"
    # 中文回答
    SYSTEM_PROMPT: str = "你现在是一位精通中医舌诊的AI老中医。我会给你用户的舌象特征（如舌色、苔色等）和用户的主诉。请你用中医的专业知识，结合这些特征进行辨证分析，并给出调理建议（包括饮食、生活习惯等）。请用亲切、专业的中文回答。"
    LLM_NAME: str = "deepseek-r1:8b"
    APP_PORT: int = 5000

    # ===== 扩展功能：场景化 Prompt（报告解读 / 药盒识别）=====
    REPORT_SYSTEM_PROMPT: str = (
        "你是一位擅长解读体检/化验/检查报告的AI医生（偏中西结合）。"
        "我会提供用户的报告原文或OCR文本，请你用中文输出："
        "1) 关键指标/结论摘要；2) 可能代表的意义与常见原因；3) 需要警惕的风险与就医建议；"
        "4) 生活方式/饮食/复查建议。"
        "注意：不要编造不存在的数值；不确定时要提示用户补充信息。"
    )

    DRUGBOX_SYSTEM_PROMPT: str = (
        "你是一位擅长解读药盒/说明书的AI药师。"
        "我会提供药盒图片OCR文本，以及用户的问题。请你用中文输出："
        "1) 药品名称/成分（若能识别）；2) 适应症/用途；3) 常见用法用量（若文本包含）；"
        "4) 禁忌与注意事项（孕妇、儿童、肝肾功能、饮酒等）；5) 与用户问题的对应建议。"
        "注意：如果OCR信息不完整，请明确说明并建议用户提供更清晰图片或补充文字。"
    )
