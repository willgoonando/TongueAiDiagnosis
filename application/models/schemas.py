"""Pydantic 数据模型与接口返回结构定义

本模块定义了所有通过 FastAPI 对外暴露的请求/响应模型（类似 Java 中的 DTO/VO）：
- UserRegister / UserLogin / UserBase 等：用户相关请求体 / 基础信息
- Result / Record / RecordResponse：舌象分析结果与历史记录返回结构
- ChatRecordResponse / ChatSessionRecordsResponse：对话记录返回结构
- SessionId / SessionIdResponse：会话列表返回结构
- BaseResponse 及其子类：统一的后端响应格式（code、message、data）

这些模型主要用于：
- routes 层的 request body / response_model
- service 层在构造返回数据时保持结构一致
"""

import time
from pydantic import BaseModel,Field
from typing import Union, Annotated, Optional
from fastapi.param_functions import Form
from typing import List


class BaseResponse(BaseModel):
    code: int
    message: str
    data: Union[dict, list] = None


class Token(BaseModel):
    token: str


class UserBase(BaseModel):
    ID: int = None
    email: str


class UserAuth(UserBase):
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserRegister(BaseModel):
    email: str
    password: str


class Result(BaseModel):
    tongue_color: Optional[int] = None
    coating_color: Optional[int] = None
    tongue_thickness: Optional[int] = None
    rot_greasy: Optional[int] = None


class Record(BaseModel):
    ID: int
    user_ID: int
    img_src: str
    state: int = None
    result: Optional[Result] = None


class LoginResponse(BaseResponse):
    data: Union[Token, None]


class RegisterResponse(BaseResponse):
    pass


class InfoResponse(BaseResponse):
    data: Union[UserBase, None]


class RecordResponse(BaseResponse):
    data: list[Record]


class UploadResponse(BaseResponse):
    data: None


class ExtendedOAuth2PasswordRequestForm:
    def __init__(
            self,
            *,
            email: Annotated[str, Form()],
            password: Annotated[str, Form()],
    ):
        self.email = email
        self.password = password


class ChatRecordResponse(BaseModel):
    content: str
    create_at: int = Field(default_factory=lambda: int(time.time() * 1000))
    role: int


class ChatSessionRecordsResponse(BaseModel):
    code: int
    message: str
    data: dict[str, List[ChatRecordResponse]]


class SessionId(BaseModel):
    session_id: int
    name: str


class SessionIdResponse(BaseModel):
    code: int
    message: str
    data: List[SessionId]
