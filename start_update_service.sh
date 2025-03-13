#!/bin/bash

# 配置参数
VENV_DIR=".venv"
LOG_FILE="update_log.txt"

# 确保脚本可执行
chmod +x update_index.py

# 检查Python是否已安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python 3，请先安装Python 3。"
    exit 1
fi

# 创建并激活虚拟环境
if [ ! -d "$VENV_DIR" ]; then
    echo "创建虚拟环境..."
    python3 -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo "错误: 创建虚拟环境失败。"
        exit 1
    fi
fi

# 获取虚拟环境的Python和pip路径
VENV_PYTHON="$VENV_DIR/bin/python"
VENV_PIP="$VENV_DIR/bin/pip"

# 检查是否已有进程在运行
if pgrep -f "python.*update_index.py" > /dev/null; then
    echo "更新服务已在运行。"
    exit 0
fi

# 在虚拟环境中安装依赖
echo "安装依赖..."
"$VENV_PIP" install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "错误: 安装依赖失败。"
    exit 1
fi

# 启动服务（在虚拟环境中）
echo "启动更新服务..."
nohup "$VENV_PYTHON" update_index.py > "$LOG_FILE" 2>&1 &

# 检查是否成功启动
sleep 2  # 等待进程启动
if pgrep -f "python.*update_index.py" > /dev/null; then
    echo "更新服务已成功启动！"
    echo "日志文件: $LOG_FILE"
    exit 0
else
    echo "错误: 启动更新服务失败。"
    echo "请查看日志文件了解详情: $LOG_FILE"
    exit 1
fi 