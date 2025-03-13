# 目录索引自动更新脚本

这个Python脚本用于监控`docs`目录的变化，并自动更新网站的索引页面（`index.html`和`docs/index.html`）。

## 功能特性

- 自动监控`docs`目录及其子目录的变化
- 当检测到变化时，自动更新主页和文档导航页面
- 智能提取每个主题的描述信息（从README.md或index.html文件中）
- 按字母顺序排列主题
- 美化主题名称显示（例如将"data-structure"转换为"Data Structure"）
- 防止频繁更新（设有冷却时间）

## 安装与使用

### 前提条件

- Python 3.6+

### 简易启动（推荐）

提供了便捷的启动脚本，会自动创建虚拟环境并安装依赖：

#### Linux/macOS

```bash
# 给启动脚本添加执行权限（仅需首次运行）
chmod +x start_update_service.sh

# 启动服务
./start_update_service.sh
```

#### Windows

```
# 双击运行 start_update_service.bat
# 或在命令提示符/PowerShell中运行
start_update_service.bat
```

### 手动安装和运行

如果你需要手动设置：

```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Linux/macOS
source .venv/bin/activate
# Windows
.venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 运行脚本
python update_index.py
```

## 工作原理

1. 脚本启动时会扫描`docs`目录，识别所有主题目录
2. 对于每个主题，尝试从README.md或index.html中提取描述信息
3. 生成新的index.html文件（主页和文档导航页）
4. 设置文件系统监控器，持续监视`docs`目录的变化
5. 当检测到变化时，重新生成索引页面

## 虚拟环境说明

由于许多现代Python安装（特别是macOS）使用"外部管理环境"保护，直接安装包会被拒绝。启动脚本会：

1. 自动创建一个名为`.venv`的虚拟环境
2. 在该环境中安装所需依赖
3. 使用虚拟环境中的Python运行脚本

虚拟环境的文件存储在项目根目录下的`.venv`文件夹中。如果需要删除虚拟环境，可以直接删除该文件夹。

## 自定义

如果需要自定义默认描述或特殊主题名称的显示，可以编辑脚本顶部的`DEFAULT_DESCRIPTIONS`字典：

```python
DEFAULT_DESCRIPTIONS = {
    "redis": "Redis 数据库的核心概念、用法、配置和最佳实践。",
    # 添加更多默认描述...
}
```

## 故障排除

- 如果启动脚本报错，可以尝试手动设置虚拟环境和运行脚本
- 如果脚本无法正确识别或提取主题描述，可以在相应主题目录中添加README.md文件，并在其中提供清晰的描述
- 如果主题名称显示不正确，可以修改脚本中的`get_pretty_name`函数，添加特殊处理规则
- 查看`update_log.txt`文件可以了解脚本的运行情况和可能的错误信息 