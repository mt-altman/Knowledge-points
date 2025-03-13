# 技术文档中心

这是一个使用GitHub Pages托管的技术文档中心，收集和整理了多个技术领域的文档和学习资料。

## 文档内容

本文档中心包含以下主题：

- **Redis**: Redis数据库的核心概念、用法、配置和最佳实践
- **数据结构**: 常见数据结构的原理、实现和应用场景分析
- **MySQL**: MySQL数据库的基础知识、优化技巧和进阶内容
- **CI/CD**: 持续集成和持续部署的流程、工具和实践指南

## 浏览文档

访问[技术文档中心](https://your-username.github.io/github-pages/)浏览所有文档。

## 本地运行

如果你想在本地查看和编辑这些文档：

1. 克隆仓库:
   ```bash
   git clone https://github.com/your-username/github-pages.git
   cd github-pages
   ```

2. 使用任意HTTP服务器在本地运行，例如：
   ```bash
   # 如果安装了Python 3
   python -m http.server
   
   # 或者使用Python 2
   python -m SimpleHTTPServer
   ```

3. 打开浏览器访问 `http://localhost:8000` 即可查看文档

## 自动更新索引

本项目包含一个自动更新索引的脚本，可以监控文档目录的变化并自动更新首页和导航页面。

### 使用方法

#### 简易启动（推荐）

使用提供的启动脚本，它会自动创建虚拟环境并安装所需依赖：

1. Linux/macOS:
   ```bash
   # 给启动脚本添加执行权限（仅首次需要）
   chmod +x start_update_service.sh
   # 启动服务
   ./start_update_service.sh
   ```

2. Windows:
   ```
   # 双击运行 start_update_service.bat
   # 或在命令提示符中运行
   start_update_service.bat
   ```

启动脚本会：
1. 检查Python是否已安装
2. 创建一个名为`.venv`的虚拟环境
3. 在虚拟环境中安装所需依赖
4. 在虚拟环境中运行更新脚本
5. 将日志输出到`update_log.txt`文件中

#### 手动安装和运行

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

详细说明请参阅 [README_UPDATE_SCRIPT.md](README_UPDATE_SCRIPT.md)。

## 贡献

欢迎贡献更多内容或改进现有文档！请遵循以下步骤：

1. Fork 这个仓库
2. 创建你的特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交你的更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启一个 Pull Request

## 许可证

本仓库内容采用 [MIT 许可证](LICENSE)。
