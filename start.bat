@echo off
echo ========================================
echo 模型训练管理系统 - 启动脚本
echo ========================================
echo.

REM 检查虚拟环境
if exist venv\Scripts\activate.bat (
    echo 激活虚拟环境...
    call venv\Scripts\activate.bat
) else (
    echo 虚拟环境不存在，使用系统 Python
)

echo.
echo 启动 Flask 应用...
echo 访问地址：http://localhost:5000
echo.

python run.py
