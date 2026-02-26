"""用户相关业务逻辑层

本模块对应 Java 项目中的 UserService，专门负责：
- 用户注册：调用 ORM 层写入 User 表，返回统一的 RegisterResponse
- 用户登录：校验账号密码并生成 JWT，返回统一的 LoginResponse
- 查询当前用户基本信息与历史舌诊记录

注意：
- 不直接处理 HTTP 请求，也不关心路由，只被 routes/user_api.py 调用
- 具体的数据库操作委托给 application.orm.crud.auth_user 中的函数
"""

from sqlalchemy.orm import Session

from application.core.authentication import create_access_token
from application.models import schemas
from application.orm import register_user, login_user, get_user, get_user_record


def register_user_service(schema: schemas.UserRegister, db: Session) -> schemas.RegisterResponse:
    """
    负责用户注册的业务逻辑：
    - 使用 ORM 层的 register_user 写入数据库
    - 根据返回 code 构造统一的 RegisterResponse
    """
    code = register_user(email=schema.email, password=schema.password, db=db)

    if code == 0:
        message = "operation success"
    elif code == 101:
        message = "has been registered"
    else:
        message = "operation failed"

    return schemas.RegisterResponse(code=code, message=message, data=None)


def login_user_service(form_data: schemas.ExtendedOAuth2PasswordRequestForm, db: Session) -> schemas.LoginResponse:
    """
    负责登录的业务逻辑：
    - 校验账号密码
    - 正确时生成 JWT Token
    - 统一返回 LoginResponse
    """
    email = form_data.email
    password = form_data.password

    code = login_user(email=email, password=password, db=db)

    if code == 0:
        user = get_user(email=email, db=db)
        token = create_access_token(data={"ID": user.id, "email": email})
        return schemas.LoginResponse(
            code=code,
            message="operation success",
            data=schemas.Token(token=token),
        )

    # 账号不存在 / 其他错误
    if code == 101:
        message = "operation failed"
    else:
        # 102: 密码错误等
        message = "wrong password"

    return schemas.LoginResponse(
        code=code,
        message=message,
        data=None,
    )


def get_user_info_service(user) -> schemas.InfoResponse:
    """
    获取当前登录用户基本信息。
    user 由 get_current_user 注入，如果为 None 视为未登录。
    """
    if not user:
        return schemas.InfoResponse(
            code=101,
            message="operation failed",
            data=None,
        )

    user_data = schemas.UserBase(
        ID=user.id,
        email=user.email,
    )

    return schemas.InfoResponse(
        code=0,
        message="operation success",
        data=user_data,
    )


def get_user_record_service(user, db: Session) -> schemas.RecordResponse:
    """
    获取用户历史舌诊记录。
    """
    if not user:
        return schemas.RecordResponse(
            code=101,
            message="operation failed",
            data=[],
        )

    records = get_user_record(ID=user.id, db=db)
    data_list: list[schemas.Record] = []

    for record in records:
        data_list.append(
            schemas.Record(
                ID=record.id,
                user_ID=record.user_id,
                img_src=record.img_src,
                state=record.state,
                result=schemas.Result(
                    tongue_color=record.tongue_color,
                    coating_color=record.coating_color,
                    tongue_thickness=record.tongue_thickness,
                    rot_greasy=record.rot_greasy,
                ),
            )
        )

    return schemas.RecordResponse(
        code=0,
        message="operation success",
        data=data_list,
    )


