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
    # 中文回答 - 明确说明这是基于AI模型分析得到的特征
    SYSTEM_PROMPT: str = (
        "你是中医舌诊AI助手。以下舌象特征已由AI模型分析得出：舌色、苔色、舌体厚薄、腐腻情况。"
        "请结合特征和用户主诉，用100字左右给出：辨证分析 + 饮食生活习惯建议。"
        "简短直接，不要提及看不到图片。"
    )
    LLM_NAME: str = "deepseek-r1:8b"
    APP_PORT: int = 5000

    # Ollama 推理模型（如 deepseek-r1）默认会把长链推理放在 message.thinking，
    # message.content 在推理结束前几近为空；本系统前端只拼接 content 时会一直显示“加载中”。
    # False：请求 Ollama 尽量直接生成正文（需较新版本 Ollama；若无效可改 True 并依赖下方转发 thinking）。
    OLLAMA_THINK: bool = False
    # 若本机 Ollama 版本过旧、不识别 think 字段并报错，可改为 False 以从请求体中省略该字段
    OLLAMA_SEND_THINK_FIELD: bool = True
    # 限制单次回复最大生成 token，略短可加快结束；None 表示不限制（不传 options）
    OLLAMA_NUM_PREDICT: int | None = 1200

    # 舌象推理设备：默认 cpu 与旧版一致；改为 auto 可在有 CUDA 时加速 YOLO/SAM/ResNet，
    # 若与 Ollama 共用同一块 GPU 且显存较小（如 4GB），可能出现 OOM，此时保持 cpu 或让 Ollama 用 CPU。
    TORCH_DEVICE: str = "auto"  # auto | cuda | cpu

    # EasyOCR：模型应位于用户目录 .EasyOCR/model（请运行「下载EasyOCR模型.bat」）。
    # False 表示运行中绝不联网下载（推荐）；若改 True，无代理时可能再次超时。
    EASYOCR_DOWNLOAD_ENABLED: bool = False

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
