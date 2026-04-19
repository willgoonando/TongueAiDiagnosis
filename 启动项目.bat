@echo off
chcp 65001 >nul
echo ======================================================================
echo 启动 AI 诊断项目
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

echo 正在启动项目...
echo.

REM 激活 conda 环境并运行
call conda activate AiDiagnosis-3.12
if %errorLevel% neq 0 (
    echo [错误] 环境激活失败
    pause
    exit /b 1
)

python run.py

if %errorLevel% neq 0 (
    echo.
    echo [错误] 项目启动失败
    echo 错误代码: %errorLevel%
)

pause

