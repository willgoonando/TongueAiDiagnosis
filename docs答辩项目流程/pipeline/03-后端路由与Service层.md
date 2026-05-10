# 03 — 后端路由与 Service 层

接口入口 → 业务逻辑 → 触发 AI 推理

## 文件调用链

```
routes/model_api.py ──► services/tongue_service.py ──► net/predict.py
     Controller                 Service                     AI Engine
```

## 路由层：`routes/model_api.py`

### `POST /api/model/session` — 上传图片创建会话（核心接口）

```python
@router_tongue_analysis.post('/session')
async def upload(file_data: UploadFile = File(...),
                 user_input: str = Form(...),
                 name: str = Form(...),
                 user: ..., db: ...):
    # 1. 舌象分析
    features: TongueFeatures = analyse_tongue_image(
        img_file=file_data, user_id=user.id, db=db,
    )
    if features.code != 0:
        return error("图片有问题")

    # 2. 格式化特征为文字
    feature_text = format_tongue_features(
        features.tongue_color, features.coating_color,
        features.tongue_thickness, features.rot_greasy,
    )
    # 结果示例: "舌色：淡红舌；苔色：白苔；舌体厚薄：薄；腐腻情况：正常"

    # 3. 创建对话记录
    session_new_id = create_session_with_first_message(...)

    # 4. 调用 LLM 生成诊断建议（SSE 流式返回）
    return stream_first_answer(user_input, feature_text, ...)
```

### `POST /api/model/session/{sessionId}` — 继续对话
追加用户消息 → 调 LLM 流式回复

### `GET /api/model/record/{sessionid}` — 获取历史记录
### `GET /api/model/session` — 获取会话列表

## Service 层：`services/tongue_service.py`

### `analyse_tongue_image()` — 核心分析函数

```python
def analyse_tongue_image(img_file, user_id, db):
    # 1. 保存图片到磁盘
    img_src = save_tongue_image(img_file)
    
    # 2. 写入数据库（state=0 处理中）
    record_id = create_tongue_analysis_record(...)
    
    # 3. 构造回调函数（推理完成时调用，写入结果）
    def fun(event_id, tongue_color, coating_color,
            tongue_thickness, rot_greasy, code):
        update_tongue_analysis_record(...)  # 更新 state=1
    
    # 4. 触发 AI 推理（异步，塞入队列即返回）
    tonguePredictor = TonguePredictor()      # 单例
    tonguePredictor.predict(img_file, record_id, fun)
    
    # 5. 轮询等待结果（同步阻塞方式）
    while True:
        record = get_tongue_analysis_record(record_id)
        if record.state != 0:  # 推理完成
            return TongueFeatures(
                code=record.state,
                tongue_color=record.tongue_color,
                ...
            )
        time.sleep(0.5)
```

**关键设计**：推理引擎是异步队列执行的，但 Service 层用轮询等待结果，对外表现为同步接口。

## 路由聚合：`routes/__init__.py`

```python
def register_routes(app):
    app.include_router(router_user, prefix="/api/user")
    app.include_router(router_tongue_analysis, prefix="/api/model")
    app.include_router(router_extra, prefix="/api/extra")
    app.include_router(router_pipeline, prefix="/api")  # 新增
```
