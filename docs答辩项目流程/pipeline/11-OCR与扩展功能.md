# 11 — OCR 与扩展功能

## 功能概述

除了核心的舌诊分析，系统还集成了 OCR 识别和两个 LLM 辅助功能。

## EasyOCR 集成

**文件**: `services/ocr_service.py`

```python
import easyocr

class OCRService:
    def __init__(self):
        # 离线加载中文+英文模型
        self.reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)
    
    def recognize(self, image_path):
        # 返回识别的文字列表
        result = self.reader.readtext(image_path)
        return " ".join([text for _, text, conf in result])
```

配置了 `DOWNLOAD_ENABLED=False`，确保推理过程中不会联网下载。

## 两个扩展场景

### 1. 报告解读

**路由**: `routes/extra_api.py` → `POST /api/extra/report/image`

用户上传体检报告照片 → OCR 识别文字 → Ollama 解读报告

系统提示词：
```
你是一位擅长解读体检/化验/检查报告的AI医生（偏中西结合）。
输出：1) 关键指标摘要；2) 可能代表的意义；3) 就医建议；4) 生活建议。
```

### 2. 药盒识别

**路由**: `routes/extra_api.py` → `POST /api/extra/drugbox/image`

用户上传药盒照片 → OCR 识别药品名称和说明 → Ollama 回答用药问题

系统提示词：
```
你是一位擅长解读药盒的AI药师。
输出：1) 药品名称/成分；2) 适应症；3) 用法用量；4) 禁忌与注意事项。
```

## 前端入口

聊天页面底部的 `ChatInput.vue` 中有三个类目切换：
- 🧪 **舌苔检测** — 舌象流水线
- 📄 **报告解读** — OCR + LLM
- 💊 **药盒识别** — OCR + LLM

## 技术栈优势

OCR → LLM 这条链路是离线可运行的，不需要调用任何云端 API，数据全程在本地。
