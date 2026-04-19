@echo off
chcp 65001 >nul
echo ======================================================================
echo YOLOv5 + 注意力机制 - 第二阶段训练（端到端微调）
echo ======================================================================
echo.

REM Check conda
where conda >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] conda not found!
    pause
    exit /b 1
)

REM Check environment
conda env list | findstr /C:"AiDiagnosis-3.12" >nul
if %errorLevel% neq 0 (
    echo [ERROR] Environment AiDiagnosis-3.12 not found!
    pause
    exit /b 1
)

REM Check dataset config
if not exist "data\tongue.yaml" (
    echo [ERROR] Dataset config not found: data\tongue.yaml
    pause
    exit /b 1
)

REM Check training script
if not exist "train_yolov5_attention.py" (
    echo [ERROR] Training script not found: train_yolov5_attention.py
    pause
    exit /b 1
)

echo [Environment] AiDiagnosis-3.12
echo [Config] data\tongue.yaml
echo [Script] train_yolov5_attention.py
echo.

REM Training parameters for RTX 3050 4GB
set EPOCHS=80
set BATCH=4
set IMG_SIZE=640
set WORKERS=2
set ATTENTION_TYPE=cbam

echo [Training Parameters - Stage 2 End-to-End Fine-tuning]
echo   Epochs: %EPOCHS%
echo   Batch Size: %BATCH% (optimized for 4GB VRAM)
echo   Image Size: %IMG_SIZE%
echo   Workers: %WORKERS%
echo   Attention Type: %ATTENTION_TYPE%
echo.

REM Find Stage 1 model
echo [Searching] Looking for Stage 1 model...
set STAGE1_MODEL=

REM Try to find the most recent stage model (stage15, stage14, etc.)
if exist "runs\train\tongue_cbam_stage15\weights\best.pt" (
    set STAGE1_MODEL=runs\train\tongue_cbam_stage15\weights\best.pt
    goto :found_stage1
)
if exist "runs\train\tongue_cbam_stage14\weights\best.pt" (
    set STAGE1_MODEL=runs\train\tongue_cbam_stage14\weights\best.pt
    goto :found_stage1
)
if exist "runs\train\tongue_cbam_stage1\weights\best.pt" (
    set STAGE1_MODEL=runs\train\tongue_cbam_stage1\weights\best.pt
    goto :found_stage1
)

REM If not found, search all stage directories
for /f "delims=" %%f in ('dir /b /s runs\train\*stage*\weights\best.pt 2^>nul') do (
    set STAGE1_MODEL=%%f
    goto :found_stage1
)

echo [ERROR] Stage 1 model not found!
echo Please check if Stage 1 training completed successfully
echo Expected location: runs\train\tongue_*_stage*\weights\best.pt
echo.
echo Available model files:
dir /b /s runs\train\*\weights\*.pt 2>nul
pause
exit /b 1

:found_stage1
echo [OK] Found Stage 1 model: %STAGE1_MODEL%
echo.

call conda activate AiDiagnosis-3.12
if errorlevel 1 (
    echo [ERROR] Failed to activate environment
    pause
    exit /b 1
)

echo ======================================================================
echo Starting Stage 2 Training (End-to-End Fine-tuning)
echo ======================================================================
echo.
echo [Stage 1 Model] %STAGE1_MODEL%
echo [Stage 2 Output] runs\train\tongue_%ATTENTION_TYPE%_stage2
echo.
echo [Note] This will fine-tune all layers including backbone
echo [Note] Training time: approximately 8-12 hours (RTX 3050 4GB)
echo.

pause

echo.
echo Starting training...
echo.

python train_yolov5_attention.py --data data\tongue.yaml --attention %ATTENTION_TYPE% --epochs %EPOCHS% --batch %BATCH% --img %IMG_SIZE% --device 0 --workers %WORKERS% --weights "%STAGE1_MODEL%" --name tongue_%ATTENTION_TYPE%_stage2

if errorlevel 1 (
    echo.
    echo [ERROR] Stage 2 training failed
    pause
    exit /b 1
)

echo.
echo ======================================================================
echo Stage 2 Training Complete!
echo ======================================================================
echo.

set FINAL_MODEL=runs\train\tongue_%ATTENTION_TYPE%_stage2\weights\best.pt

REM Copy model to weight directory
if exist "%FINAL_MODEL%" (
    echo Saving model to weight directory...
    copy /Y "%FINAL_MODEL%" "weight\yolov5.pt"
    if errorlevel 1 (
        echo [WARNING] Save failed, please copy manually:
        echo   copy "%FINAL_MODEL%" weight\yolov5.pt
    ) else (
        echo [SUCCESS] Model saved to: weight\yolov5.pt
        echo.
        echo [Next Step] Deploy model to application:
        echo   copy /Y weight\yolov5.pt application\net\weights\yolov5.pt
    )
) else (
    echo [ERROR] Model file not found: %FINAL_MODEL%
    echo Please check if training completed successfully
)

echo.
echo [Note] Final model: %FINAL_MODEL%
echo [Note] Model saved to: weight\yolov5.pt
echo.
pause

