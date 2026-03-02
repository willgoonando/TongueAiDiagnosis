@echo off
REM Windows批处理脚本：批量训练所有4个分类任务

REM 设置数据集路径
set DATA_PATH=./data

REM 设置训练参数
set EPOCHS=50
set BATCH_SIZE=32
set LR=0.001

echo 开始训练所有分类模型...
echo 数据集路径: %DATA_PATH%
echo 训练轮数: %EPOCHS%
echo 批次大小: %BATCH_SIZE%
echo 学习率: %LR%
echo.

REM 训练舌色模型
echo ==========================================
echo 训练舌色分类模型 (tongue_color)
echo ==========================================
python train_resnet.py --task tongue_color --data_path %DATA_PATH% --epochs %EPOCHS% --batch_size %BATCH_SIZE% --lr %LR%

REM 训练苔色模型
echo ==========================================
echo 训练苔色分类模型 (tongue_coat_color)
echo ==========================================
python train_resnet.py --task tongue_coat_color --data_path %DATA_PATH% --epochs %EPOCHS% --batch_size %BATCH_SIZE% --lr %LR%

REM 训练厚度模型
echo ==========================================
echo 训练厚度分类模型 (thickness)
echo ==========================================
python train_resnet.py --task thickness --data_path %DATA_PATH% --epochs %EPOCHS% --batch_size %BATCH_SIZE% --lr %LR%

REM 训练腐腻模型
echo ==========================================
echo 训练腐腻分类模型 (rot_and_greasy)
echo ==========================================
python train_resnet.py --task rot_and_greasy --data_path %DATA_PATH% --epochs %EPOCHS% --batch_size %BATCH_SIZE% --lr %LR%

echo.
echo ==========================================
echo 所有模型训练完成！
echo ==========================================
echo 最佳模型保存在 ./checkpoints/ 目录
echo.
echo 部署模型到项目：
echo copy ./checkpoints/tongue_color_best.pth application/net/weights/tongue_color.pth
echo copy ./checkpoints/tongue_coat_color_best.pth application/net/weights/tongue_coat_color.pth
echo copy ./checkpoints/thickness_best.pth application/net/weights/thickness.pth
echo copy ./checkpoints/rot_and_greasy_best.pth application/net/weights/rot_and_greasy.pth

pause

