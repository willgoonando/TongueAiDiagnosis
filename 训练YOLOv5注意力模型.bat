@echo off
chcp 65001 >nul
echo ======================================================================
echo Training YOLOv5 with Attention Mechanism
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
set EPOCHS=100
set BATCH=4
set IMG_SIZE=640
set WORKERS=2
set FREEZE_BACKBONE=false

echo [Training Parameters - RTX 3050 4GB Optimized]
echo   Epochs: %EPOCHS%
echo   Batch Size: %BATCH% (optimized for 4GB VRAM)
echo   Image Size: %IMG_SIZE%
echo   Workers: %WORKERS% (reduced to avoid virtual memory issues)
echo.

REM Ask about attention type
echo Select Attention Type:
echo   1. CBAM (Convolutional Block Attention Module) - Recommended
echo   2. SE (Squeeze-and-Excitation)
echo   3. ECA (Efficient Channel Attention)
echo.
set /p att_choice="Choose (1/2/3, default 1): "
if "%att_choice%"=="2" (
    set ATTENTION_TYPE=se
) else (
    if "%att_choice%"=="3" (
        set ATTENTION_TYPE=eca
    ) else (
        set ATTENTION_TYPE=cbam
    )
)

echo.
echo Selected Attention Type: %ATTENTION_TYPE%
echo.

REM Ask about freeze backbone
echo Freeze Backbone first?
echo   1. Yes - Freeze backbone for 20 epochs, then end-to-end training (Recommended)
echo   2. No - Direct end-to-end training
echo.
set /p choice="Choose (1/2, default 1): "
if "%choice%"=="2" (
    set FREEZE_BACKBONE=false
) else (
    set FREEZE_BACKBONE=true
    set STAGE1_EPOCHS=20
    set STAGE2_EPOCHS=80
)

call conda activate AiDiagnosis-3.12
if errorlevel 1 (
    echo [ERROR] Failed to activate environment
    pause
    exit /b 1
)

REM Create weight directory if not exists
if not exist "weight" (
    echo Creating weight directory...
    mkdir weight
    echo [OK] weight directory created
) else (
    echo [OK] weight directory exists
)

echo.
echo ======================================================================
echo Starting Training
echo ======================================================================
echo.
echo [Note] Model will be saved to: weight\yolov5.pt
echo [Note] Please manually replace application\net\weights\yolov5.pt
echo.

if "%FREEZE_BACKBONE%"=="true" (
    echo [Stage 1] Freeze Backbone, train attention module (%STAGE1_EPOCHS% epochs)
    echo.
    python train_yolov5_attention.py --data data\tongue.yaml --attention %ATTENTION_TYPE% --epochs %STAGE1_EPOCHS% --batch %BATCH% --img %IMG_SIZE% --device 0 --workers %WORKERS% --freeze-backbone --name tongue_%ATTENTION_TYPE%_stage1
    
    if errorlevel 1 (
        echo [ERROR] Stage 1 training failed
        pause
        exit /b 1
    )
    
    REM Check if stage1 model exists (try multiple possible names)
    set STAGE1_MODEL=runs\train\tongue_%ATTENTION_TYPE%_stage1\weights\last.pt
    if not exist "%STAGE1_MODEL%" (
        REM Try to find the actual model file
        for /f "delims=" %%f in ('dir /b /s runs\train\tongue_%ATTENTION_TYPE%*stage*\weights\last.pt 2^>nul') do (
            set STAGE1_MODEL=%%f
            goto :found_stage1
        )
        echo [WARNING] Stage 1 model not found at expected path: %STAGE1_MODEL%
        echo [INFO] Searching for model files...
        dir /b /s runs\train\*stage*\weights\*.pt 2>nul
        echo.
        echo [INFO] Please check the training output above for the actual model path
        echo [INFO] You can manually continue to stage 2 by specifying the model path
        pause
        exit /b 1
        :found_stage1
    )
    
    echo.
    echo [Stage 2] End-to-end fine-tuning (%STAGE2_EPOCHS% epochs)
    echo [Loading] Stage 1 model: %STAGE1_MODEL%
    echo.
    python train_yolov5_attention.py --data data\tongue.yaml --attention %ATTENTION_TYPE% --epochs %STAGE2_EPOCHS% --batch %BATCH% --img %IMG_SIZE% --device 0 --workers %WORKERS% --weights "%STAGE1_MODEL%" --name tongue_%ATTENTION_TYPE%_stage2
    
    if errorlevel 1 (
        echo [ERROR] Stage 2 training failed
        pause
        exit /b 1
    )
    
    set FINAL_MODEL=runs\train\tongue_%ATTENTION_TYPE%_stage2\weights\best.pt
) else (
    echo [Single Stage] End-to-end training (%EPOCHS% epochs)
    echo.
    python train_yolov5_attention.py --data data\tongue.yaml --attention %ATTENTION_TYPE% --epochs %EPOCHS% --batch %BATCH% --img %IMG_SIZE% --device 0 --workers %WORKERS% --name tongue_%ATTENTION_TYPE%
    
    if errorlevel 1 (
        echo [ERROR] Training failed
        pause
        exit /b 1
    )
    
    set FINAL_MODEL=runs\train\tongue_%ATTENTION_TYPE%\weights\best.pt
)

echo.
echo ======================================================================
echo Training Complete!
echo ======================================================================
echo.
echo Best Model: %FINAL_MODEL%
echo.

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
        echo [Next Step] Please manually replace application\net\weights\yolov5.pt
        echo   Command: copy /Y weight\yolov5.pt application\net\weights\yolov5.pt
    )
) else (
    echo [ERROR] Model file not found: %FINAL_MODEL%
    echo Please check if training completed successfully
)

echo.
echo [Note] Model format: .pt (YOLOv5 standard format)
echo [Note] Model saved to: weight\yolov5.pt
echo [Note] Original training model: %FINAL_MODEL%
echo.
pause
