@echo off
setlocal

:: 配置参数
set VENV_DIR=.venv
set LOG_FILE=update_log.txt

echo 检查Python是否已安装...
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo 错误: 未找到Python，请先安装Python。
    exit /b 1
)

:: 创建虚拟环境（如果不存在）
if not exist %VENV_DIR%\ (
    echo 创建虚拟环境...
    python -m venv %VENV_DIR%
    if %ERRORLEVEL% neq 0 (
        echo 错误: 创建虚拟环境失败。
        exit /b 1
    )
)

:: 设置虚拟环境路径
set VENV_PYTHON=%VENV_DIR%\Scripts\python.exe
set VENV_PIP=%VENV_DIR%\Scripts\pip.exe

:: 检查更新服务是否已在运行
tasklist /FI "IMAGENAME eq python.exe" /FO CSV | findstr /I "update_index.py" >nul
if %ERRORLEVEL% equ 0 (
    echo 更新服务已在运行。
    exit /b 0
)

:: 在虚拟环境中安装依赖
echo 安装依赖...
%VENV_PIP% install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo 错误: 安装依赖失败。
    exit /b 1
)

:: 启动服务（在虚拟环境中）
echo 启动更新服务...
start /B "" %VENV_PYTHON% update_index.py > %LOG_FILE% 2>&1

:: 等待一会儿确保进程启动
timeout /t 2 /nobreak >nul

:: 检查是否成功启动
tasklist /FI "IMAGENAME eq python.exe" /FO CSV | findstr /I "update_index.py" >nul
if %ERRORLEVEL% equ 0 (
    echo 更新服务已成功启动！
    echo 日志文件: %LOG_FILE%
) else (
    echo 错误: 启动更新服务失败。
    echo 请查看日志文件了解详情: %LOG_FILE%
    exit /b 1
)

endlocal 