@echo off
chcp 65001 >nul
echo ======================================================================
echo 项目启动检查工具
echo ======================================================================
echo.

REM 检查 conda 是否可用
where conda >nul 2>&1
if %errorLevel% neq 0 (
    echo [错误] conda 命令未找到！
    echo 请确保 Anaconda 已安装并添加到 PATH
    echo 或使用 Anaconda Prompt 运行此脚本
    pause
    exit /b 1
)

REM 检查环境是否存在
conda env list | findstr /C:"AiDiagnosis-3.12" >nul
if %errorLevel% neq 0 (
    echo [错误] 环境 AiDiagnosis-3.12 不存在！
    echo 请先创建 conda 环境: conda create -n AiDiagnosis-3.12 python=3.12
    pause
    exit /b 1
)

REM 激活环境
call conda activate AiDiagnosis-3.12
if %errorLevel% neq 0 (
    echo [错误] 环境激活失败
    pause
    exit /b 1
)

echo [1] 检查 Python 版本...
python --version
echo.

echo [2] 检查核心依赖...
python -c "import fastapi; import uvicorn; import torch; import ultralytics; print('[OK] 核心依赖正常')" 2>nul
if %errorLevel% neq 0 (
    echo [错误] 核心依赖检查失败
    goto :error
)
echo.

echo [3] 检查应用导入...
python -c "from application import create_app; print('[OK] 应用导入成功')" 2>nul
if %errorLevel% neq 0 (
    echo [错误] 应用导入失败
    goto :error
)
echo.

echo [4] 检查配置...
python -c "from application.config import settings; print('[OK] 配置加载成功'); print('端口:', settings.APP_PORT)" 2>nul
if %errorLevel% neq 0 (
    echo [错误] 配置加载失败
    goto :error
)
echo.

echo [5] 检查数据库...
python -c "from application.models.database import engine; print('[OK] 数据库引擎正常')" 2>nul
if %errorLevel% neq 0 (
    echo [警告] 数据库检查失败
)
echo.

echo [6] 检查模型文件...
if exist ".\application\net\weights\yolov5.pt" (
    echo [OK] YOLOv5 模型文件存在
) else (
    echo [警告] YOLOv5 模型文件不存在
)
echo.

echo ======================================================================
echo 检查完成！如果所有项目都显示 [OK]，项目应该可以正常启动
echo ======================================================================
echo.
echo 启动项目: 运行 启动项目.bat 或 python run.py
echo.
pause
exit /b 0

:error
echo.
echo ======================================================================
echo 检查失败！请修复上述错误后重试
echo ======================================================================
pause
exit /b 1
